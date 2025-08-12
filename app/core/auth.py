from fastapi import HTTPException, Depends, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from typing import Optional

from .database import get_db
from .security import verify_token
from ..models.user import User, UserRole
from ..schemas.user import TokenData

# configurar el esquema de autenticacion Bearer
security = HTTPBearer()


def get_current_user(
        credentials: HTTPAuthorizationCredentials = Depends(security),
        db: Session = Depends(get_db)
) -> User:
    """
    obtener el usuario actual desde el JWT token
    esta dependencia se usa en endpoints que requieren autenticacion
    """
    # extraer el token del header Authorization
    token = credentials.credentials

    # verificar el token
    payload = verify_token(token)
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # extraer user_id del payload
    user_id: str = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # buscar el usuario en la base de datos
    user = db.query(User).filter(User.id == user_id, User.is_active == True).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return user


def get_current_active_user(current_user: User = Depends(get_current_user)) -> User:
    """
    verificar que el usuario actual este activo
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    return current_user


def require_role(required_role: UserRole):
    """
    crear una dependencia que requiere un rol especifico
    uso: require_admin = require_role(UserRole.ADMIN)
    """

    def role_checker(current_user: User = Depends(get_current_active_user)) -> User:
        if current_user.role != required_role:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Operation requires {required_role.value} role"
            )
        return current_user

    return role_checker


def require_tenant_access(tenant_id: str):
    """
    verificar que el usuario tenga acceso al tenant especificado
    """

    def tenant_checker(current_user: User = Depends(get_current_active_user)) -> User:
        # los admins pueden acceder a cualquier tenant
        if current_user.role == UserRole.ADMIN:
            return current_user

        # otros usuarios solo pueden acceder a su propio tenant
        if current_user.tenant_id != tenant_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied to this tenant"
            )

        return current_user

    return tenant_checker


# dependencias pre-configuradas para roles comunes
require_admin = require_role(UserRole.ADMIN)
require_auditor_or_admin = lambda current_user: current_user if current_user.role in [UserRole.ADMIN,
                                                                                      UserRole.AUDITOR] else HTTPException(
    status_code=403, detail="Requires auditor or admin role")
