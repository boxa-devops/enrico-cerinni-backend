from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    Text,
    JSON,
    ForeignKey,
    Enum,
    Boolean,
)
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.database import Base
import enum


class ReportType(str, enum.Enum):
    SALES = "sales"
    FINANCE = "finance"
    INVENTORY = "inventory"
    CLIENTS = "clients"
    PERFORMANCE = "performance"
    CUSTOM = "custom"


class ReportStatus(str, enum.Enum):
    GENERATING = "generating"
    COMPLETED = "completed"
    FAILED = "failed"


class ReportFormat(str, enum.Enum):
    JSON = "json"
    PDF = "pdf"
    EXCEL = "excel"
    CSV = "csv"


class Report(Base):
    """
    Model for storing report metadata and configurations.
    Used for custom reports, scheduled reports, and report history.
    """
    __tablename__ = "reports"

    id = Column(Integer, primary_key=True, index=True)
    
    # Basic report information
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    report_type = Column(Enum(ReportType), nullable=False)
    
    # Report configuration
    config = Column(JSON, nullable=True)  # Store report parameters, filters, etc.
    
    # Report status and metadata
    status = Column(Enum(ReportStatus), default=ReportStatus.GENERATING)
    format = Column(Enum(ReportFormat), default=ReportFormat.JSON)
    file_path = Column(String(500), nullable=True)  # Path to generated report file
    
    # Scheduling and automation
    is_scheduled = Column(Boolean, default=False)
    schedule_config = Column(JSON, nullable=True)  # Cron-like schedule configuration
    
    # User and timestamps
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    generated_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    user = relationship("User", backref="reports")


class ReportTemplate(Base):
    """
    Model for storing reusable report templates.
    Templates can be used to create new reports with predefined configurations.
    """
    __tablename__ = "report_templates"

    id = Column(Integer, primary_key=True, index=True)
    
    # Template information
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    report_type = Column(Enum(ReportType), nullable=False)
    
    # Template configuration
    config_template = Column(JSON, nullable=False)  # Default configuration
    
    # Template metadata
    is_system_template = Column(Boolean, default=False)  # System vs user templates
    is_active = Column(Boolean, default=True)
    
    # User and timestamps
    created_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # Relationships
    creator = relationship("User", backref="created_report_templates")


class ReportExecution(Base):
    """
    Model for tracking report execution history and performance.
    """
    __tablename__ = "report_executions"

    id = Column(Integer, primary_key=True, index=True)
    
    # Report reference
    report_id = Column(Integer, ForeignKey("reports.id"), nullable=True)
    report_type = Column(Enum(ReportType), nullable=False)
    
    # Execution details
    parameters = Column(JSON, nullable=True)  # Parameters used for this execution
    status = Column(Enum(ReportStatus), nullable=False)
    
    # Performance metrics
    execution_time_ms = Column(Integer, nullable=True)  # Execution time in milliseconds
    data_points = Column(Integer, nullable=True)  # Number of data points processed
    file_size_bytes = Column(Integer, nullable=True)  # Size of generated file
    
    # Error handling
    error_message = Column(Text, nullable=True)
    
    # Timestamps
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)
    
    # User reference
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Relationships
    report = relationship("Report", backref="executions")
    user = relationship("User", backref="report_executions")
