from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, Dict, Any
from uuid import UUID


class TenantBase(BaseModel):
    """Base schema for tenant data"""
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None


class TenantCreate(TenantBase):
    """Schema for creating a new tenant"""
    pass


class TenantResponse(TenantBase):
    """Schema for tenant response"""
    id: UUID
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True  # For SQLAlchemy compatibility


class AuditLogBase(BaseModel):
    """Base schema for audit log data"""
    tenant_id: UUID
    user_id: str = Field(..., min_length=1, max_length=255)
    session_id: Optional[str] = Field(None, max_length=255)
    action: str = Field(..., min_length=1, max_length=50)
    resource_type: str = Field(..., min_length=1, max_length=50)
    resource_id: str = Field(..., min_length=1, max_length=255)
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    before_state: Optional[Dict[str, Any]] = None
    after_state: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None
    message: Optional[str] = None
    severity: str = Field(default="INFO", regex="^(INFO|WARNING|ERROR|CRITICAL)$")


class AuditLogCreate(AuditLogBase):
    """Schema for creating a new audit log entry"""
    pass


class AuditLogResponse(AuditLogBase):
    """Schema for audit log response"""
    id: UUID
    timestamp: datetime
    created_at: datetime

    class Config:
        from_attributes = True  # For SQLAlchemy compatibility


class AuditLogFilter(BaseModel):
    """Schema for filtering audit logs"""
    tenant_id: Optional[UUID] = None
    user_id: Optional[str] = None
    action: Optional[str] = None
    resource_type: Optional[str] = None
    severity: Optional[str] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None


class PaginationParams(BaseModel):
    """Schema for pagination parameters"""
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=50, ge=1, le=1000)


class AuditLogListResponse(BaseModel):
    """Schema for paginated audit log list response"""
    logs: list[AuditLogResponse]
    total: int
    page: int
    page_size: int
    total_pages: int