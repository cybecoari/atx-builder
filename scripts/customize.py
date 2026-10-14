#!/usr/bin/env python3
"""Personaliza um APK ATX descompilado."""
import pathlib
import re
import sys

if len(sys.argv) != 4:
    raise SystemExit("Uso: customize.py DIRETORIO NOME_APP CREDENCIAL")

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
if "\n" in credential or "\r" in credential or "\x00" in credential:
    raise SystemExit("Credencial contém caracteres inválidos")
if not (1 <= len(credential) <= 200):
    raise SystemExit("Credencial vazia ou longa demais")
if not re.fullmatch(r"[A-Za-z0-9_\-\.=]+", credential):
    raise SystemExit("Credencial contém caracteres não permitidos")

# --- Validações do projeto ---
if not manifest.is_file():
    raise SystemExit("AndroidManifest.xml não encontrado")
if not credential_file.is_file():
    raise SystemExit(f"credential.txt não existe em {credential_file}")

# --- Escape XML ---
def xml_escape(s: str) -> str:
    return (s.replace("&", "&amp;")
             .replace("<", "&lt;")
             .replace(">", "&gt;")
             .replace('"', "&quot;"))

escaped = xml_escape(app_name)
manifest_text = manifest.read_text(encoding="utf-8")

# Troca TODOS os android:label="atx_3.0" (ou qualquer valor atual do app)
# Só troca quando o valor NÃO começa com @string/ (pra preservar traduções)
pattern = re.compile(r'(android:label=")((?!@string/)[^"]*)(")')
new_text, count = pattern.subn(rf'\g<1>{escaped}\g<3>', manifest_text)

if count == 0:
    raise SystemExit("Nenhum android:label para substituir foi encontrado")

manifest.write_text(new_text, encoding="utf-8")
credential_file.write_text(credential, encoding="utf-8")

print(f"OK: {count} labels substituídos por '{app_name}'")
print(f"OK: credencial escrita em {credential_file}")
