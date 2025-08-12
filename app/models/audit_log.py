from sqlalchemy import Column, String, DateTime, Text, JSON, Integer
from sqlalchemy.sql import func
import uuid
from ..core.database import Base


class Tenant(Base):
    """
    modelo Tenant para soporte multi-tenancy
    cada tenant representa una organizacion o aplicacion separada
    """
    __tablename__ = "tenants"

    # id unico del tenant, generado automaticamente como UUID string simple
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))

    # nombre del tenant, obligatorio y unico
    name = Column(String(255), nullable=False, unique=True)

    # descripcion opcional del tenant, texto libre
    description = Column(Text, nullable=True)

    # fecha y hora de creacion, se pone automaticamente al crear el registro
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # fecha y hora de la ultima actualizacion, se actualiza automaticamente
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class AuditLog(Base):
    """
    modelo principal de auditoria
    almacena todas las acciones de usuario y eventos del sistema con contexto completo
    """
    __tablename__ = "audit_logs"

    # identificador unico del log, generado automaticamente como UUID string simple
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))

    # multi-tenancy: id del tenant al que pertenece este log (obligatorio)
    tenant_id = Column(String(36), nullable=False)

    # informacion de usuario y sesion
    user_id = Column(String(255), nullable=False)  # id del usuario que realizo la accion
    session_id = Column(String(255), nullable=True)  # id de la sesion del usuario (opcional)

    # detalles de la accion
    action = Column(String(50), nullable=False)  # tipo de accion (crear, actualizar, borrar, ver, etc)
    resource_type = Column(String(50), nullable=False)  # tipo de recurso afectado (usuario, pedido, producto, etc)
    resource_id = Column(String(255), nullable=False)  # id del recurso afectado

    # informacion temporal
    timestamp = Column(DateTime(timezone=True), server_default=func.now())  # fecha y hora del evento

    # contexto de la peticion
    ip_address = Column(String(45), nullable=True)  # direccion ip del cliente (opcional)
    user_agent = Column(Text, nullable=True)  # informacion del navegador o cliente (opcional)

    # cambios de estado antes y despues
    before_state = Column(JSON, nullable=True)  # estado del recurso antes de la accion (opcional)
    after_state = Column(JSON, nullable=True)  # estado del recurso despues de la accion (opcional)

    # contexto adicional
    custom_metadata = Column(JSON, nullable=True)  # metadatos personalizados (opcional)
    message = Column(Text, nullable=True)  # descripcion legible para humanos (opcional)

    # niveles de severidad: INFO, WARNING, ERROR, CRITICAL
    severity = Column(String(20), default="INFO", nullable=False)

    # auditoria para los propios logs
    created_at = Column(DateTime(timezone=True), server_default=func.now())  # fecha y hora de creacion del log
