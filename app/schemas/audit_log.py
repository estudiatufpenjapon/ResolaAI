from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, Dict, Any


class TenantBase(BaseModel):
    """esquema base para datos de tenant"""
    # nombre obligatorio del tenant, con longitud minima 1 y maxima 255 caracteres
    name: str = Field(..., min_length=1, max_length=255)

    # descripcion opcional del tenant, puede ser None
    description: Optional[str] = None


class TenantCreate(TenantBase):
    """esquema para crear un tenant nuevo
    hereda todos los campos de TenantBase sin cambios"""
    pass


class TenantResponse(TenantBase):
    """esquema para devolver datos de tenant en respuestas
    incluye campos extra generados por la base de datos"""
    id: str  # id unico del tenant
    created_at: datetime  # fecha y hora de creacion del tenant
    updated_at: Optional[datetime] = None  # fecha y hora de ultima actualizacion, puede ser None

    class Config:
        # permite crear este modelo a partir de objetos que no son dict (como objetos SQLAlchemy)
        from_attributes = True


class AuditLogBase(BaseModel):
    """esquema base para datos de audit log, define los campos principales"""

    tenant_id: str    # id del tenant al que pertenece este log (obligatorio)

    user_id: str = Field(..., min_length=1, max_length=255)  # id del usuario que realizo la accion

    session_id: Optional[str] = Field(None, max_length=255)  # id de la sesion, opcional

    action: str = Field(..., min_length=1, max_length=50)  # tipo de accion (crear, actualizar, borrar, etc)

    resource_type: str = Field(..., min_length=1, max_length=50)  # tipo de recurso afectado

    resource_id: str = Field(..., min_length=1, max_length=255)  # id del recurso afectado

    ip_address: Optional[str] = None  # direccion ip del cliente, opcional

    user_agent: Optional[str] = None  # informacion del navegador o cliente, opcional

    # estado antes de la accion en formato diccionario JSON, opcional
    before_state: Optional[Dict[str, Any]] = None

    # estado despues de la accion en formato diccionario JSON, opcional
    after_state: Optional[Dict[str, Any]] = None

    # metadatos adicionales personalizados en formato diccionario JSON, opcional
    custom_metadata: Optional[Dict[str, Any]] = None

    message: Optional[str] = None  # mensaje descriptivo legible para humanos, opcional

    # nivel de severidad, con valor por defecto "INFO"
    # el patron valida que solo pueda ser uno de los siguientes valores exactos
    severity: str = Field(default="INFO", pattern="^(INFO|WARNING|ERROR|CRITICAL)$")


class AuditLogCreate(AuditLogBase):
    """esquema para crear una nueva entrada de audit log
    hereda todos los campos del esquema base sin cambios"""
    pass


class AuditLogResponse(AuditLogBase):
    """esquema para devolver datos de audit log en respuestas
    incluye campos extra generados por la base de datos"""

    id: str    # id unico del log

    timestamp: datetime  # fecha y hora en que ocurrio el evento

    created_at: datetime  # fecha y hora en que se registro el log

    class Config:
        # permite crear este modelo a partir de objetos SQLAlchemy u otros que no sean dict
        from_attributes = True


class AuditLogFilter(BaseModel):
    """esquema para filtrar los audit logs en consultas"""

    tenant_id: Optional[str  ] = None  # filtrar por tenant id, opcional

    user_id: Optional[str] = None  # filtrar por user id, opcional

    action: Optional[str] = None  # filtrar por tipo de accion, opcional

    resource_type: Optional[str] = None  # filtrar por tipo de recurso, opcional

    severity: Optional[str] = None  # filtrar por nivel de severidad, opcional

    start_date: Optional[datetime] = None  # filtrar logs despues de esta fecha, opcional

    end_date: Optional[datetime] = None  # filtrar logs antes de esta fecha, opcional


class PaginationParams(BaseModel):
    """esquema para parametros de paginacion en consultas"""

    page: int = Field(default=1, ge=1)  # numero de pagina, minimo 1, por defecto 1

    page_size: int = Field(default=50, ge=1, le=1000)  # elementos por pagina, minimo 1 maximo 1000, por defecto 50


class AuditLogListResponse(BaseModel):
    """esquema para devolver listas paginadas de audit logs"""

    logs: list[AuditLogResponse]  # lista con los logs de auditoria en la pagina actual

    total: int  # total de logs encontrados sin paginar

    page: int  # pagina actual

    page_size: int  # cantidad de elementos por pagina

    total_pages: int  # total de paginas calculadas segun total y page_size
