from sqlalchemy import Column, String, DateTime, Text, JSON, Integer
from sqlalchemy.dialects.postgresql import UUID, INET
from sqlalchemy.sql import func
import uuid
from ..core.database import Base


class Tenant(Base):
    """
    Tenant model for multi-tenancy support
    Each tenant represents a separate organization/application
    """
    __tablename__ = "tenants"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False, unique=True)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())


class AuditLog(Base):
    """
    Main audit log model
    Stores all user actions and system events with full context
    """
    __tablename__ = "audit_logs"

    # Primary identifier
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # Multi-tenancy
    tenant_id = Column(UUID(as_uuid=True), nullable=False)

    # User and session information
    user_id = Column(String(255), nullable=False)
    session_id = Column(String(255), nullable=True)

    # Action details
    action = Column(String(50), nullable=False)  # CREATE, UPDATE, DELETE, VIEW, etc.
    resource_type = Column(String(50), nullable=False)  # user, order, product, etc.
    resource_id = Column(String(255), nullable=False)

    # Timing information
    timestamp = Column(DateTime(timezone=True), server_default=func.now())

    # Request context
    ip_address = Column(INET, nullable=True)
    user_agent = Column(Text, nullable=True)

    # State changes (JSON format for flexibility)
    before_state = Column(JSON, nullable=True)
    after_state = Column(JSON, nullable=True)

    # Additional context
    metadata = Column(JSON, nullable=True)  # Custom fields
    message = Column(Text, nullable=True)  # Human readable description

    # Severity levels: INFO, WARNING, ERROR, CRITICAL
    severity = Column(String(20), default="INFO", nullable=False)

    # Audit trail for the audit logs themselves
    created_at = Column(DateTime(timezone=True), server_default=func.now())