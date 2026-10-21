"""Inicializa el hash de contraseña del operador sin imprimir secretos."""
from __future__ import annotations

import argparse
import json
import os
import stat
from getpass import getpass
from pathlib import Path

from .auth import _restrict_windows_acl, _verify_windows_acl_no_untrusted_writers, hash_operator_password


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
    if os.name == "posix":
        state_dir_info = target.parent.stat()
        if state_dir_info.st_uid != os.geteuid():
            parser.error("El directorio de destino debe pertenecer al usuario que ejecuta el inicializador.")
        if stat.S_IMODE(state_dir_info.st_mode) & 0o077:
            parser.error("El directorio de destino debe ser privado (0700); corrige sus permisos antes de continuar.")
        parent_info = target.parent.parent.stat()
        if parent_info.st_uid not in {os.geteuid(), 0}:
            parser.error("El directorio superior debe pertenecer al usuario actual o a root.")
        parent_mode = stat.S_IMODE(parent_info.st_mode)
        if parent_mode & 0o022 and not (
            parent_mode & stat.S_ISVTX and parent_info.st_uid == 0
        ):
            parser.error("El directorio superior permite escritura a grupo/otros y no es un directorio raíz con sticky bit.")
    if os.name == "nt":
        try:
            _verify_windows_acl_no_untrusted_writers(target.parent.parent)
            _restrict_windows_acl(target.parent, directory=True)
        except PermissionError as exc:
            parser.error(str(exc))
    fd = os.open(target, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as handle:
        json.dump({"password_hash": password_hash}, handle)
        handle.write("\n")
    if os.name == "nt":
        try:
            _restrict_windows_acl(target, directory=False)
        except PermissionError as exc:
            target.unlink(missing_ok=True)
            parser.error(str(exc))
    print(f"Hash de operador guardado en {target}; no se guarda la contraseña en texto plano.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
