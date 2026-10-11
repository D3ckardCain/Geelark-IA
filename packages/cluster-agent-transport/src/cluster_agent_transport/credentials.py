"""Lectura de credenciales del directorio protegido por systemd.

El adaptador no descifra archivos propios ni almacena secretos: systemd debe montar
el directorio de credenciales del servicio. No usarlo fuera de un servicio configurado.
"""
from __future__ import annotations

import os
import re
import stat
from pathlib import Path
from typing import Protocol


class CredentialProviderError(RuntimeError):
    """Error genérico de carga de credencial; nunca incluye el secreto."""


class CredentialProvider(Protocol):
    """Contrato portable para proveedores de credenciales del sistema operativo."""

    def load_bearer_token(self) -> str:
        """Devuelve un token bearer sin espacios ni saltos de línea."""
        ...


class SystemdCredentialProvider:
    """Lee un token de LoadCredential/LoadCredentialEncrypted de systemd."""

    def __init__(
        self,
        *,
        credential_name: str = "geelark-agent-token",
        credentials_directory: str | os.PathLike[str] | None = None,
    ) -> None:
        if (
            not isinstance(credential_name, str)
            or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,127}", credential_name)
        ):
            raise ValueError("credential_name debe ser un nombre de archivo simple")
        if credentials_directory is not None and not isinstance(
            credentials_directory, (str, os.PathLike)
        ):
            raise ValueError("credentials_directory debe ser una ruta")
        self.credential_name = credential_name
        self.credentials_directory = (
            Path(credentials_directory) if credentials_directory is not None else None
        )

    def load_bearer_token(self) -> str:
        directory_value = (
            str(self.credentials_directory)
            if self.credentials_directory is not None
            else os.environ.get("CREDENTIALS_DIRECTORY")
        )
        if not directory_value:
            raise CredentialProviderError("SYSTEMD_CREDENTIALS_DIRECTORY_UNAVAILABLE")

        try:
            directory = Path(directory_value).resolve(strict=True)
            directory_stat = directory.stat()
        except OSError:
            raise CredentialProviderError("SYSTEMD_CREDENTIAL_DIRECTORY_UNAVAILABLE") from None
        if not directory.is_dir():
            raise CredentialProviderError("SYSTEMD_CREDENTIAL_DIRECTORY_INVALID")
        if directory_stat.st_mode & 0o077:
            raise CredentialProviderError("SYSTEMD_CREDENTIAL_DIRECTORY_PERMISSIONS_INVALID")

        path = directory / self.credential_name
        flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_NONBLOCK", 0)
        try:
            descriptor = os.open(path, flags)
        except OSError:
            raise CredentialProviderError("SYSTEMD_CREDENTIAL_UNAVAILABLE") from None

        try:
            info = os.fstat(descriptor)
            if not stat.S_ISREG(info.st_mode):
                raise CredentialProviderError("SYSTEMD_CREDENTIAL_FILE_INVALID")
            if info.st_mode & 0o077:
                raise CredentialProviderError("SYSTEMD_CREDENTIAL_FILE_PERMISSIONS_INVALID")
            raw = os.read(descriptor, 4097)
        finally:
            os.close(descriptor)

        if len(raw) > 4096:
            raise CredentialProviderError("SYSTEMD_CREDENTIAL_TOO_LARGE")
        if raw.endswith(b"\r\n"):
            raw = raw[:-2]
        elif raw.endswith(b"\n"):
            raw = raw[:-1]
        if len(raw) < 32 or any(byte < 33 or byte > 126 for byte in raw):
            raise CredentialProviderError("SYSTEMD_CREDENTIAL_FORMAT_INVALID")
        try:
            return raw.decode("ascii")
        except UnicodeDecodeError:
            raise CredentialProviderError("SYSTEMD_CREDENTIAL_FORMAT_INVALID") from None
