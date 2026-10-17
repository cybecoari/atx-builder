#!/usr/bin/env python3
"""Renomeia o pacote de um APK descompilado pelo apktool."""
import pathlib
import re
import shutil
import sys

if len(sys.argv) != 3:
    raise SystemExit("Uso: rename_package.py DIRETORIO NOVO_PACOTE")

root = pathlib.Path(sys.argv[1]).resolve()
new_pkg = sys.argv[2].strip()

if not re.fullmatch(r"[a-z][a-z0-9_]*(\.[a-z][a-z0-9_]*)+", new_pkg):
    raise SystemExit(f"Pacote inválido: {new_pkg}")

manifest = root / "AndroidManifest.xml"
if not manifest.is_file():
    raise SystemExit("AndroidManifest.xml não encontrado")

manifest_text = manifest.read_text(encoding="utf-8")
m = re.search(r'package="([^"]+)"', manifest_text)
if not m:
    raise SystemExit("Não achei o atributo package no manifest")
old_pkg = m.group(1)

if old_pkg == new_pkg:
    print(f"Pacote já é {new_pkg}. Nada a fazer.")
    sys.exit(0)

print(f"Renomeando: {old_pkg} -> {new_pkg}")
old_path = old_pkg.replace(".", "/")
new_path = new_pkg.replace(".", "/")

# 1) Manifest
new_manifest = manifest_text.replace(old_pkg, new_pkg)
manifest.write_text(new_manifest, encoding="utf-8")
print("  OK AndroidManifest.xml")

# 2) Smali
for smali_dir in root.glob("smali*"):
    if not smali_dir.is_dir():
        continue
    old_folder = smali_dir / old_path
    new_folder = smali_dir / new_path
    count_files = 0
    for smali_file in smali_dir.rglob("*.smali"):
        try:
            content = smali_file.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        new_content = content.replace(old_path, new_path)
        if new_content != content:
            smali_file.write_text(new_content, encoding="utf-8")
            count_files += 1
    if old_folder.is_dir():
        new_folder.parent.mkdir(parents=True, exist_ok=True)
        if new_folder.exists():
            shutil.rmtree(new_folder)
        shutil.move(str(old_folder), str(new_folder))
        print(f"  OK {smali_dir.name}: {count_files} arquivos + pasta movida")

# 3) res XML
for xml_file in root.glob("res/**/*.xml"):
    try:
        content = xml_file.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        continue
    new_content = content.replace(old_pkg, new_pkg)
    if new_content != content:
        xml_file.write_text(new_content, encoding="utf-8")

print(f"Concluído: {old_pkg} -> {new_pkg}")