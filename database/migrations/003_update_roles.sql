-- Drop existing role constraint
ALTER TABLE users DROP CONSTRAINT IF EXISTS users_role_check;

-- Add new role constraint with all 8 roles
ALTER TABLE users ADD CONSTRAINT users_role_check 
    CHECK (role IN ('admin', 'call_center', 'technician', 'manager', 'controller', 'warehouse', 'client', 'blocked')); 