from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import datetime

from ...core.database import get_db
from ...core.auth import get_current_active_user, require_admin
from ...models.audit_log import AuditLog, Tenant
from ...models.user import User, UserRole
from ...schemas.audit_log import (
    AuditLogCreate,
    AuditLogResponse,
    AuditLogListResponse,
    TenantCreate,
    TenantResponse,
    PaginationParams
)

# crear el router para los endpoints de audit log
router = APIRouter(prefix="/logs", tags=["audit-logs"])


# =================== ENDPOINTS DE TENANTS PRIMERO ===================
@router.post("/tenants", response_model=TenantResponse)
def create_tenant(
        tenant_data: TenantCreate,
        db: Session = Depends(get_db),
        current_user: User = Depends(require_admin)  # SOLO ADMINS PUEDEN CREAR TENANTS
):
    """
    crear un nuevo tenant
    requiere rol de administrador
    """
    db_tenant = Tenant(**tenant_data.model_dump())
    db.add(db_tenant)
    db.commit()
    db.refresh(db_tenant)

    return db_tenant


@router.get("/tenants", response_model=List[TenantResponse])
def get_tenants(
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_active_user)  # REQUIERE AUTENTICACIÓN
):
    """
    obtener todos los tenants
    usuarios normales solo ven su tenant, admins ven todos
    """
    if current_user.role == UserRole.ADMIN:
        # admins pueden ver todos los tenants
        return db.query(Tenant).all()
    else:
        # usuarios normales solo ven su propio tenant
        return db.query(Tenant).filter(Tenant.id == current_user.tenant_id).all()


@router.get("/tenants/{tenant_id}", response_model=TenantResponse)
def get_tenant(
        tenant_id: str,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_active_user)  # REQUIERE AUTENTICACIÓN
):
    """
    obtener un tenant específico por su ID
    usuarios solo pueden acceder a su propio tenant, admins a cualquiera
    """
    # verificar permisos de acceso al tenant
    if current_user.role != UserRole.ADMIN and current_user.tenant_id != tenant_id:
        raise HTTPException(status_code=403, detail="Access denied to this tenant")

    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if not tenant:
        raise HTTPException(status_code=404, detail="tenant not found")

    return tenant


@router.put("/tenants/{tenant_id}", response_model=TenantResponse)
def update_tenant(
        tenant_id: str,
        tenant_data: TenantCreate,
        db: Session = Depends(get_db),
        current_user: User = Depends(require_admin)  # SOLO ADMINS PUEDEN ACTUALIZAR
):
    """
    actualizar un tenant existente
    requiere rol de administrador
    """
    # buscar el tenant existente
    existing_tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if not existing_tenant:
        raise HTTPException(status_code=404, detail="tenant not found")

    # verificar que el nuevo nombre no esté en uso por otro tenant
    if tenant_data.name != existing_tenant.name:
        name_exists = db.query(Tenant).filter(
            Tenant.name == tenant_data.name,
            Tenant.id != tenant_id
        ).first()
        if name_exists:
            raise HTTPException(status_code=400, detail="tenant name already exists")

    # actualizar campos
    existing_tenant.name = tenant_data.name
    existing_tenant.description = tenant_data.description

    db.commit()
    db.refresh(existing_tenant)

    return existing_tenant


@router.delete("/tenants/{tenant_id}")
def delete_tenant(
        tenant_id: str,
        force: bool = Query(False, description="forzar eliminación aunque tenga audit logs"),
        db: Session = Depends(get_db),
        current_user: User = Depends(require_admin)  # SOLO ADMINS PUEDEN ELIMINAR
):
    """
    eliminar un tenant
    requiere rol de administrador
    """
    # buscar el tenant
    tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if not tenant:
        raise HTTPException(status_code=404, detail="tenant not found")

    # verificar si tiene audit logs asociados
    logs_count = db.query(AuditLog).filter(AuditLog.tenant_id == tenant_id).count()

    if logs_count > 0 and not force:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot delete tenant with {logs_count} audit logs. Use force=true to delete anyway."
        )

    # si force=true, eliminar primero todos los audit logs del tenant
    if force and logs_count > 0:
        db.query(AuditLog).filter(AuditLog.tenant_id == tenant_id).delete()

    # eliminar el tenant
    db.delete(tenant)
    db.commit()

    return {
        "message": f"tenant {tenant_id} deleted successfully",
        "logs_deleted": logs_count if force else 0
    }


@router.patch("/tenants/{tenant_id}", response_model=TenantResponse)
def partial_update_tenant(
        tenant_id: str,
        name: Optional[str] = Query(None, description="nuevo nombre del tenant"),
        description: Optional[str] = Query(None, description="nueva descripción del tenant"),
        db: Session = Depends(get_db),
        current_user: User = Depends(require_admin)  # SOLO ADMINS PUEDEN ACTUALIZAR
):
    """
    actualización parcial de un tenant
    requiere rol de administrador
    """
    # buscar el tenant existente
    existing_tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
    if not existing_tenant:
        raise HTTPException(status_code=404, detail="tenant not found")

    # actualizar solo los campos proporcionados
    if name is not None:
        # verificar que el nuevo nombre no esté en uso
        name_exists = db.query(Tenant).filter(
            Tenant.name == name,
            Tenant.id != tenant_id
        ).first()
        if name_exists:
            raise HTTPException(status_code=400, detail="tenant name already exists")

        existing_tenant.name = name

    if description is not None:
        existing_tenant.description = description

    # verificar que al menos un campo fue actualizado
    if name is None and description is None:
        raise HTTPException(status_code=400, detail="at least one field must be provided for update")

    db.commit()
    db.refresh(existing_tenant)

    return existing_tenant


