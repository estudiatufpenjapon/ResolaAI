from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from datetime import timedelta
from typing import List

from ...core.database import get_db
from ...core.security import verify_password, get_password_hash, create_access_token
from ...core.auth import get_current_active_user, require_admin
from ...core.config import settings
from ...models.user import User, UserRole
from ...schemas.user import (
    UserCreate,
    UserResponse,
    UserLogin,
    Token,
    UserRole as UserRoleSchema
)

# crear el router para autenticacion
router = APIRouter(prefix="/auth", tags=["authentication"])


@router.post("/register", response_model=UserResponse)
def register_user(
        user_data: UserCreate,
        db: Session = Depends(get_db),
        current_user: User = Depends(require_admin)  # solo admins pueden crear usuarios
):
    """
    registrar un nuevo usuario
    solo los administradores pueden crear nuevos usuarios
    """
    # verificar que el username no exista
    existing_user = db.query(User).filter(User.username == user_data.username).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )

    # verificar que el email no exista
    existing_email = db.query(User).filter(User.email == user_data.email).first()
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    # crear el hash de la password
    hashed_password = get_password_hash(user_data.password)

    # crear el nuevo usuario
    db_user = User(
        username=user_data.username,
        email=user_data.email,
        hashed_password=hashed_password,
        role=user_data.role,
        tenant_id=user_data.tenant_id,
        is_active=user_data.is_active
    )

    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    return db_user


@router.post("/login", response_model=Token)
def login_user(
        form_data: OAuth2PasswordRequestForm = Depends(),
        db: Session = Depends(get_db)
):
    """
    hacer login con username y password
    devuelve un JWT token para autenticacion
    """
    # buscar el usuario por username
    user = db.query(User).filter(User.username == form_data.username).first()

    # verificar que el usuario existe y la password es correcta
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # verificar que el usuario este activo
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )

    # crear el access token
    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = create_access_token(
        data={
            "sub": user.id,
            "username": user.username,
            "role": user.role.value,
            "tenant_id": user.tenant_id
        },
        expires_delta=access_token_expires
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": settings.access_token_expire_minutes * 60,  # en segundos
        "user_id": user.id,
        "role": user.role.value,
        "tenant_id": user.tenant_id
    }


@router.get("/me", response_model=UserResponse)
def get_current_user_info(current_user: User = Depends(get_current_active_user)):
    """
    obtener informacion del usuario actual
    requiere estar autenticado
    """
    return current_user


@router.get("/users", response_model=List[UserResponse])
def list_users(
        db: Session = Depends(get_db),
        current_user: User = Depends(require_admin)  # solo admins pueden ver todos los usuarios
):
    """
    listar todos los usuarios
    solo administradores pueden acceder
    """
    users = db.query(User).all()
    return users


@router.get("/users/{user_id}", response_model=UserResponse)
def get_user(
        user_id: str,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_active_user)
):
    """
    obtener un usuario especifico
    usuarios normales solo pueden ver su propia informacion
    admins pueden ver cualquier usuario
    """
    # verificar permisos
    if current_user.role != UserRole.ADMIN and current_user.id != user_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    return user


@router.patch("/users/{user_id}/deactivate")
def deactivate_user(
        user_id: str,
        db: Session = Depends(get_db),
        current_user: User = Depends(require_admin)  # solo admins pueden desactivar usuarios
):
    """
    desactivar un usuario
    solo administradores pueden hacerlo
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    user.is_active = False
    db.commit()

    return {"message": f"User {user.username} deactivated successfully"}


@router.patch("/users/{user_id}/activate")
def activate_user(
        user_id: str,
        db: Session = Depends(get_db),
        current_user: User = Depends(require_admin)
):
    """
    activar un usuario desactivado
    solo administradores pueden hacerlo
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    user.is_active = True
    db.commit()

    return {"message": f"User {user.username} activated successfully"}