from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
from uuid import UUID
from datetime import datetime

from ...core.database import get_db
from ...models.audit_log import AuditLog, Tenant
from ...schemas.audit_log import (
    AuditLogCreate,
    AuditLogResponse,
    AuditLogListResponse,
    TenantCreate,
    TenantResponse,
    PaginationParams
)

# Create router for audit log endpoints
router = APIRouter(prefix="/logs", tags=["audit-logs"])


@router.post("/", response_model=AuditLogResponse)
def create_audit_log(
        log_data: AuditLogCreate,
        db: Session = Depends(get_db)
):
    """
    Create a new audit log entry

    Creates a new audit log with all provided information.
    Validates tenant exists before creating the log.
    """
    # Check if tenant exists
    tenant = db.query(Tenant).filter(Tenant.id == log_data.tenant_id).first()
    if not tenant:
        raise HTTPException(status_code=404, detail="Tenant not found")

    # Create new audit log
    db_log = AuditLog(**log_data.dict())
    db.add(db_log)
    db.commit()
    db.refresh(db_log)

    return db_log


@router.get("/", response_model=AuditLogListResponse)
def get_audit_logs(
        # Pagination parameters
        page: int = Query(default=1, ge=1, description="Page number"),
        page_size: int = Query(default=50, ge=1, le=1000, description="Items per page"),

        # Filter parameters
        tenant_id: Optional[UUID] = Query(None, description="Filter by tenant ID"),
        user_id: Optional[str] = Query(None, description="Filter by user ID"),
        action: Optional[str] = Query(None, description="Filter by action type"),
        resource_type: Optional[str] = Query(None, description="Filter by resource type"),
        severity: Optional[str] = Query(None, description="Filter by severity level"),
        start_date: Optional[datetime] = Query(None, description="Filter logs after this date"),
        end_date: Optional[datetime] = Query(None, description="Filter logs before this date"),

        db: Session = Depends(get_db)
):
    """
    Get audit logs with filtering and pagination

    Returns a paginated list of audit logs with optional filters.
    Supports filtering by tenant, user, action, resource type, severity, and date range.
    """
    # Build query with filters
    query = db.query(AuditLog)

    if tenant_id:
        query = query.filter(AuditLog.tenant_id == tenant_id)
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

    # Order by timestamp descending (newest first)
    query = query.order_by(AuditLog.timestamp.desc())

    # Get total count for pagination
    total = query.count()

    # Apply pagination
    offset = (page - 1) * page_size
    logs = query.offset(offset).limit(page_size).all()

    # Calculate total pages
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
        log_id: UUID,
        db: Session = Depends(get_db)
):
    """
    Get a specific audit log entry by ID

    Returns detailed information for a single audit log entry.
    """
    log = db.query(AuditLog).filter(AuditLog.id == log_id).first()
    if not log:
        raise HTTPException(status_code=404, detail="Audit log not found")

    return log


@router.get("/stats", response_model=dict)
def get_audit_log_stats(
        tenant_id: Optional[UUID] = Query(None, description="Filter stats by tenant ID"),
        db: Session = Depends(get_db)
):
    """
    Get audit log statistics

    Returns basic statistics about audit logs including counts by action and severity.
    """
    query = db.query(AuditLog)

    if tenant_id:
        query = query.filter(AuditLog.tenant_id == tenant_id)

    total_logs = query.count()

    # Count by action
    action_counts = {}
    actions = db.query(AuditLog.action).distinct().all()
    for (action,) in actions:
        count = query.filter(AuditLog.action == action).count()
        action_counts[action] = count

    # Count by severity
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


# Tenant management endpoints
@router.post("/tenants", response_model=TenantResponse)
def create_tenant(
        tenant_data: TenantCreate,
        db: Session = Depends(get_db)
):
    """
    Create a new tenant

    Creates a new tenant for multi-tenant audit logging.
    """
    db_tenant = Tenant(**tenant_data.dict())
    db.add(db_tenant)
    db.commit()
    db.refresh(db_tenant)

    return db_tenant


@router.get("/tenants", response_model=list[TenantResponse])
def get_tenants(db: Session = Depends(get_db)):
    """
    Get all tenants

    Returns a list of all available tenants.
    """
    return db.query(Tenant).all()