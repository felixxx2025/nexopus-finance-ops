"""
RBAC — Role-Based Access Control para o Nexopus Finance Ops.

Roles:
  admin   — acesso total
  analista — leitura + upload + IA
  viewer  — somente leitura
"""
from __future__ import annotations

import json
import logging
from enum import Enum
from typing import Optional

from passlib.context import CryptContext

logger = logging.getLogger(__name__)

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class Role(str, Enum):
    ADMIN = "admin"
    ANALISTA = "analista"
    VIEWER = "viewer"


# Permissões por role
ROLE_PERMISSIONS: dict[Role, set[str]] = {
    Role.ADMIN: {
        "read", "write", "upload", "delete",
        "ai:run", "reports:generate", "admin:manage",
        "audit:read", "forecast:read", "reconcile:run",
    },
    Role.ANALISTA: {
        "read", "write", "upload",
        "ai:run", "reports:generate",
        "audit:read", "forecast:read", "reconcile:run",
    },
    Role.VIEWER: {
        "read", "forecast:read", "audit:read",
    },
}


class UserDB:
    """Repositório de usuários em memória (admin + extras via JSON env)."""

    def __init__(self, admin_username: str, admin_password_hash: str, extra_json: Optional[str] = None):
        self._users: dict[str, dict] = {}

        # Admin sempre presente
        self._users[admin_username] = {
            "username": admin_username,
            "password_hash": admin_password_hash,
            "role": Role.ADMIN,
        }

        # Usuários extras via EXTRA_USERS_JSON
        if extra_json:
            try:
                extras = json.loads(extra_json)
                for u in extras:
                    uname = u.get("username", "").strip()
                    role_str = u.get("role", "viewer").lower()
                    ph = u.get("password_hash", "")
                    if uname and ph:
                        try:
                            role = Role(role_str)
                        except ValueError:
                            role = Role.VIEWER
                        self._users[uname] = {
                            "username": uname,
                            "password_hash": ph,
                            "role": role,
                        }
            except Exception as e:
                logger.warning("Erro ao parsear EXTRA_USERS_JSON: %s", e)

    def authenticate(self, username: str, password: str) -> Optional[dict]:
        user = self._users.get(username)
        if not user:
            return None
        if not pwd_context.verify(password, user["password_hash"]):
            return None
        return user

    def get_user(self, username: str) -> Optional[dict]:
        return self._users.get(username)


def require_permission(user: dict, permission: str) -> None:
    """Levanta PermissionError se o usuário não tiver a permissão solicitada."""
    role = Role(user.get("role", "viewer"))
    if permission not in ROLE_PERMISSIONS.get(role, set()):
        raise PermissionError(
            f"Usuário '{user.get('username')}' (role={role}) não tem permissão '{permission}'."
        )


def has_permission(user: dict, permission: str) -> bool:
    """Retorna True se o usuário tiver a permissão solicitada."""
    role = Role(user.get("role", "viewer"))
    return permission in ROLE_PERMISSIONS.get(role, set())
