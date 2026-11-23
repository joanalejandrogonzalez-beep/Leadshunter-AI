-- ============================================================================
-- SUPABASE / POSTGRESQL MIGRATION: UP (Creación de esquema inicial)
-- Archivo: 20261108000001_initial_schema.sql
-- ============================================================================

CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- 1. users
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR(255) NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'active',
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_users_email UNIQUE (email),
    CONSTRAINT chk_users_email_lowercase CHECK (email = LOWER(email))
);

-- 2. profiles
CREATE TABLE IF NOT EXISTS profiles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL,
    full_name VARCHAR(150) NOT NULL,
    avatar_url VARCHAR(500),
    phone VARCHAR(50),
    preferences JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_profiles_user_id UNIQUE (user_id),
    CONSTRAINT fk_profiles_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- 3. organizations
CREATE TABLE IF NOT EXISTS organizations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(150) NOT NULL,
    slug VARCHAR(180) NOT NULL,
    plan_id VARCHAR(50) NOT NULL DEFAULT 'starter',
    commercial_profile TEXT DEFAULT '',
    target_country VARCHAR(100) DEFAULT '',
    target_city VARCHAR(100) DEFAULT '',
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_organizations_slug UNIQUE (slug)
);

-- 4. organization_members
CREATE TABLE IF NOT EXISTS organization_members (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL,
    user_id UUID NOT NULL,
    role VARCHAR(50) NOT NULL DEFAULT 'member',
    joined_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_org_member UNIQUE (organization_id, user_id),
    CONSTRAINT fk_org_members_org FOREIGN KEY (organization_id) REFERENCES organizations(id) ON DELETE CASCADE,
    CONSTRAINT fk_org_members_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
);

-- 5. searches
CREATE TABLE IF NOT EXISTS searches (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL,
    created_by_user_id UUID,
    query_prompt TEXT NOT NULL,
    sector VARCHAR(100) NOT NULL,
    city VARCHAR(100) NOT NULL,
    country VARCHAR(100) NOT NULL DEFAULT 'República Dominicana',
    sources VARCHAR(255) NOT NULL DEFAULT 'OpenStreetMap,DuckDuckGo',
    total_found INTEGER NOT NULL DEFAULT 0,
    new_leads_count INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_searches_organization FOREIGN KEY (organization_id) REFERENCES organizations(id) ON DELETE CASCADE,
    CONSTRAINT fk_searches_user FOREIGN KEY (created_by_user_id) REFERENCES users(id) ON DELETE SET NULL
);

-- 6. leads
CREATE TABLE IF NOT EXISTS leads (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL,
    search_id UUID,
    dedupe_key VARCHAR(255) NOT NULL,
    name VARCHAR(255) NOT NULL,
    website VARCHAR(500) DEFAULT '',
    phone VARCHAR(100) DEFAULT '',
    email VARCHAR(255) DEFAULT '',
    instagram VARCHAR(255) DEFAULT '',
    country VARCHAR(100) DEFAULT '',
    city VARCHAR(100) DEFAULT '',
    sector VARCHAR(100) DEFAULT '',
    address TEXT DEFAULT '',
    score SMALLINT NOT NULL DEFAULT 0,
    score_detail JSONB NOT NULL DEFAULT '{}'::jsonb,
    evidence JSONB NOT NULL DEFAULT '[]'::jsonb,
    inferences JSONB NOT NULL DEFAULT '[]'::jsonb,
    status VARCHAR(50) NOT NULL DEFAULT 'Nuevo',
    notes TEXT NOT NULL DEFAULT '',
    next_followup DATE,
    analyzed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT uq_leads_organization_dedupe UNIQUE (organization_id, dedupe_key),
    CONSTRAINT chk_leads_score_range CHECK (score >= 0 AND score <= 100),
    CONSTRAINT fk_leads_organization FOREIGN KEY (organization_id) REFERENCES organizations(id) ON DELETE CASCADE,
    CONSTRAINT fk_leads_search FOREIGN KEY (search_id) REFERENCES searches(id) ON DELETE SET NULL
);

-- 7. activities
CREATE TABLE IF NOT EXISTS activities (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    organization_id UUID NOT NULL,
    lead_id UUID NOT NULL,
    user_id UUID,
    activity_type VARCHAR(50) NOT NULL,
    description TEXT NOT NULL,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_activities_org FOREIGN KEY (organization_id) REFERENCES organizations(id) ON DELETE CASCADE,
    CONSTRAINT fk_activities_lead FOREIGN KEY (lead_id) REFERENCES leads(id) ON DELETE CASCADE,
    CONSTRAINT fk_activities_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
);

-- 8. Índices de Rendimiento
CREATE INDEX IF NOT EXISTS idx_leads_org_score_created ON leads (organization_id, score DESC, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_leads_org_status ON leads (organization_id, status);
CREATE INDEX IF NOT EXISTS idx_leads_org_sector_city ON leads (organization_id, sector, city);
CREATE INDEX IF NOT EXISTS idx_leads_org_email ON leads (organization_id, email) WHERE email != '';
CREATE INDEX IF NOT EXISTS idx_leads_org_phone ON leads (organization_id, phone) WHERE phone != '';
CREATE INDEX IF NOT EXISTS idx_activities_lead_created ON activities (lead_id, created_at DESC);
CREATE INDEX IF NOT EXISTS idx_searches_org_created ON searches (organization_id, created_at DESC);
