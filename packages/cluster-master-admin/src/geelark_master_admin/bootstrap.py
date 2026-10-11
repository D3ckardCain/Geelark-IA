"""Inicializa el hash de contraseña del operador sin imprimir secretos."""
from __future__ import annotations

import argparse
import json
import os
from getpass import getpass
from pathlib import Path

from .auth import _restrict_windows_acl, hash_operator_password


def main() -> int:
    parser = argparse.ArgumentParser(description="Inicializar credencial local del operador PC-MASTER")
    parser.add_argument("--output", required=True, help="Ruta privada fuera del repositorio")
    args = parser.parse_args()
    target = Path(args.output).expanduser().resolve()
    if target.exists():
        parser.error("El archivo ya existe; no se sobrescribirá.")
    first = getpass("Nueva contraseña de operador (mínimo 12 caracteres): ")
    second = getpass("Repita la contraseña: ")
    if first != second:
        parser.error("Las contraseñas no coinciden.")
    try:
        password_hash = hash_operator_password(first)
    except ValueError as exc:
        parser.error(str(exc))
    target.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
    if os.name == "posix" and target.parent.stat().st_mode & 0o077:
        parser.error("El directorio de destino debe ser privado (0700); corrige sus permisos antes de continuar.")
    if os.name == "nt":
        try:
            _restrict_windows_acl(target.parent, directory=True)
        except PermissionError as exc:
            parser.error(str(exc))
    fd = os.open(target, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as handle:
        json.dump({"password_hash": password_hash}, handle)
        handle.write("\n")
    print(f"Hash de operador guardado en {target}; no se guarda la contraseña en texto plano.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
