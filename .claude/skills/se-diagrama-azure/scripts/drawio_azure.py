#!/usr/bin/env python3
"""Genera diagramas draw.io de arquitectura Azure con iconos oficiales a partir de una especificación JSON.

Uso: uv run --group se drawio_azure.py <spec.json> [--salida proposal/diagramas/<nombre>.drawio] [--validar]
     uv run --group se drawio_azure.py --iconos

Adaptado de la skill drawio-azure-reference: iconos SVG oficiales incrustados como data URI
codificada en URL, icono y etiqueta como objetos separados, leyenda con muestras de color,
un color por flujo principal, flujo de plataforma gris discontinuo y saltos en los cruces.
La diferencia es que el diagrama se describe en datos (zonas, nodos, flujos, conexiones) y
el script calcula la disposición, en lugar de editar coordenadas en código.

--validar comprueba la especificación sin escribir el fichero. Exit 1 si hay errores.
Formato de la especificación: references/especificacion.md.
"""
from __future__ import annotations

import argparse
import json
import math
import re
import sys
from pathlib import Path
from urllib.parse import quote

SKILL = Path(__file__).resolve().parents[1]
ICONS = SKILL / "assets" / "icons"
ICON_FILES = {
    "app_service": "app-services.svg", "app_service_plan": "app-service-plans.svg", "function_app": "function-apps.svg",
    "storage": "storage-accounts.svg", "openai": "azure-openai.svg", "search": "cognitive-search.svg",
    "docintel": "form-recognizers.svg", "cosmos": "cosmos-db.svg", "sql_server": "sql-server.svg",
    "sql_database": "sql-database.svg", "key_vault": "key-vaults.svg", "private_endpoint": "private-endpoints.svg",
    "virtual_network": "virtual-networks.svg", "subnet": "subnet.svg", "dns_zone": "dns-zones.svg",
    "app_insights": "application-insights.svg", "log_analytics": "log-analytics-workspaces.svg",
}
PALETTE = ["#0078D4", "#D83B01", "#107C10", "#8E44AD", "#C19C00", "#008575", "#B4009E"]
PLATFORM = "#5F6A72"
ZONE_COLORS = {"naranja": ("#FFF4E5", "#E3A74A"), "azul": ("#EFF6FF", "#7DA2D6"), "verde": ("#F2FBF4", "#7DBE88"),
               "morado": ("#F7F2FF", "#A58AD6"), "amarillo": ("#FFF9E8", "#D9B85F"), "gris": ("#F4F4F4", "#A0A0A0"),
               "blanco": ("#FFFFFF", "#C8C8C8")}
COL_W, ROW_H, GAP, NODE_W, NODE_H, PAD_TOP, PAD_X = 460, 330, 40, 170, 150, 60, 25
LEGEND_W = 280


def icon_uri(key: str) -> str:
    return "data:image/svg+xml," + quote((ICONS / ICON_FILES[key]).read_text(encoding="utf-8"), safe="")


def validate(spec: dict) -> list[str]:
    errs = []
    zones = {z.get("id") for z in spec.get("zonas", [])}
    if not spec.get("zonas"):
        errs.append("faltan 'zonas'")
    for z in spec.get("zonas", []):
        for k in ("id", "titulo", "columna", "fila"):
            if k not in z:
                errs.append(f"zona {z.get('id', '?')}: falta '{k}'")
        if z.get("color", "blanco") not in ZONE_COLORS:
            errs.append(f"zona {z.get('id')}: color '{z.get('color')}' no válido ({', '.join(ZONE_COLORS)})")
    ids = [n.get("id") for n in spec.get("nodos", [])] + [n.get("id") for n in spec.get("notas", [])]
    for d in {i for i in ids if ids.count(i) > 1}:
        errs.append(f"id duplicado: {d}")
    for n in spec.get("nodos", []):
        if n.get("zona") not in zones:
            errs.append(f"nodo {n.get('id')}: zona '{n.get('zona')}' no existe")
        if n.get("icono") and n["icono"] not in ICON_FILES:
            errs.append(f"nodo {n.get('id')}: icono '{n['icono']}' no disponible (usa --iconos o añade el SVG)")
    for n in spec.get("notas", []):
        if n.get("zona") not in zones:
            errs.append(f"nota {n.get('id')}: zona '{n.get('zona')}' no existe")
    flows = {f.get("id") for f in spec.get("flujos", [])} | {"plataforma"}
    if len(spec.get("flujos", [])) > len(PALETTE):
        errs.append(f"más de {len(PALETTE)} flujos principales: agrupa o simplifica")
    for c in spec.get("conexiones", []):
        for end in ("de", "a"):
            if c.get(end) not in ids:
                errs.append(f"conexión {c.get('de')}→{c.get('a')}: '{c.get(end)}' no existe")
        if c.get("flujo", "plataforma") not in flows:
            errs.append(f"conexión {c.get('de')}→{c.get('a')}: flujo '{c.get('flujo')}' no declarado")
    return errs


