"""Migración inicial de esquema PostgreSQL para LeadHunter AI SaaS.

Revision ID: 0001_initial_postgres_schema
Revises: None
Create Date: 2026-11-08 02:25:00.000000

Entidades creadas:
- users
- profiles
- organizations
- organization_members
- searches
- leads
- activities
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# Identificadores de revisión requeridos por Alembic
revision: str = '0001_initial_postgres_schema'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 0. Habilitar extensión pgcrypto para generación nativa de UUIDs
    op.execute('CREATE EXTENSION IF NOT EXISTS "pgcrypto"')

    # 1. Tabla: users
    op.create_table(
        'users',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('password_hash', sa.String(length=255), nullable=False),
        sa.Column('status', sa.String(length=50), server_default='active', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.PrimaryKeyConstraint('id', name='pk_users'),
        sa.UniqueConstraint('email', name='uq_users_email'),
        sa.CheckConstraint('email = LOWER(email)', name='chk_users_email_lowercase')
    )

    # 2. Tabla: profiles
    op.create_table(
        'profiles',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('full_name', sa.String(length=150), nullable=False),
        sa.Column('avatar_url', sa.String(length=500), nullable=True),
        sa.Column('phone', sa.String(length=50), nullable=True),
        sa.Column('preferences', postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'{}'::jsonb"), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], name='fk_profiles_user_id', ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id', name='pk_profiles'),
        sa.UniqueConstraint('user_id', name='uq_profiles_user_id')
    )

    # 3. Tabla: organizations
    op.create_table(
        'organizations',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('name', sa.String(length=150), nullable=False),
        sa.Column('slug', sa.String(length=180), nullable=False),
        sa.Column('plan_id', sa.String(length=50), server_default='starter', nullable=False),
        sa.Column('commercial_profile', sa.Text(), server_default='', nullable=True),
        sa.Column('target_country', sa.String(length=100), server_default='', nullable=True),
        sa.Column('target_city', sa.String(length=100), server_default='', nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.PrimaryKeyConstraint('id', name='pk_organizations'),
        sa.UniqueConstraint('slug', name='uq_organizations_slug')
    )

    # 4. Tabla: organization_members
    op.create_table(
        'organization_members',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('role', sa.String(length=50), server_default='member', nullable=False),
        sa.Column('joined_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], name='fk_org_members_org_id', ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], name='fk_org_members_user_id', ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id', name='pk_organization_members'),
        sa.UniqueConstraint('organization_id', 'user_id', name='uq_org_member')
    )

    # 5. Tabla: searches
    op.create_table(
        'searches',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_by_user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('query_prompt', sa.Text(), nullable=False),
        sa.Column('sector', sa.String(length=100), nullable=False),
        sa.Column('city', sa.String(length=100), nullable=False),
        sa.Column('country', sa.String(length=100), server_default='República Dominicana', nullable=False),
        sa.Column('sources', sa.String(length=255), server_default='OpenStreetMap,DuckDuckGo', nullable=False),
        sa.Column('total_found', sa.Integer(), server_default='0', nullable=False),
        sa.Column('new_leads_count', sa.Integer(), server_default='0', nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['created_by_user_id'], ['users.id'], name='fk_searches_created_by_user_id', ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], name='fk_searches_organization_id', ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id', name='pk_searches')
    )

    # 6. Tabla: leads
    op.create_table(
        'leads',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('search_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('dedupe_key', sa.String(length=255), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False),
        sa.Column('website', sa.String(length=500), server_default='', nullable=True),
        sa.Column('phone', sa.String(length=100), server_default='', nullable=True),
        sa.Column('email', sa.String(length=255), server_default='', nullable=True),
        sa.Column('instagram', sa.String(length=255), server_default='', nullable=True),
        sa.Column('country', sa.String(length=100), server_default='', nullable=True),
        sa.Column('city', sa.String(length=100), server_default='', nullable=True),
        sa.Column('sector', sa.String(length=100), server_default='', nullable=True),
        sa.Column('address', sa.Text(), server_default='', nullable=True),
        sa.Column('score', sa.SmallInteger(), server_default='0', nullable=False),
        sa.Column('score_detail', postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'{}'::jsonb"), nullable=False),
        sa.Column('evidence', postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'[]'::jsonb"), nullable=False),
        sa.Column('inferences', postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'[]'::jsonb"), nullable=False),
        sa.Column('status', sa.String(length=50), server_default='Nuevo', nullable=False),
        sa.Column('notes', sa.Text(), server_default='', nullable=False),
        sa.Column('next_followup', sa.Date(), nullable=True),
        sa.Column('analyzed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.CheckConstraint('score >= 0 AND score <= 100', name='chk_leads_score_range'),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], name='fk_leads_organization_id', ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['search_id'], ['searches.id'], name='fk_leads_search_id', ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id', name='pk_leads'),
        sa.UniqueConstraint('organization_id', 'dedupe_key', name='uq_leads_organization_dedupe')
    )

    # 7. Tabla: activities
    op.create_table(
        'activities',
        sa.Column('id', postgresql.UUID(as_uuid=True), server_default=sa.text('gen_random_uuid()'), nullable=False),
        sa.Column('organization_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('lead_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('activity_type', sa.String(length=50), nullable=False),
        sa.Column('description', sa.Text(), nullable=False),
        sa.Column('metadata', postgresql.JSONB(astext_type=sa.Text()), server_default=sa.text("'{}'::jsonb"), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.ForeignKeyConstraint(['lead_id'], ['leads.id'], name='fk_activities_lead_id', ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], name='fk_activities_organization_id', ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], name='fk_activities_user_id', ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id', name='pk_activities')
    )

    # 8. Índices de Rendimiento
    op.create_index(
        'idx_leads_org_score_created',
        'leads',
        ['organization_id', sa.text('score DESC'), sa.text('created_at DESC')]
    )
    op.create_index('idx_leads_org_status', 'leads', ['organization_id', 'status'])
    op.create_index('idx_leads_org_sector_city', 'leads', ['organization_id', 'sector', 'city'])
    op.create_index(
        'idx_leads_org_email',
        'leads',
        ['organization_id', 'email'],
        postgresql_where=sa.text("email != ''")
    )
    op.create_index(
        'idx_leads_org_phone',
        'leads',
        ['organization_id', 'phone'],
        postgresql_where=sa.text("phone != ''")
    )
    op.create_index(
        'idx_activities_lead_created',
        'activities',
        ['lead_id', sa.text('created_at DESC')]
    )
    op.create_index(
        'idx_searches_org_created',
        'searches',
        ['organization_id', sa.text('created_at DESC')]
    )


def downgrade() -> None:
    # 1. Eliminación de índices de rendimiento
    op.drop_index('idx_searches_org_created', table_name='searches')
    op.drop_index('idx_activities_lead_created', table_name='activities')
    op.drop_index('idx_leads_org_phone', table_name='leads')
    op.drop_index('idx_leads_org_email', table_name='leads')
    op.drop_index('idx_leads_org_sector_city', table_name='leads')
    op.drop_index('idx_leads_org_status', table_name='leads')
    op.drop_index('idx_leads_org_score_created', table_name='leads')

    # 2. Eliminación de tablas en orden inverso respetando integridad referencial (FKs)
    op.drop_table('activities')
    op.drop_table('leads')
    op.drop_table('searches')
    op.drop_table('organization_members')
    op.drop_table('organizations')
    op.drop_table('profiles')
    op.drop_table('users')

    # 3. Eliminación de extensión si se requiere limpieza total
    op.execute('DROP EXTENSION IF EXISTS "pgcrypto"')
