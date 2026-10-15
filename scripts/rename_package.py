#!/usr/bin/env python3
"""
Renomeia o pacote de um APK descompilado pelo apktool.
Ajusta AndroidManifest.xml, pastas smali, arquivos smali, res/xml e assets.
"""
import pathlib
import re
import shutil
import sys

if len(sys.argv) != 3:
    raise SystemExit("Uso: rename_package.py DIRETORIO NOVO_PACOTE")

root = pathlib.Path(sys.argv[1]).resolve()
new_pkg = sys.argv[2].strip()

if not re.fullmatch(r"[a-z][a-z0-9_]*(\.[a-z][a-z0-9_]*)+", new_pkg):
    raise SystemExit(f"Pacote inválido: {new_pkg}. Use formato tipo com.cliente.app")

manifest = root / "AndroidManifest.xml"
if not manifest.is_file():
    raise SystemExit("AndroidManifest.xml não encontrado")

# Descobre o pacote antigo lendo o manifest
manifest_text = manifest.read_text(encoding="utf-8")
m = re.search(r'package="([^"]+)"', manifest_text)
if not m:
    raise SystemExit("Não achei o atributo package no manifest")
old_pkg = m.group(1)

if old_pkg == new_pkg:
    print(f"Pacote já é {new_pkg}, nada a fazer.")
    sys.exit(0)

print(f"Renomeando: {old_pkg} -> {new_pkg}")

old_path = old_pkg.replace(".", "/")
new_path = new_pkg.replace(".", "/")

# 1) Manifest: troca TODAS as ocorrências do pacote antigo
new_manifest = manifest_text.replace(old_pkg, new_pkg)
manifest.write_text(new_manifest, encoding="utf-8")
print("  OK AndroidManifest.xml atualizado")

# 2) Smali: renomeia pastas e atualiza conteúdo
for smali_dir in root.glob("smali*"):
    if not smali_dir.is_dir():
        continue

    old_folder = smali_dir / old_path
    new_folder = smali_dir / new_path

    # Atualiza TODOS os arquivos .smali trocando o pacote antigo
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
    print(f"  OK {smali_dir.name}: {count_files} arquivos .smali atualizados")

    # Move a pasta do pacote antigo pra nova
    if old_folder.is_dir():
        new_folder.parent.mkdir(parents=True, exist_ok=True)
        if new_folder.exists():
            shutil.rmtree(new_folder)
        shutil.move(str(old_folder), str(new_folder))
        print(f"  OK Pasta movida: {old_folder} -> {new_folder}")

# 3) res/xml e outros XMLs que possam referenciar o pacote
for xml_file in list(root.glob("res/**/*.xml")):
    try:
        content = xml_file.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        continue
    new_content = content.replace(old_pkg, new_pkg)
    if new_content != content:
        xml_file.write_text(new_content, encoding="utf-8")

print(f"Renomeacao concluida: {old_pkg} -> {new_pkg}")
