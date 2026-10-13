#!/usr/bin/env python3
"""Perfila muestras de datos y genera un perfil .md y .json por fichero.

Uso:
  uv run --group se profile_dataset.py [raíz] [--max-rows N] [--file ruta]

Lee data-samples/ (csv, tsv, txt delimitado, parquet, xlsx/xls, json, jsonl).
Salida: proposal/_meta/data-profiles/<fichero>.md|.json
Requiere pandas; pyarrow para parquet; openpyxl para xlsx.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import warnings
from pathlib import Path

try:
    import pandas as pd
except ImportError:
    print("ERROR: falta pandas en el entorno: ejecuta /se-init o `uv add --group se pandas pyarrow openpyxl`")
    sys.exit(2)

warnings.filterwarnings("ignore", category=UserWarning)

PII = {
    "email": re.compile(r"^[\w.+-]+@[\w-]+\.[\w.-]+$"),
    "telefono": re.compile(r"^\+?\d[\d\s-]{7,14}\d$"),
    "dni_nie": re.compile(r"^[XYZ]?\d{7,8}[A-Z]$", re.I),
    "iban": re.compile(r"^[A-Z]{2}\d{2}[A-Z0-9]{10,30}$"),
    "ip": re.compile(r"^\d{1,3}(\.\d{1,3}){3}$"),
}
PII_NAMES = re.compile(r"nombre|name|apellido|surname|email|correo|tel[eé]f|phone|movil|m[oó]vil|dni|nif|nie\b|passport|pasaporte|iban|direcc|address|postal|nacim|birth|genero|gender|sexo|salud|health|ip_?addr", re.I)
SUPPORTED = {".csv", ".tsv", ".txt", ".parquet", ".xlsx", ".xls", ".json", ".jsonl"}


def read(path: Path, max_rows: int) -> dict:
    ext = path.suffix.lower()
    if ext in {".csv", ".tsv", ".txt"}:
        sep = "\t" if ext == ".tsv" else None
        for enc in ("utf-8", "latin-1"):
            try:
                return {"": pd.read_csv(path, sep=sep, engine="python", nrows=max_rows, encoding=enc)}
            except UnicodeDecodeError:
                continue
    if ext == ".parquet":
        return {"": pd.read_parquet(path).head(max_rows)}
    if ext in {".xlsx", ".xls"}:
        sheets = pd.read_excel(path, sheet_name=None, nrows=max_rows)
        return {f"#{k}": v for k, v in sheets.items()}
    if ext == ".jsonl":
        return {"": pd.read_json(path, lines=True, nrows=max_rows)}
    if ext == ".json":
        data = json.loads(path.read_text(encoding="utf-8"))
        if isinstance(data, dict):
            data = next((v for v in data.values() if isinstance(v, list)), [data])
        return {"": pd.json_normalize(data).head(max_rows)}
    raise ValueError(f"formato no soportado: {ext}")


def mask(v: object) -> str:
    s = str(v)
    return "*" * len(s) if len(s) <= 4 else s[:2] + "*" * (len(s) - 4) + s[-2:]


def looks_like_date(s: "pd.Series") -> "pd.Series | None":
    sample = s.head(500)
    if not sample.str.contains(r"\d{1,4}[-/.]\d{1,2}[-/.]\d{1,4}", regex=True).mean() > 0.9:
        return None
    parsed = pd.to_datetime(s, errors="coerce", dayfirst=False, format="mixed")
    return parsed if parsed.notna().mean() > 0.9 else None


def profile(df: "pd.DataFrame") -> dict:
    n = len(df)
    cols = []
    for c in df.columns:
        s = df[c]
        nn = s.dropna()
        info = {"columna": str(c), "tipo": str(s.dtype), "nulos_pct": round(100 * (1 - len(nn) / n), 2) if n else 0.0,
                "distintos": int(nn.nunique()), "unico": bool(n and nn.nunique() == n)}
        if pd.api.types.is_numeric_dtype(s) and not pd.api.types.is_bool_dtype(s) and len(nn):
            info.update(min=float(nn.min()), max=float(nn.max()), media=round(float(nn.mean()), 4))
        elif pd.api.types.is_datetime64_any_dtype(s) and len(nn):
            info.update(tipo_inferido="fecha", min=str(nn.min()), max=str(nn.max()))
        elif len(nn):
            as_str = nn.astype(str)
            dates = looks_like_date(as_str)
            if dates is not None:
                info.update(tipo_inferido="fecha", min=str(dates.min()), max=str(dates.max()))
            else:
                sample = as_str.head(1000)
                hits = [k for k, rx in PII.items() if sample.str.match(rx).mean() > 0.6]
                if hits:
                    info["pii_por_valor"] = hits
        if PII_NAMES.search(str(c)):
            info["pii_por_nombre"] = True
        top = nn.astype(str).value_counts().head(5)
        is_pii = info.get("pii_por_valor") or info.get("pii_por_nombre")
        info["frecuentes"] = [{"valor": mask(k) if is_pii else k[:60], "n": int(v)} for k, v in top.items()]
        cols.append(info)
    dup = int(df.duplicated().sum()) if n else 0
    keys = [c["columna"] for c in cols if c["unico"] and c["nulos_pct"] == 0
            and c.get("tipo_inferido") != "fecha" and not c["tipo"].startswith("float")]
    return {"filas": n, "columnas": len(df.columns), "filas_duplicadas": dup, "claves_candidatas": keys, "detalle": cols}


def to_md(name: str, p: dict, truncated: bool) -> str:
    out = [f"# Perfil · `{name}`", "",
           f"- Filas analizadas: {p['filas']}{' (truncado por --max-rows)' if truncated else ''}",
           f"- Columnas: {p['columnas']}", f"- Filas duplicadas: {p['filas_duplicadas']}",
           f"- Claves candidatas: {', '.join(f'`{k}`' for k in p['claves_candidatas']) or 'ninguna'}", "",
           "| Columna | Tipo | Nulos % | Distintos | Rango | PII | Valores frecuentes |",
           "| --- | --- | ---: | ---: | --- | --- | --- |"]
    for c in p["detalle"]:
        rng = f"{c.get('min', '')} → {c.get('max', '')}" if "min" in c else ""
        pii = ", ".join(c.get("pii_por_valor", [])) or ("por nombre" if c.get("pii_por_nombre") else "")
        freq = "; ".join(f"{f['valor']} ({f['n']})" for f in c["frecuentes"][:3]).replace("|", "/")
        out.append(f"| `{c['columna']}` | {c.get('tipo_inferido', c['tipo'])} | {c['nulos_pct']} | {c['distintos']} | {rng} | {pii} | {freq} |")
    return "\n".join(out) + "\n"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("root", nargs="?", default=".", help="raíz del workspace (por defecto, el directorio actual)")
    ap.add_argument("--max-rows", type=int, default=200_000)
    ap.add_argument("--file")
    a = ap.parse_args()
    root = Path(a.root).resolve()
    files = [Path(a.file).resolve()] if a.file else sorted(
        p for p in (root / "data-samples").rglob("*") if p.suffix.lower() in SUPPORTED)
    if not files:
        print("No hay muestras soportadas en data-samples/")
        return 1
    out_dir = root / "proposal/_meta/data-profiles"
    out_dir.mkdir(parents=True, exist_ok=True)
    rc = 0
    for f in files:
        try:
            rel = f.relative_to(root).as_posix()
        except ValueError:
            rel = f.name
        try:
            for suffix, df in read(f, a.max_rows).items():
                name = rel + suffix
                p = profile(df)
                stem = name.replace("/", "__").replace("#", "__")
                (out_dir / f"{stem}.json").write_text(json.dumps(p, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
                (out_dir / f"{stem}.md").write_text(to_md(name, p, len(df) >= a.max_rows), encoding="utf-8")
                pii = [c["columna"] for c in p["detalle"] if c.get("pii_por_valor") or c.get("pii_por_nombre")]
                print(f"OK {name}: {p['filas']}x{p['columnas']} · claves {p['claves_candidatas'] or '-'} · PII {pii or '-'}")
        except Exception as exc:  # noqa: BLE001
            print(f"KO {rel}: {exc}")
            rc = 1
    print(f"perfiles en {out_dir}")
    return rc


if __name__ == "__main__":
    sys.exit(main())
