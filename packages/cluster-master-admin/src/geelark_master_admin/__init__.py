"""API administrativa local para PC-MASTER; no abre listeners al importar."""

from .app import create_admin_app
from .auth import hash_operator_password

__all__ = ["create_admin_app", "hash_operator_password"]
