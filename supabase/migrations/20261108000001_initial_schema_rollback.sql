-- ============================================================================
-- SUPABASE / POSTGRESQL MIGRATION: DOWN (Reversión limpia del esquema inicial)
-- Archivo: 20261108000001_initial_schema_rollback.sql
-- ============================================================================

-- 1. Eliminar índices
DROP INDEX IF EXISTS idx_searches_org_created;
DROP INDEX IF EXISTS idx_activities_lead_created;
DROP INDEX IF EXISTS idx_leads_org_phone;
DROP INDEX IF EXISTS idx_leads_org_email;
DROP INDEX IF EXISTS idx_leads_org_sector_city;
DROP INDEX IF EXISTS idx_leads_org_status;
DROP INDEX IF EXISTS idx_leads_org_score_created;

-- 2. Eliminar tablas en orden inverso respetando foreign keys
DROP TABLE IF EXISTS activities CASCADE;
DROP TABLE IF EXISTS leads CASCADE;
DROP TABLE IF EXISTS searches CASCADE;
DROP TABLE IF EXISTS organization_members CASCADE;
DROP TABLE IF EXISTS organizations CASCADE;
DROP TABLE IF EXISTS profiles CASCADE;
DROP TABLE IF EXISTS users CASCADE;

-- 3. Eliminar extensión si no se utiliza por otros servicios
-- DROP EXTENSION IF EXISTS "pgcrypto";
