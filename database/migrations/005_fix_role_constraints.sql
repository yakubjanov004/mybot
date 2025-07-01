-- Fix role constraints to match the current schema
-- This migration ensures all role references are consistent

-- Drop existing role constraint
ALTER TABLE users DROP CONSTRAINT IF EXISTS users_role_check;

-- Add correct role constraint with all 8 roles
ALTER TABLE users ADD CONSTRAINT users_role_check 
    CHECK (role IN ('admin', 'call_center', 'technician', 'manager', 'controller', 'warehouse', 'client', 'blocked'));

-- Update any existing 'operator' roles to 'call_center'
UPDATE users SET role = 'call_center' WHERE role = 'operator';

-- Update any other incorrect role names
UPDATE users SET role = 'controller' WHERE role = 'kontroler';
UPDATE users SET role = 'warehouse' WHERE role = 'sklad';
UPDATE users SET role = 'call_center' WHERE role = 'callcenter';

-- Add index for better performance on role queries
CREATE INDEX IF NOT EXISTS idx_users_role_updated ON users(role); 