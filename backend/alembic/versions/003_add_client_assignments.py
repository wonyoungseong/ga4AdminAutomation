"""Add client assignments system

Revision ID: 003
Revises: 002
Create Date: 2024-08-04 05:30:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = '003'
down_revision = '002'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add client assignments and related tables"""
    
    # Create client_assignment_status enum
    client_assignment_status = postgresql.ENUM(
        'active', 'inactive', 'suspended',
        name='clientassignmentstatus',
        create_type=False
    )
    client_assignment_status.create(op.get_bind(), checkfirst=True)
    
    # Create client_assignments table
    op.create_table('client_assignments',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('client_id', sa.Integer(), nullable=False),
        sa.Column('assigned_by_id', sa.Integer(), nullable=False),
        sa.Column('status', client_assignment_status, nullable=False, default='active'),
        sa.Column('assigned_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['assigned_by_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['client_id'], ['clients.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for efficient lookups
    op.create_index('ix_client_assignments_user_id', 'client_assignments', ['user_id'])
    op.create_index('ix_client_assignments_client_id', 'client_assignments', ['client_id'])
    op.create_index('ix_client_assignments_status', 'client_assignments', ['status'])
    op.create_index('ix_client_assignments_assigned_at', 'client_assignments', ['assigned_at'])
    
    # Create unique constraint to prevent duplicate active assignments
    op.create_index(
        'ix_client_assignments_unique_active',
        'client_assignments',
        ['user_id', 'client_id'],
        unique=True,
        postgresql_where=sa.text("status = 'active'")
    )
    
    # Add client_assignment_id column to audit_logs table
    op.add_column('audit_logs', sa.Column('client_assignment_id', sa.Integer(), nullable=True))
    op.create_foreign_key(
        'fk_audit_logs_client_assignment_id',
        'audit_logs', 'client_assignments',
        ['client_assignment_id'], ['id']
    )
    
    # Create trigger to update updated_at timestamp
    op.execute("""
        CREATE OR REPLACE FUNCTION update_updated_at_column()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = now();
            RETURN NEW;
        END;
        $$ language 'plpgsql';
    """)
    
    op.execute("""
        CREATE TRIGGER update_client_assignments_updated_at
        BEFORE UPDATE ON client_assignments
        FOR EACH ROW
        EXECUTE FUNCTION update_updated_at_column();
    """)


def downgrade() -> None:
    """Remove client assignments system"""
    
    # Drop trigger
    op.execute('DROP TRIGGER IF EXISTS update_client_assignments_updated_at ON client_assignments')
    op.execute('DROP FUNCTION IF EXISTS update_updated_at_column()')
    
    # Remove foreign key from audit_logs
    op.drop_constraint('fk_audit_logs_client_assignment_id', 'audit_logs', type_='foreignkey')
    op.drop_column('audit_logs', 'client_assignment_id')
    
    # Drop indexes
    op.drop_index('ix_client_assignments_unique_active', 'client_assignments')
    op.drop_index('ix_client_assignments_assigned_at', 'client_assignments')
    op.drop_index('ix_client_assignments_status', 'client_assignments')
    op.drop_index('ix_client_assignments_client_id', 'client_assignments')
    op.drop_index('ix_client_assignments_user_id', 'client_assignments')
    
    # Drop client_assignments table
    op.drop_table('client_assignments')
    
    # Drop enum
    sa.Enum(name='clientassignmentstatus').drop(op.get_bind(), checkfirst=True)