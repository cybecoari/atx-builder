#!/usr/bin/env python3
"""Personaliza um APK descompilado (nome + credencial opcional)."""
import pathlib
import re
import sys

if len(sys.argv) != 4:
    raise SystemExit("Uso: customize_simples.py DIRETORIO NOME_APP CREDENCIAL")

root = pathlib.Path(sys.argv[1]).resolve()
app_name = sys.argv[2]
credential = sys.argv[3]

manifest = root / "AndroidManifest.xml"
credential_file = root / "assets" / "config" / "credential.txt"

# --- Validações de entrada ---
if not app_name.strip():
    raise SystemExit("Nome do app vazio")
if "\n" in app_name or "\r" in app_name:
    raise SystemExit("Nome do app contém quebra de linha")
if credential and ("\n" in credential or "\r" in credential or "\x00" in credential):
    raise SystemExit("Credencial contém caracteres inválidos")
if credential and len(credential) > 200:
    raise SystemExit("Credencial longa demais")
if credential and not re.fullmatch(r"[A-Za-z0-9_\-\.=]*", credential):
    raise SystemExit("Credencial contém caracteres não permitidos")

# --- Validação do manifest ---
if not manifest.is_file():
    raise SystemExit("AndroidManifest.xml não encontrado")

# --- Escape XML ---
def xml_escape(s: str) -> str:
    return (s.replace("&", "&amp;")
             .replace("<", "&lt;")
             .replace(">", "&gt;")
             .replace('"', "&quot;"))

escaped = xml_escape(app_name)
manifest_text = manifest.read_text(encoding="utf-8")

# Troca todos os android:label="..." que NÃO começam com @string/
pattern = re.compile(r'(android:label=")((?!@string/)[^"]*)(")')
new_text, count = pattern.subn(rf'\g<1>{escaped}\g<3>', manifest_text)

if count == 0:
    raise SystemExit("Nenhum android:label para substituir foi encontrado")

manifest.write_text(new_text, encoding="utf-8")
print(f"OK: {count} labels substituídos por '{app_name}'")

# --- Credencial (opcional) ---
if credential_file.is_file():
    credential_file.write_text(credential, encoding="utf-8")
    print(f"OK: credencial escrita em {credential_file}")
else:
    print(f"AVISO: {credential_file} não existe. App usa login manual. Pulando.")