def build(spec: dict, out: Path) -> Path:
    import logging
    logging.disable(logging.INFO)  # drawpyo informa de cada paso
    import drawpyo
    f = drawpyo.File()
    f.file_path, f.file_name = str(out.parent), out.name
    page = drawpyo.Page(file=f)
    page.name = spec.get("pagina", spec.get("titulo", "Arquitectura"))

    def box(text, x, y, w, h, style):
        o = drawpyo.diagram.Object(page=page, value=text)
        o.position, o.width, o.height = (x, y), w, h
        o.apply_style_string(style)
        return o

    x0 = LEGEND_W + 2 * GAP
    zone_geo = {}
    for z in spec["zonas"]:
        x = x0 + z["columna"] * (COL_W + GAP)
        y = GAP + z["fila"] * (ROW_H + GAP)
        w = z.get("ancho", 1) * COL_W + (z.get("ancho", 1) - 1) * GAP
        members = [n for n in spec.get("nodos", []) + spec.get("notas", []) if n.get("zona") == z["id"]]
        per_row = max(1, int((w - 2 * PAD_X) // NODE_W))
        rows_needed = math.ceil(len(members) / per_row) if members else 1
        h = max(z.get("alto", 1) * ROW_H + (z.get("alto", 1) - 1) * GAP, PAD_TOP + rows_needed * NODE_H + 20)
        fill, stroke = ZONE_COLORS[z.get("color", "blanco")]
        box(z["titulo"], x, y, w, h, "rounded=1;whiteSpace=wrap;html=1;align=left;verticalAlign=top;spacingTop=12;"
            f"spacingLeft=12;fontStyle=1;fontSize=16;fillColor={fill};strokeColor={stroke};strokeWidth=2;")
        zone_geo[z["id"]] = (x, y, w, per_row)
    anchors, slot = {}, {k: 0 for k in zone_geo}
    for n in spec.get("nodos", []) + spec.get("notas", []):
        zx, zy, zw, per_row = zone_geo[n["zona"]]
        i = slot[n["zona"]]
        slot[n["zona"]] += 1
        x = zx + PAD_X + (i % per_row) * NODE_W
        y = zy + PAD_TOP + (i // per_row) * NODE_H
        if "texto" in n:  # nota
            anchors[n["id"]] = box(n["texto"].replace("\n", "<br>"), x, y, NODE_W - 10, NODE_H - 30,
                                   "whiteSpace=wrap;html=1;align=left;verticalAlign=middle;spacingLeft=8;fontSize=10;"
                                   "rounded=1;dashed=1;fillColor=#FFFFFF;strokeColor=#9AA4AE;")
        elif n.get("icono"):
            anchor = box("", x, y, NODE_W - 20, 72, "rounded=0;strokeColor=none;fillColor=none;opacity=0;")
            box("", x + (NODE_W - 20 - 72) / 2, y, 72, 72,
                f"shape=image;html=1;aspect=fixed;imageAspect=0;image={icon_uri(n['icono'])};")
            box(n["etiqueta"].replace("\n", "<br>"), x, y + 80, NODE_W - 20, 44,
                "rounded=0;strokeColor=none;fillColor=none;html=1;align=center;verticalAlign=top;fontSize=11;whiteSpace=wrap;")
            anchors[n["id"]] = anchor
        else:
            anchors[n["id"]] = box(n["etiqueta"].replace("\n", "<br>"), x, y + 14, NODE_W - 20, 48,
                                   "rounded=1;whiteSpace=wrap;html=1;fontSize=11;fillColor=#FDE9D9;strokeColor=#C27C0E;")
    colors = {fl["id"]: fl.get("color") or PALETTE[i] for i, fl in enumerate(spec.get("flujos", []))}
    colors["plataforma"] = PLATFORM
    legend = [(fl["etiqueta"], colors[fl["id"]], False) for fl in spec.get("flujos", [])]
    legend.append(("Plataforma / conectividad privada", PLATFORM, True))
    lx, ly = GAP, GAP
    box("Leyenda", lx, ly, LEGEND_W, 60 + 45 * len(legend), "rounded=1;whiteSpace=wrap;html=1;align=left;"
        "verticalAlign=top;spacingTop=12;spacingLeft=12;fontStyle=1;fontSize=16;fillColor=#FFFFFF;strokeColor=#C8C8C8;")
    for i, (label, color, dashed) in enumerate(legend):
        yy = ly + 55 + i * 45
        box("", lx + 20, yy + 9, 68, 6, f"rounded=1;html=1;dashed={int(dashed)};fillColor={color};strokeColor={color};strokeWidth=3;")
        box(label, lx + 100, yy, LEGEND_W - 110, 24, "rounded=0;strokeColor=none;fillColor=none;html=1;align=left;verticalAlign=middle;fontSize=11;")
    for c in spec.get("conexiones", []):
        flow = c.get("flujo", "plataforma")
        dashed = c.get("discontinua", flow == "plataforma")
        width = 2 if flow == "plataforma" else 3
        color = colors[flow]
        e = drawpyo.diagram.Edge(page=page, source=anchors[c["de"]], target=anchors[c["a"]], label=c.get("etiqueta", ""))
        e.apply_style_string("edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;jumpStyle=arc;"
                             f"jumpSize=10;strokeColor={color};strokeWidth={width};fontSize=10;fontColor={color};html=1;"
                             f"dashed={int(dashed)};endArrow=block;startArrow=none;")
    out.parent.mkdir(parents=True, exist_ok=True)
    f.write()
    return out


def check_output(path: Path, spec: dict) -> list[str]:
    xml = path.read_text(encoding="utf-8")
    errs = []
    n_icons = sum(1 for n in spec.get("nodos", []) if n.get("icono"))
    if xml.count("shape=image") < n_icons:
        errs.append("faltan iconos en el XML generado")
    for fl in spec.get("flujos", []):
        if fl["etiqueta"] not in xml:
            errs.append(f"la leyenda no contiene '{fl['etiqueta']}'")
    return errs


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("spec", nargs="?")
    ap.add_argument("--salida")
    ap.add_argument("--validar", action="store_true")
    ap.add_argument("--iconos", action="store_true")
    a = ap.parse_args()
    if a.iconos:
        for k, v in ICON_FILES.items():
            print(f"{k:<18} {v}")
        return 0
    if not a.spec:
        ap.error("indica la especificación JSON")
    spec = json.loads(Path(a.spec).read_text(encoding="utf-8"))
    errs = validate(spec)
    if errs:
        print("KO especificación:")
        for e in errs:
            print(f"  - {e}")
        return 1
    if a.validar:
        print("OK especificación")
        return 0
    name = re.sub(r"[^\w.-]+", "-", spec.get("nombre") or Path(a.spec).stem).strip("-").lower()
    out = Path(a.salida or f"proposal/diagramas/{name}.drawio")
    try:
        build(spec, out)
    except ModuleNotFoundError:
        print("KO: falta drawpyo en el entorno (ejecuta /se-init)")
        return 1
    errs = check_output(out, spec)
    if errs:
        print("KO salida:")
        for e in errs:
            print(f"  - {e}")
        return 1
    print(f"OK {out} · {len(spec.get('nodos', []))} nodos · {len(spec.get('conexiones', []))} conexiones")
    return 0


if __name__ == "__main__":
    sys.exit(main())
