-- 012_add_junior_manager_role.sql
-- Yangi kichik menejer (junior_manager) roli uchun constraint yangilash

ALTER TABLE public.users
  DROP CONSTRAINT IF EXISTS users_role_check;

ALTER TABLE public.users
  ADD CONSTRAINT users_role_check CHECK (
    (role)::text = ANY (
      ARRAY[
        'admin',
        'call_center',
        'technician',
        'manager',
        'controller',
        'warehouse',
        'client',
        'blocked',
        'junior_manager'
      ]::text[]
    )
  ); 