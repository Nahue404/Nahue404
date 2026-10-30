"""Arma assets/lenguajes.svg con los lenguajes de todos mis repos, privados incluidos.

La tarjeta de github-profile-summary-cards solo ve los repos publicos, y casi todo lo que
hago esta en privados. Esto suma los bytes de cada lenguaje que reporta GitHub en cada repo
propio (sin forks) y deja afuera lo que no es codigo que escribi yo:

- HTML y CSS: las plantillas inflan los numeros (un solo repo tiene 2,7 MB de HTML).
- El codigo nativo que Flutter genera para Windows, iOS y Android (C++, CMake, Swift...).
- Archivos de configuracion o scripts sueltos (Procfile, PowerShell).

Uso: GITHUB_TOKEN=<token con acceso a los repos privados> python scripts/lenguajes.py
"""
import json
import os
import urllib.request
from pathlib import Path

USUARIO = "Nahue404"
FUERA = {"HTML", "CSS", "SCSS", "CMake", "Procfile", "PowerShell", "Batchfile", "Shell", "Dockerfile"}
# Flutter genera carpetas windows/, ios/, android/ y linux/ con estos lenguajes
NATIVO_FLUTTER = {"C++", "C", "Swift", "Kotlin", "Objective-C"}
# Linguist confunde algunos .php con Hack, y las funciones de Supabase salen como PLpgSQL
ALIAS = {"Hack": "PHP", "PLpgSQL": "SQL", "TSQL": "SQL"}
COLORES = {
    "Dart": "#29d3ff",
    "Python": "#3fb950",
    "PHP": "#8b93ff",
    "SQL": "#ff9f43",
    "TypeScript": "#3b82f6",
    "JavaScript": "#f7df1e",
    "Java": "#ff6b6b",
    "C#": "#c58cff",
    "C": "#a0a0a0",
}
OTRO = "#555c6b"


def pedir(url, token):
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.loads(r.read())


def contar(token):
    repos = pedir("https://api.github.com/user/repos?per_page=100&affiliation=owner", token)
    total = {}
    for repo in repos:
        if repo["fork"]:
            continue
        langs = pedir(repo["languages_url"], token)
        es_flutter = "Dart" in langs
        for lang, bytes_ in langs.items():
            if lang in FUERA or (es_flutter and lang in NATIVO_FLUTTER):
                continue
            lang = ALIAS.get(lang, lang)
            total[lang] = total.get(lang, 0) + bytes_
    return total


def svg(total):
    suma = sum(total.values())
    orden = sorted(total.items(), key=lambda t: -t[1])
    grandes = [(l, b) for l, b in orden if b / suma >= 0.01]
    resto = suma - sum(b for _, b in grandes)
    if resto:
        grandes.append(("Otros", resto))

    ancho, x0, barra = 860, 24, 812
    filas = (len(grandes) + 1) // 2
    alto = 96 + filas * 26
    partes = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {ancho} {alto}" width="{ancho}" height="{alto}">',
        f'  <rect width="{ancho}" height="{alto}" rx="10" fill="#03060d" stroke="#1d2433"/>',
        '  <text x="24" y="36" font-family="Consolas, Menlo, monospace" font-size="15" fill="#d4d4d4">'
        '<tspan fill="#39ff14">nahuel@dev</tspan>:<tspan fill="#29d3ff">~</tspan>$ cat languages.txt</text>',
        f'  <clipPath id="b"><rect x="{x0}" y="52" width="{barra}" height="12" rx="6"/></clipPath>',
        '  <g clip-path="url(#b)">',
    ]
    x = x0
    for lang, b in grandes:
        w = barra * b / suma
        partes.append(f'    <rect x="{x:.1f}" y="52" width="{w + 0.5:.1f}" height="12" fill="{COLORES.get(lang, OTRO)}"/>')
        x += w
    partes.append("  </g>")
    for i, (lang, b) in enumerate(grandes):
        col, fila = divmod(i, filas)
        cx, cy = x0 + col * 420, 98 + fila * 26
        partes.append(f'  <circle cx="{cx + 6}" cy="{cy - 5}" r="5" fill="{COLORES.get(lang, OTRO)}"/>')
        partes.append(
            f'  <text x="{cx + 20}" y="{cy}" font-family="Consolas, Menlo, monospace" font-size="14" fill="#d4d4d4">'
            f'{lang}<tspan fill="#7d8590"> {100 * b / suma:.1f}%</tspan></text>'
        )
    partes.append("</svg>")
    return "\n".join(partes) + "\n"


if __name__ == "__main__":
    total = contar(os.environ["GITHUB_TOKEN"])
    destino = Path(__file__).resolve().parent.parent / "assets" / "lenguajes.svg"
    destino.write_text(svg(total), encoding="utf-8")
    for lang, b in sorted(total.items(), key=lambda t: -t[1]):
        print(f"{lang:12} {b:>9}")
