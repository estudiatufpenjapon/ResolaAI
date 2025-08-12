from sqlalchemy import Column, String, Boolean, DateTime, Enum
from sqlalchemy.sql import func
import uuid
import enum
from ..core.database import Base


class UserRole(enum.Enum):
    ADMIN = "admin"
    AUDITOR = "auditor"
    USER = "user"


class User(Base):
    """
    modelo de usuario para authentication y authorization
    cada usuario tiene un rol que determina sus permisos
    """
    __tablename__ = "users"

    # id unico del usuario
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))

    # datos de login
    username = Column(String(50), unique=True, nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)

    # rol del usuario para authorization
    role = Column(Enum(UserRole), nullable=False, default=UserRole.USER)

    # tenant al que pertenece este usuario (para multi-tenancy)
    tenant_id = Column(String(36), nullable=False)

    # estado del usuario
    is_active = Column(Boolean, default=True)

    # timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())