# =================== ENDPOINTS DE STATS ===================
@router.get("/stats", response_model=dict)
def get_audit_log_stats(
        tenant_id: Optional[str] = Query(None, description="filtrar estadisticas por tenant id"),
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_active_user)  # REQUIERE AUTENTICACIÓN
):
    """
    obtener estadisticas de los audit logs
    usuarios solo pueden ver stats de su tenant, admins de cualquiera
    """
    # determinar qué tenant puede ver el usuario
    if current_user.role == UserRole.ADMIN:
        # admins pueden especificar cualquier tenant_id o ver todos
        allowed_tenant_id = tenant_id
    else:
        # usuarios normales solo pueden ver su propio tenant
        allowed_tenant_id = current_user.tenant_id
        if tenant_id and tenant_id != current_user.tenant_id:
            raise HTTPException(status_code=403, detail="Access denied to this tenant")

    query = db.query(AuditLog)

    if allowed_tenant_id:
        query = query.filter(AuditLog.tenant_id == allowed_tenant_id)

    total_logs = query.count()

    # conteo por accion
    action_counts = {}
    actions = db.query(AuditLog.action).distinct().all()
    for (action,) in actions:
        count = query.filter(AuditLog.action == action).count()
        action_counts[action] = count

    # conteo por severidad
    severity_counts = {}
    severities = db.query(AuditLog.severity).distinct().all()
    for (severity,) in severities:
        count = query.filter(AuditLog.severity == severity).count()
        severity_counts[severity] = count

    return {
        "total_logs": total_logs,
        "action_counts": action_counts,
        "severity_counts": severity_counts
    }


# =================== ENDPOINTS DE AUDIT LOGS ===================
@router.post("/", response_model=AuditLogResponse)
def create_audit_log(
        log_data: AuditLogCreate,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_active_user)  # REQUIERE AUTENTICACIÓN
):
    """
    crear una nueva entrada de audit log
    usuarios solo pueden crear logs en su propio tenant
    """
    # verificar permisos de tenant
    if current_user.role != UserRole.ADMIN and log_data.tenant_id != current_user.tenant_id:
        raise HTTPException(status_code=403, detail="Cannot create logs for other tenants")

    # verificar si el tenant existe
    tenant = db.query(Tenant).filter(Tenant.id == log_data.tenant_id).first()
    if not tenant:
        raise HTTPException(status_code=404, detail="tenant not found")

    # crear nuevo audit log
    db_log = AuditLog(**log_data.model_dump())
    db.add(db_log)
    db.commit()
    db.refresh(db_log)

    return db_log


@router.get("/", response_model=AuditLogListResponse)
def get_audit_logs(
        # parametros para paginacion
        page: int = Query(default=1, ge=1, description="numero de pagina"),
        page_size: int = Query(default=50, ge=1, le=1000, description="elementos por pagina"),

        # parametros para filtrado
        tenant_id: Optional[str] = Query(None, description="filtrar por tenant id"),
        user_id: Optional[str] = Query(None, description="filtrar por user id"),
        action: Optional[str] = Query(None, description="filtrar por tipo de accion"),
        resource_type: Optional[str] = Query(None, description="filtrar por tipo de recurso"),
        severity: Optional[str] = Query(None, description="filtrar por nivel de severidad"),
        start_date: Optional[datetime] = Query(None, description="filtrar logs despues de esta fecha"),
        end_date: Optional[datetime] = Query(None, description="filtrar logs antes de esta fecha"),

        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_active_user)  # REQUIERE AUTENTICACIÓN
):
    """
    obtener audit logs con filtros y paginacion
    usuarios solo pueden ver logs de su tenant, admins de cualquiera
    """
    # construir la consulta con los filtros
    query = db.query(AuditLog)

    # aplicar filtro de tenant basado en permisos del usuario
    if current_user.role == UserRole.ADMIN:
        # admins pueden ver cualquier tenant si especifican tenant_id
        if tenant_id:
            query = query.filter(AuditLog.tenant_id == tenant_id)
    else:
        # usuarios normales solo pueden ver su propio tenant
        if tenant_id and tenant_id != current_user.tenant_id:
            raise HTTPException(status_code=403, detail="Access denied to this tenant")
        query = query.filter(AuditLog.tenant_id == current_user.tenant_id)

    # aplicar otros filtros
    if user_id:
        query = query.filter(AuditLog.user_id == user_id)
    if action:
        query = query.filter(AuditLog.action == action)
    if resource_type:
        query = query.filter(AuditLog.resource_type == resource_type)
    if severity:
        query = query.filter(AuditLog.severity == severity)
    if start_date:
        query = query.filter(AuditLog.timestamp >= start_date)
    if end_date:
        query = query.filter(AuditLog.timestamp <= end_date)

    # ordenar por timestamp descendente (los mas recientes primero)
    query = query.order_by(AuditLog.timestamp.desc())

    # obtener el total para la paginacion
    total = query.count()

    # aplicar paginacion con offset y limit
    offset = (page - 1) * page_size
    logs = query.offset(offset).limit(page_size).all()

    # calcular total de paginas
    total_pages = (total + page_size - 1) // page_size

    return AuditLogListResponse(
        logs=logs,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages
    )


@router.get("/{log_id}", response_model=AuditLogResponse)
def get_audit_log(
        log_id: str,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_active_user)  # REQUIERE AUTENTICACIÓN
):
    """
    obtener un log especifico por su id
    usuarios solo pueden ver logs de su tenant
    """
    log = db.query(AuditLog).filter(AuditLog.id == log_id).first()
    if not log:
        raise HTTPException(status_code=404, detail="audit log not found")

    # verificar permisos de acceso al tenant del log
    if current_user.role != UserRole.ADMIN and log.tenant_id != current_user.tenant_id:
        raise HTTPException(status_code=403, detail="Access denied to this audit log")

    return log