-- 015_update_workflow.sql
-- Update workflow with new roles and statuses

-- 1. Add 'call_center_supervisor' role to users table
ALTER TABLE users
DROP CONSTRAINT IF EXISTS users_role_check,
ADD CONSTRAINT users_role_check CHECK (role IN (
    'admin',
    'call_center',
    'call_center_supervisor',
    'technician',
    'manager',
    'junior_manager',
    'controller',
    'warehouse',
    'client',
    'blocked'
));

-- 2. Update zayavki statuses
-- No schema change needed for statuses as they are handled in the application logic,
-- but this file is created to keep track of the workflow changes.

-- END OF MIGRATION