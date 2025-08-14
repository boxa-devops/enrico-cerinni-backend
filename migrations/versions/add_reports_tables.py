"""Add reports tables

Revision ID: add_reports_tables
Revises: 
Create Date: 2024-01-15 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'add_reports_tables'
down_revision = None  # Update this with the latest revision ID
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create report_type enum
    report_type_enum = postgresql.ENUM(
        'sales', 'finance', 'inventory', 'clients', 'performance', 'custom',
        name='reporttype'
    )
    report_type_enum.create(op.get_bind())
    
    # Create report_status enum
    report_status_enum = postgresql.ENUM(
        'generating', 'completed', 'failed',
        name='reportstatus'
    )
    report_status_enum.create(op.get_bind())
    
    # Create report_format enum
    report_format_enum = postgresql.ENUM(
        'json', 'pdf', 'excel', 'csv',
        name='reportformat'
    )
    report_format_enum.create(op.get_bind())
    
    # Create reports table
    op.create_table(
        'reports',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('report_type', report_type_enum, nullable=False),
        sa.Column('config', sa.JSON(), nullable=True),
        sa.Column('status', report_status_enum, nullable=False, default='generating'),
        sa.Column('format', report_format_enum, nullable=False, default='json'),
        sa.Column('file_path', sa.String(length=500), nullable=True),
        sa.Column('is_scheduled', sa.Boolean(), nullable=False, default=False),
        sa.Column('schedule_config', sa.JSON(), nullable=True),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('generated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_reports_id'), 'reports', ['id'], unique=False)
    
    # Create report_templates table
    op.create_table(
        'report_templates',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('report_type', report_type_enum, nullable=False),
        sa.Column('config_template', sa.JSON(), nullable=False),
        sa.Column('is_system_template', sa.Boolean(), nullable=False, default=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('created_by', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['created_by'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_report_templates_id'), 'report_templates', ['id'], unique=False)
    
    # Create report_executions table
    op.create_table(
        'report_executions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('report_id', sa.Integer(), nullable=True),
        sa.Column('report_type', report_type_enum, nullable=False),
        sa.Column('parameters', sa.JSON(), nullable=True),
        sa.Column('status', report_status_enum, nullable=False),
        sa.Column('execution_time_ms', sa.Integer(), nullable=True),
        sa.Column('data_points', sa.Integer(), nullable=True),
        sa.Column('file_size_bytes', sa.Integer(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('started_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['report_id'], ['reports.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_report_executions_id'), 'report_executions', ['id'], unique=False)


def downgrade() -> None:
    # Drop tables
    op.drop_index(op.f('ix_report_executions_id'), table_name='report_executions')
    op.drop_table('report_executions')
    op.drop_index(op.f('ix_report_templates_id'), table_name='report_templates')
    op.drop_table('report_templates')
    op.drop_index(op.f('ix_reports_id'), table_name='reports')
    op.drop_table('reports')
    
    # Drop enums
    op.execute('DROP TYPE IF EXISTS reportformat')
    op.execute('DROP TYPE IF EXISTS reportstatus')
    op.execute('DROP TYPE IF EXISTS reporttype')
