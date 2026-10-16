
#!/usr/bin/env python3
"""Renomeação cautelosa do pacote de um APK descompilado com Apktool."""

import pathlib
import re
import shutil
import sys

PACKAGE_RE = re.compile(
    r"[a-z][a-z0-9_]*(?:\.[a-z][a-z0-9_]*)+"
)

if len(sys.argv) != 3:
    raise SystemExit(
        "Uso: rename_package.py DIRETORIO NOVO_PACOTE"
    )

root = pathlib.Path(sys.argv[1]).resolve()
new_pkg = sys.argv[2].strip()

if not PACKAGE_RE.fullmatch(new_pkg):
    raise SystemExit(
        f"Pacote inválido: {new_pkg}. "
        "Exemplo: com.cliente.app"
    )

manifest = root / "AndroidManifest.xml"

if not manifest.is_file():
    raise SystemExit(
        f"Manifesto não encontrado: {manifest}"
    )

manifest_text = manifest.read_text(encoding="utf-8")

match = re.search(
    r'\bpackage="([^"]+)"',
    manifest_text
)

if not match:
    raise SystemExit(
        "Não foi possível identificar o pacote original."
    )

old_pkg = match.group(1)

if old_pkg == new_pkg:
    print(f"O pacote já é {new_pkg}. Nenhuma alteração.")
    sys.exit(0)

old_path = old_pkg.replace(".", "/")
new_path = new_pkg.replace(".", "/")

# Não sobrescrever uma pasta de classes que já exista.
for smali_dir in root.glob("smali*"):
    if not smali_dir.is_dir():
        continue

    old_folder = smali_dir / old_path
    new_folder = smali_dir / new_path

    if old_folder.is_dir() and new_folder.exists():
        raise SystemExit(
            "Conflito: a pasta de destino já existe: "
            f"{new_folder}. Nenhum arquivo foi alterado."
        )

# Criar backup antes de editar o manifesto.
backup = manifest.with_suffix(".xml.bak")

if backup.exists():
    raise SystemExit(
        f"Backup já existe: {backup}. "
        "Verifique os arquivos antes de continuar."
    )

shutil.copy2(manifest, backup)

try:
    # Atualizar o atributo package e referências explícitas
    # ao nome completo do pacote no manifesto.
    updated_manifest = manifest_text.replace(
        old_pkg, new_pkg
    )
    manifest.write_text(
        updated_manifest, encoding="utf-8"
    )

    # Atualizar referências de classes em Smali.
    for smali_dir in root.glob("smali*"):
        if not smali_dir.is_dir():
            continue

        for file in smali_dir.rglob("*.smali"):
            content = file.read_text(encoding="utf-8")
            updated = content.replace(old_path, new_path)

            if updated != content:
                file.write_text(updated, encoding="utf-8")

        old_folder = smali_dir / old_path
        new_folder = smali_dir / new_path

        if old_folder.is_dir():
            new_folder.parent.mkdir(
                parents=True, exist_ok=True
            )
            shutil.move(str(old_folder), str(new_folder))

    # Atualizar referências explícitas em XMLs de recursos.
    res = root / "res"

    if res.is_dir():
        for file in res.rglob("*.xml"):
            content = file.read_text(encoding="utf-8")
            updated = content.replace(old_pkg, new_pkg)

            if updated != content:
                file.write_text(updated, encoding="utf-8")

except Exception:
    # Restaurar o manifesto em caso de erro.
    shutil.copy2(backup, manifest)
    raise

print(f"Pacote no manifesto: {old_pkg} -> {new_pkg}")
print("Atenção: valide referências, recursos e inicialização.")
print(f"Backup do manifesto: {backup}")
