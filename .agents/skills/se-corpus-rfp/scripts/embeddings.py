"""Embeddings para la similitud de requisitos, con caché en disco.

Backend configurable en se.config.json → requirements.dedupe.backend:
  "lexico"  sin embeddings (por defecto, sin dependencias)
  "azure"   Azure OpenAI (paquete `openai`, que añade `init_workspace.py --embeddings`; autenticación por clave en la variable indicada
            en `api_key_env` o, si no existe, Entra ID con `azure-identity`)

La caché vive en proposal/_meta/req-scan/embeddings.jsonl, indexada por modelo + texto, de
modo que solo se calculan los textos nuevos y los grupos son reproducibles. Si el backend
falla, `get_embedder` devuelve None y el llamador continúa en modo léxico con un aviso.
"""
from __future__ import annotations

import hashlib
import json
import math
import os
from pathlib import Path


class Embedder:
    """Interfaz: name (modelo) y embed(textos) -> vectores normalizados."""
    name = "base"

    def _call(self, texts: list[str]) -> list[list[float]]:
        raise NotImplementedError

    def __init__(self, cache_file: Path, batch: int = 256):
        self.cache_file, self.batch = cache_file, batch
        self.cache: dict[str, list[float]] = {}
        self.calls = 0
        if cache_file.exists():
            for line in cache_file.read_text(encoding="utf-8").splitlines():
                if line.strip():
                    row = json.loads(line)
                    self.cache[row["k"]] = row["v"]

    def key(self, text: str) -> str:
        return hashlib.sha1(f"{self.name}\n{text}".encode()).hexdigest()

    def embed(self, texts: list[str]) -> list[list[float]]:
        todo = sorted({t for t in texts if self.key(t) not in self.cache})
        if todo:
            self.cache_file.parent.mkdir(parents=True, exist_ok=True)
            with self.cache_file.open("a", encoding="utf-8") as fh:
                for i in range(0, len(todo), self.batch):
                    chunk = todo[i:i + self.batch]
                    vecs = self._call(chunk)
                    self.calls += 1
                    for t, v in zip(chunk, vecs):
                        n = math.sqrt(sum(x * x for x in v)) or 1.0
                        v = [round(x / n, 6) for x in v]
                        self.cache[self.key(t)] = v
                        fh.write(json.dumps({"k": self.key(t), "m": self.name, "v": v}) + "\n")
        return [self.cache[self.key(t)] for t in texts]


class AzureEmbedder(Embedder):
    def __init__(self, cfg: dict, cache_file: Path):
        from openai import AzureOpenAI  # import diferido: solo si se usa
        endpoint = os.environ.get(cfg.get("endpoint_env", "AZURE_OPENAI_ENDPOINT"))
        if not endpoint:
            raise RuntimeError(f"falta la variable {cfg.get('endpoint_env')}")
        key = os.environ.get(cfg.get("api_key_env", "AZURE_OPENAI_API_KEY"))
        kwargs = {"azure_endpoint": endpoint, "api_version": cfg.get("api_version", "2024-10-21")}
        if key:
            kwargs["api_key"] = key
        else:
            from azure.identity import DefaultAzureCredential, get_bearer_token_provider
            kwargs["azure_ad_token_provider"] = get_bearer_token_provider(
                DefaultAzureCredential(), "https://cognitiveservices.azure.com/.default")
        self.client = AzureOpenAI(**kwargs)
        self.deployment = cfg["deployment"]
        self.name = f"azure:{self.deployment}"
        super().__init__(cache_file, cfg.get("batch", 256))

    def _call(self, texts: list[str]) -> list[list[float]]:
        out = self.client.embeddings.create(model=self.deployment, input=texts)
        return [d.embedding for d in sorted(out.data, key=lambda d: d.index)]


def cache_path(opp: Path) -> Path:
    return opp / "proposal/_meta/req-scan/embeddings.jsonl"


def get_embedder(opp: Path, dcfg: dict) -> tuple[Embedder | None, str]:
    """Devuelve (embedder o None, mensaje). None significa modo léxico."""
    backend = dcfg.get("backend", "lexico")
    if backend == "lexico":
        return None, "lexico"
    try:
        if backend == "azure":
            return AzureEmbedder(dcfg.get("azure", {}), cache_path(opp)), f"azure ({dcfg['azure']['deployment']})"
        return None, f"AVISO: backend '{backend}' desconocido; se usa el modo léxico"
    except Exception as exc:  # noqa: BLE001 - cualquier fallo degrada a léxico
        return None, f"AVISO: no se pudo iniciar el backend '{backend}' ({exc}); se usa el modo léxico"


def dot(a: list[float], b: list[float]) -> float:
    return sum(x * y for x, y in zip(a, b))
