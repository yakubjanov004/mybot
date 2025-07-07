--
-- PostgreSQL database dump
--

-- Dumped from database version 17.5
-- Dumped by pg_dump version 17.5

SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET transaction_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;

--
-- Name: update_updated_at_column(); Type: FUNCTION; Schema: public; Owner: postgres
--

CREATE FUNCTION public.update_updated_at_column() RETURNS trigger
    LANGUAGE plpgsql
    AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$;


ALTER FUNCTION public.update_updated_at_column() OWNER TO postgres;

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: admin_action_logs; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.admin_action_logs (
    id integer NOT NULL,
    admin_id bigint NOT NULL,
    action character varying(100) NOT NULL,
    details jsonb,
    performed_at timestamp without time zone DEFAULT now()
);


ALTER TABLE public.admin_action_logs OWNER TO postgres;

--
-- Name: admin_action_logs_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.admin_action_logs_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.admin_action_logs_id_seq OWNER TO postgres;

--
-- Name: admin_action_logs_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.admin_action_logs_id_seq OWNED BY public.admin_action_logs.id;


--
-- Name: call_logs; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.call_logs (
    id integer NOT NULL,
    user_id integer,
    phone_number text NOT NULL,
    duration integer DEFAULT 0 NOT NULL,
    result character varying(50) NOT NULL,
    notes text,
    created_by integer,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT call_logs_duration_check CHECK ((duration >= 0))
);


ALTER TABLE public.call_logs OWNER TO postgres;

--
-- Name: call_logs_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.call_logs_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.call_logs_id_seq OWNER TO postgres;

--
-- Name: call_logs_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.call_logs_id_seq OWNED BY public.call_logs.id;


--
-- Name: chat_messages; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.chat_messages (
    id integer NOT NULL,
    session_id integer NOT NULL,
    sender_id integer NOT NULL,
    message_text text NOT NULL,
    message_type character varying(20) DEFAULT 'text'::character varying NOT NULL,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chat_messages_message_type_check CHECK (((message_type)::text = ANY ((ARRAY['text'::character varying, 'image'::character varying, 'document'::character varying, 'location'::character varying, 'contact'::character varying])::text[])))
);


ALTER TABLE public.chat_messages OWNER TO postgres;

--
-- Name: chat_messages_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.chat_messages_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.chat_messages_id_seq OWNER TO postgres;

--
-- Name: chat_messages_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.chat_messages_id_seq OWNED BY public.chat_messages.id;


--
-- Name: chat_sessions; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.chat_sessions (
    id integer NOT NULL,
    user_id integer NOT NULL,
    operator_id integer NOT NULL,
    status character varying(20) DEFAULT 'active'::character varying NOT NULL,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    closed_at timestamp with time zone,
    CONSTRAINT chat_sessions_status_check CHECK (((status)::text = ANY ((ARRAY['active'::character varying, 'closed'::character varying, 'transferred'::character varying])::text[])))
);


ALTER TABLE public.chat_sessions OWNER TO postgres;

--
-- Name: chat_sessions_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.chat_sessions_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.chat_sessions_id_seq OWNER TO postgres;

--
-- Name: chat_sessions_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.chat_sessions_id_seq OWNED BY public.chat_sessions.id;


--
-- Name: equipment_requests; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.equipment_requests (
    id integer NOT NULL,
    technician_id integer NOT NULL,
    equipment_type character varying(100) NOT NULL,
    quantity integer NOT NULL,
    reason text NOT NULL,
    status character varying(20) DEFAULT 'pending'::character varying NOT NULL,
    approved_by integer,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT equipment_requests_quantity_check CHECK ((quantity > 0)),
    CONSTRAINT equipment_requests_status_check CHECK (((status)::text = ANY ((ARRAY['pending'::character varying, 'approved'::character varying, 'issued'::character varying, 'rejected'::character varying])::text[])))
);


ALTER TABLE public.equipment_requests OWNER TO postgres;

--
-- Name: equipment_requests_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.equipment_requests_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.equipment_requests_id_seq OWNER TO postgres;

--
-- Name: equipment_requests_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.equipment_requests_id_seq OWNED BY public.equipment_requests.id;


--
-- Name: feedback; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.feedback (
    id integer NOT NULL,
    zayavka_id integer,
    user_id integer NOT NULL,
    rating integer NOT NULL,
    comment text,
    created_by integer,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT feedback_rating_check CHECK (((rating >= 1) AND (rating <= 5)))
);


ALTER TABLE public.feedback OWNER TO postgres;

--
-- Name: feedback_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.feedback_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.feedback_id_seq OWNER TO postgres;

--
-- Name: feedback_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.feedback_id_seq OWNED BY public.feedback.id;


--
-- Name: help_requests; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.help_requests (
    id integer NOT NULL,
    technician_id integer NOT NULL,
    help_type character varying(50) NOT NULL,
    description text NOT NULL,
    status character varying(20) DEFAULT 'pending'::character varying NOT NULL,
    priority character varying(10) DEFAULT 'medium'::character varying NOT NULL,
    assigned_to integer,
    resolution text,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    resolved_at timestamp with time zone,
    CONSTRAINT help_requests_priority_check CHECK (((priority)::text = ANY ((ARRAY['low'::character varying, 'medium'::character varying, 'high'::character varying, 'urgent'::character varying])::text[]))),
    CONSTRAINT help_requests_status_check CHECK (((status)::text = ANY ((ARRAY['pending'::character varying, 'assigned'::character varying, 'in_progress'::character varying, 'resolved'::character varying, 'cancelled'::character varying])::text[])))
);


ALTER TABLE public.help_requests OWNER TO postgres;

--
-- Name: help_requests_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.help_requests_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.help_requests_id_seq OWNER TO postgres;

--
-- Name: help_requests_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.help_requests_id_seq OWNED BY public.help_requests.id;


--
-- Name: issued_items; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.issued_items (
    id integer NOT NULL,
    zayavka_id integer,
    material_id integer NOT NULL,
    quantity integer NOT NULL,
    issued_by integer NOT NULL,
    issued_to integer,
    issued_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT issued_items_quantity_check CHECK ((quantity > 0))
);


ALTER TABLE public.issued_items OWNER TO postgres;

--
-- Name: issued_items_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.issued_items_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.issued_items_id_seq OWNER TO postgres;

--
-- Name: issued_items_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.issued_items_id_seq OWNED BY public.issued_items.id;


--
-- Name: login_logs; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.login_logs (
    id integer NOT NULL,
    user_id bigint,
    ip_address text,
    user_agent text,
    logged_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.login_logs OWNER TO postgres;

--
-- Name: login_logs_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.login_logs_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.login_logs_id_seq OWNER TO postgres;

--
-- Name: login_logs_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.login_logs_id_seq OWNED BY public.login_logs.id;


--
-- Name: material_receipts; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.material_receipts (
    id integer NOT NULL,
    material_id integer NOT NULL,
    quantity integer NOT NULL,
    received_by integer NOT NULL,
    supplier text,
    notes text,
    received_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT material_receipts_quantity_check CHECK ((quantity > 0))
);


ALTER TABLE public.material_receipts OWNER TO postgres;

--
-- Name: material_receipts_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.material_receipts_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.material_receipts_id_seq OWNER TO postgres;

--
-- Name: material_receipts_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.material_receipts_id_seq OWNED BY public.material_receipts.id;


--
-- Name: materials; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.materials (
    id integer NOT NULL,
    name text NOT NULL,
    category text DEFAULT 'general'::text,
    quantity integer DEFAULT 0 NOT NULL,
    unit character varying(10) DEFAULT 'pcs'::character varying NOT NULL,
    min_quantity integer DEFAULT 5 NOT NULL,
    price numeric(10,2) DEFAULT 0.00 NOT NULL,
    description text,
    supplier text,
    is_active boolean DEFAULT true NOT NULL,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT materials_min_quantity_check CHECK ((min_quantity >= 0)),
    CONSTRAINT materials_price_check CHECK ((price >= (0)::numeric)),
    CONSTRAINT materials_quantity_check CHECK ((quantity >= 0))
);


ALTER TABLE public.materials OWNER TO postgres;

--
-- Name: materials_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.materials_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.materials_id_seq OWNER TO postgres;

--
-- Name: materials_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.materials_id_seq OWNED BY public.materials.id;


--
-- Name: notification_queue; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.notification_queue (
    id integer NOT NULL,
    user_id integer,
    message text NOT NULL,
    zayavka_id integer,
    notification_type character varying(50),
    sent boolean DEFAULT false,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.notification_queue OWNER TO postgres;

--
-- Name: notification_queue_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.notification_queue_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.notification_queue_id_seq OWNER TO postgres;

--
-- Name: notification_queue_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.notification_queue_id_seq OWNED BY public.notification_queue.id;


--
-- Name: notification_templates; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.notification_templates (
    id integer NOT NULL,
    template_type character varying(50) NOT NULL,
    language character varying(2) NOT NULL,
    content text NOT NULL,
    updated_by integer,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT notification_templates_language_check CHECK (((language)::text = ANY ((ARRAY['uz'::character varying, 'ru'::character varying])::text[])))
);


ALTER TABLE public.notification_templates OWNER TO postgres;

--
-- Name: notification_templates_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.notification_templates_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.notification_templates_id_seq OWNER TO postgres;

--
-- Name: notification_templates_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.notification_templates_id_seq OWNED BY public.notification_templates.id;


--
-- Name: notifications; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.notifications (
    id integer NOT NULL,
    user_id bigint,
    zayavka_id integer,
    message text,
    sent_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    channel character varying(10),
    CONSTRAINT notifications_channel_check CHECK (((channel)::text = ANY (ARRAY[('telegram'::character varying)::text, ('email'::character varying)::text])))
);


ALTER TABLE public.notifications OWNER TO postgres;

--
-- Name: notifications_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.notifications_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.notifications_id_seq OWNER TO postgres;

--
-- Name: notifications_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.notifications_id_seq OWNED BY public.notifications.id;


--
-- Name: solutions; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.solutions (
    id integer NOT NULL,
    zayavka_id integer NOT NULL,
    instander_id integer NOT NULL,
    solution_text text NOT NULL,
    media text,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.solutions OWNER TO postgres;

--
-- Name: solutions_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.solutions_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.solutions_id_seq OWNER TO postgres;

--
-- Name: solutions_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.solutions_id_seq OWNED BY public.solutions.id;


--
-- Name: status_logs; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.status_logs (
    id integer NOT NULL,
    zayavka_id integer NOT NULL,
    old_status character varying(20) NOT NULL,
    new_status character varying(20) NOT NULL,
    changed_by integer NOT NULL,
    changed_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.status_logs OWNER TO postgres;

--
-- Name: status_logs_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.status_logs_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.status_logs_id_seq OWNER TO postgres;

--
-- Name: status_logs_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.status_logs_id_seq OWNED BY public.status_logs.id;


--
-- Name: system_settings; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.system_settings (
    id integer NOT NULL,
    setting_key character varying(100) NOT NULL,
    setting_value text NOT NULL,
    description text,
    updated_by integer,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.system_settings OWNER TO postgres;

--
-- Name: system_settings_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.system_settings_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.system_settings_id_seq OWNER TO postgres;

--
-- Name: system_settings_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.system_settings_id_seq OWNED BY public.system_settings.id;


--
-- Name: technician_locations; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.technician_locations (
    technician_id integer NOT NULL,
    latitude numeric(10,8) NOT NULL,
    longitude numeric(11,8) NOT NULL,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.technician_locations OWNER TO postgres;

--
-- Name: technician_performance; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.technician_performance (
    id integer NOT NULL,
    technician_id bigint,
    completed_tasks integer DEFAULT 0,
    average_completion_time numeric(5,2),
    rating numeric(3,2) DEFAULT 5.0,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.technician_performance OWNER TO postgres;

--
-- Name: technician_performance_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.technician_performance_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.technician_performance_id_seq OWNER TO postgres;

--
-- Name: technician_performance_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.technician_performance_id_seq OWNED BY public.technician_performance.id;


--
-- Name: technician_workload; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.technician_workload (
    id integer NOT NULL,
    technician_id bigint,
    active_tasks integer DEFAULT 0,
    max_tasks integer DEFAULT 5,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.technician_workload OWNER TO postgres;

--
-- Name: technician_workload_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.technician_workload_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.technician_workload_id_seq OWNER TO postgres;

--
-- Name: technician_workload_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.technician_workload_id_seq OWNED BY public.technician_workload.id;


--
-- Name: users; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.users (
    id integer NOT NULL,
    telegram_id bigint NOT NULL,
    full_name text,
    username text,
    phone_number text,
    role character varying(20) DEFAULT 'client'::character varying NOT NULL,
    abonent_id character varying(50),
    language character varying(2) DEFAULT 'uz'::character varying NOT NULL,
    is_active boolean DEFAULT true NOT NULL,
    address text,
    permissions jsonb,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT users_language_check CHECK (((language)::text = ANY ((ARRAY['uz'::character varying, 'ru'::character varying])::text[]))),
    CONSTRAINT users_role_check CHECK (((role)::text = ANY ((ARRAY['admin'::character varying, 'call_center'::character varying, 'technician'::character varying, 'manager'::character varying, 'controller'::character varying, 'warehouse'::character varying, 'client'::character varying, 'blocked'::character varying])::text[])))
);


ALTER TABLE public.users OWNER TO postgres;

--
-- Name: users_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.users_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.users_id_seq OWNER TO postgres;

--
-- Name: users_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.users_id_seq OWNED BY public.users.id;


--
-- Name: zayavka_transfers; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.zayavka_transfers (
    id integer NOT NULL,
    zayavka_id integer,
    from_technician_id bigint,
    to_technician_id bigint,
    transferred_by bigint,
    reason text,
    transferred_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.zayavka_transfers OWNER TO postgres;

--
-- Name: zayavka_transfers_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.zayavka_transfers_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.zayavka_transfers_id_seq OWNER TO postgres;

--
-- Name: zayavka_transfers_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.zayavka_transfers_id_seq OWNED BY public.zayavka_transfers.id;


--
-- Name: zayavki; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.zayavki (
    id integer NOT NULL,
    user_id integer NOT NULL,
    description text NOT NULL,
    media text,
    status character varying(20) DEFAULT 'new'::character varying NOT NULL,
    address text,
    latitude numeric(10,8),
    longitude numeric(11,8),
    assigned_to integer,
    zayavka_type character varying(20),
    abonent_id character varying(50),
    phone_number text,
    priority integer DEFAULT 1 NOT NULL,
    estimated_time integer,
    actual_time integer,
    completion_notes text,
    created_by_role character varying(20),
    created_by integer,
    ready_to_install boolean DEFAULT false NOT NULL,
    assigned_at timestamp with time zone,
    completed_at timestamp with time zone,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT zayavki_priority_check CHECK (((priority >= 1) AND (priority <= 5))),
    CONSTRAINT zayavki_status_check CHECK (((status)::text = ANY ((ARRAY['new'::character varying, 'pending'::character varying, 'assigned'::character varying, 'in_progress'::character varying, 'completed'::character varying, 'cancelled'::character varying, 'transferred'::character varying])::text[])))
);


ALTER TABLE public.zayavki OWNER TO postgres;

--
-- Name: zayavki_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.zayavki_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.zayavki_id_seq OWNER TO postgres;

--
-- Name: zayavki_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.zayavki_id_seq OWNED BY public.zayavki.id;


--
-- Name: admin_action_logs id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.admin_action_logs ALTER COLUMN id SET DEFAULT nextval('public.admin_action_logs_id_seq'::regclass);


--
-- Name: call_logs id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.call_logs ALTER COLUMN id SET DEFAULT nextval('public.call_logs_id_seq'::regclass);


--
-- Name: chat_messages id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.chat_messages ALTER COLUMN id SET DEFAULT nextval('public.chat_messages_id_seq'::regclass);


--
-- Name: chat_sessions id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.chat_sessions ALTER COLUMN id SET DEFAULT nextval('public.chat_sessions_id_seq'::regclass);


--
-- Name: equipment_requests id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.equipment_requests ALTER COLUMN id SET DEFAULT nextval('public.equipment_requests_id_seq'::regclass);


--
-- Name: feedback id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.feedback ALTER COLUMN id SET DEFAULT nextval('public.feedback_id_seq'::regclass);


--
-- Name: help_requests id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.help_requests ALTER COLUMN id SET DEFAULT nextval('public.help_requests_id_seq'::regclass);


--
-- Name: issued_items id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.issued_items ALTER COLUMN id SET DEFAULT nextval('public.issued_items_id_seq'::regclass);


--
-- Name: login_logs id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.login_logs ALTER COLUMN id SET DEFAULT nextval('public.login_logs_id_seq'::regclass);


--
-- Name: material_receipts id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.material_receipts ALTER COLUMN id SET DEFAULT nextval('public.material_receipts_id_seq'::regclass);


--
-- Name: materials id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.materials ALTER COLUMN id SET DEFAULT nextval('public.materials_id_seq'::regclass);


--
-- Name: notification_queue id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.notification_queue ALTER COLUMN id SET DEFAULT nextval('public.notification_queue_id_seq'::regclass);


--
-- Name: notification_templates id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.notification_templates ALTER COLUMN id SET DEFAULT nextval('public.notification_templates_id_seq'::regclass);


--
-- Name: notifications id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.notifications ALTER COLUMN id SET DEFAULT nextval('public.notifications_id_seq'::regclass);


--
-- Name: solutions id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.solutions ALTER COLUMN id SET DEFAULT nextval('public.solutions_id_seq'::regclass);


--
-- Name: status_logs id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.status_logs ALTER COLUMN id SET DEFAULT nextval('public.status_logs_id_seq'::regclass);


--
-- Name: system_settings id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.system_settings ALTER COLUMN id SET DEFAULT nextval('public.system_settings_id_seq'::regclass);


--
-- Name: technician_performance id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.technician_performance ALTER COLUMN id SET DEFAULT nextval('public.technician_performance_id_seq'::regclass);


--
-- Name: technician_workload id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.technician_workload ALTER COLUMN id SET DEFAULT nextval('public.technician_workload_id_seq'::regclass);


--
-- Name: users id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.users ALTER COLUMN id SET DEFAULT nextval('public.users_id_seq'::regclass);


--
-- Name: zayavka_transfers id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.zayavka_transfers ALTER COLUMN id SET DEFAULT nextval('public.zayavka_transfers_id_seq'::regclass);


--
-- Name: zayavki id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.zayavki ALTER COLUMN id SET DEFAULT nextval('public.zayavki_id_seq'::regclass);


--
-- Data for Name: admin_action_logs; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.admin_action_logs (id, admin_id, action, details, performed_at) FROM stdin;
1	1978574076	admin_login	\N	2025-07-04 17:36:07.488688
\.


--
-- Data for Name: call_logs; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.call_logs (id, user_id, phone_number, duration, result, notes, created_by, created_at) FROM stdin;
\.


--
-- Data for Name: chat_messages; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.chat_messages (id, session_id, sender_id, message_text, message_type, created_at) FROM stdin;
\.


--
-- Data for Name: chat_sessions; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.chat_sessions (id, user_id, operator_id, status, created_at, closed_at) FROM stdin;
\.


--
-- Data for Name: equipment_requests; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.equipment_requests (id, technician_id, equipment_type, quantity, reason, status, approved_by, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: feedback; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.feedback (id, zayavka_id, user_id, rating, comment, created_by, created_at) FROM stdin;
\.


--
-- Data for Name: help_requests; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.help_requests (id, technician_id, help_type, description, status, priority, assigned_to, resolution, created_at, updated_at, resolved_at) FROM stdin;
\.


--
-- Data for Name: issued_items; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.issued_items (id, zayavka_id, material_id, quantity, issued_by, issued_to, issued_at) FROM stdin;
\.


--
-- Data for Name: login_logs; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.login_logs (id, user_id, ip_address, user_agent, logged_at) FROM stdin;
\.


--
-- Data for Name: material_receipts; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.material_receipts (id, material_id, quantity, received_by, supplier, notes, received_at) FROM stdin;
\.


--
-- Data for Name: materials; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.materials (id, name, category, quantity, unit, min_quantity, price, description, supplier, is_active, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: notification_queue; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.notification_queue (id, user_id, message, zayavka_id, notification_type, sent, created_at) FROM stdin;
\.


--
-- Data for Name: notification_templates; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.notification_templates (id, template_type, language, content, updated_by, updated_at) FROM stdin;
1	zayavka_created	uz	Sizning zayavkangiz #{id} yaratildi va ko'rib chiqilmoqda.	\N	2025-07-03 15:13:40.531525+05
2	zayavka_created	ru	Р’Р°С€Р° Р·Р°СЏРІРєР° #{id} СЃРѕР·РґР°РЅР° Рё СЂР°СЃСЃРјР°С‚СЂРёРІР°РµС‚СЃСЏ.	\N	2025-07-03 15:13:40.531525+05
3	zayavka_assigned	uz	Sizning zayavkangiz #{id} texnikka tayinlandi.	\N	2025-07-03 15:13:40.531525+05
4	zayavka_assigned	ru	Р’Р°С€Р° Р·Р°СЏРІРєР° #{id} РЅР°Р·РЅР°С‡РµРЅР° С‚РµС…РЅРёРєСѓ.	\N	2025-07-03 15:13:40.531525+05
5	zayavka_completed	uz	Sizning zayavkangiz #{id} bajarildi.	\N	2025-07-03 15:13:40.531525+05
6	zayavka_completed	ru	Р’Р°С€Р° Р·Р°СЏРІРєР° #{id} РІС‹РїРѕР»РЅРµРЅР°.	\N	2025-07-03 15:13:40.531525+05
\.


--
-- Data for Name: notifications; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.notifications (id, user_id, zayavka_id, message, sent_at, channel) FROM stdin;
\.


--
-- Data for Name: solutions; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.solutions (id, zayavka_id, instander_id, solution_text, media, created_at) FROM stdin;
\.


--
-- Data for Name: status_logs; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.status_logs (id, zayavka_id, old_status, new_status, changed_by, changed_at) FROM stdin;
\.


--
-- Data for Name: system_settings; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.system_settings (id, setting_key, setting_value, description, updated_by, updated_at) FROM stdin;
1	bot_version	2.0.0	Current bot version	\N	2025-07-03 15:13:40.530045+05
2	maintenance_mode	false	Maintenance mode flag	\N	2025-07-03 15:13:40.530045+05
3	max_zayavkas_per_day	10	Maximum zayavkas per user per day	\N	2025-07-03 15:13:40.530045+05
4	default_language	uz	Default system language	\N	2025-07-03 15:13:40.530045+05
5	notification_enabled	true	Global notification flag	\N	2025-07-03 15:13:40.530045+05
\.


--
-- Data for Name: technician_locations; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.technician_locations (technician_id, latitude, longitude, updated_at) FROM stdin;
\.


--
-- Data for Name: technician_performance; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.technician_performance (id, technician_id, completed_tasks, average_completion_time, rating, updated_at) FROM stdin;
\.


--
-- Data for Name: technician_workload; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.technician_workload (id, technician_id, active_tasks, max_tasks, updated_at) FROM stdin;
\.


--
-- Data for Name: users; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.users (id, telegram_id, full_name, username, phone_number, role, abonent_id, language, is_active, address, permissions, created_at, updated_at) FROM stdin;
2	1978574076	Ulug'bek	ulugbekbb	998900042544	admin	\N	uz	t	\N	\N	2025-07-04 12:03:23.086731+05	2025-07-04 13:02:20.435395+05
1	8188731606	Barat	bratuuha	998881249327	client	\N	uz	t	Manzu	\N	2025-07-03 16:18:27.465056+05	2025-07-04 17:41:09.830316+05
\.


--
-- Data for Name: zayavka_transfers; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.zayavka_transfers (id, zayavka_id, from_technician_id, to_technician_id, transferred_by, reason, transferred_at) FROM stdin;
\.


--
-- Data for Name: zayavki; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.zayavki (id, user_id, description, media, status, address, latitude, longitude, assigned_to, zayavka_type, abonent_id, phone_number, priority, estimated_time, actual_time, completion_notes, created_by_role, created_by, ready_to_install, assigned_at, completed_at, created_at, updated_at) FROM stdin;
1	1	Salom	\N	new	Manzil 123	\N	\N	\N	b2b	\N	\N	1	\N	\N	\N	\N	\N	f	\N	\N	2025-07-03 16:43:57.892843+05	2025-07-03 16:43:57.892843+05
2	1	Salom hamaga	AgACAgIAAxkBAAIjrWhmbpmCA4L-UiqTomfvZsR2V23SAAIg8zEbTKE5SwIu-88WKC5NAQADAgADeQADNgQ	new	Manzil 123	41.32216800	69.28328800	\N	b2b	\N	\N	1	\N	\N	\N	\N	\N	f	\N	\N	2025-07-03 16:51:15.799271+05	2025-07-03 16:51:15.799271+05
\.


--
-- Name: admin_action_logs_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.admin_action_logs_id_seq', 1, true);


--
-- Name: call_logs_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.call_logs_id_seq', 1, false);


--
-- Name: chat_messages_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.chat_messages_id_seq', 1, false);


--
-- Name: chat_sessions_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.chat_sessions_id_seq', 1, false);


--
-- Name: equipment_requests_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.equipment_requests_id_seq', 1, false);


--
-- Name: feedback_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.feedback_id_seq', 1, false);


--
-- Name: help_requests_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.help_requests_id_seq', 1, false);


--
-- Name: issued_items_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.issued_items_id_seq', 1, false);


--
-- Name: login_logs_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.login_logs_id_seq', 1, false);


--
-- Name: material_receipts_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.material_receipts_id_seq', 1, false);


--
-- Name: materials_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.materials_id_seq', 1, false);


--
-- Name: notification_queue_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.notification_queue_id_seq', 1, false);


--
-- Name: notification_templates_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.notification_templates_id_seq', 6, true);


--
-- Name: notifications_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.notifications_id_seq', 1, false);


--
-- Name: solutions_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.solutions_id_seq', 1, false);


--
-- Name: status_logs_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.status_logs_id_seq', 1, false);


--
-- Name: system_settings_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.system_settings_id_seq', 5, true);


--
-- Name: technician_performance_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.technician_performance_id_seq', 1, false);


--
-- Name: technician_workload_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.technician_workload_id_seq', 1, false);


--
-- Name: users_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.users_id_seq', 7, true);


--
-- Name: zayavka_transfers_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.zayavka_transfers_id_seq', 1, false);


--
-- Name: zayavki_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.zayavki_id_seq', 2, true);


--
-- Name: admin_action_logs admin_action_logs_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.admin_action_logs
    ADD CONSTRAINT admin_action_logs_pkey PRIMARY KEY (id);


--
-- Name: call_logs call_logs_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.call_logs
    ADD CONSTRAINT call_logs_pkey PRIMARY KEY (id);


--
-- Name: chat_messages chat_messages_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.chat_messages
    ADD CONSTRAINT chat_messages_pkey PRIMARY KEY (id);


--
-- Name: chat_sessions chat_sessions_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.chat_sessions
    ADD CONSTRAINT chat_sessions_pkey PRIMARY KEY (id);


--
-- Name: equipment_requests equipment_requests_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.equipment_requests
    ADD CONSTRAINT equipment_requests_pkey PRIMARY KEY (id);


--
-- Name: feedback feedback_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.feedback
    ADD CONSTRAINT feedback_pkey PRIMARY KEY (id);


--
-- Name: help_requests help_requests_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.help_requests
    ADD CONSTRAINT help_requests_pkey PRIMARY KEY (id);


--
-- Name: issued_items issued_items_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.issued_items
    ADD CONSTRAINT issued_items_pkey PRIMARY KEY (id);


--
-- Name: login_logs login_logs_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.login_logs
    ADD CONSTRAINT login_logs_pkey PRIMARY KEY (id);


--
-- Name: material_receipts material_receipts_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.material_receipts
    ADD CONSTRAINT material_receipts_pkey PRIMARY KEY (id);


--
-- Name: materials materials_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.materials
    ADD CONSTRAINT materials_pkey PRIMARY KEY (id);


--
-- Name: notification_queue notification_queue_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.notification_queue
    ADD CONSTRAINT notification_queue_pkey PRIMARY KEY (id);


--
-- Name: notification_templates notification_templates_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.notification_templates
    ADD CONSTRAINT notification_templates_pkey PRIMARY KEY (id);


--
-- Name: notification_templates notification_templates_template_type_language_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.notification_templates
    ADD CONSTRAINT notification_templates_template_type_language_key UNIQUE (template_type, language);


--
-- Name: notifications notifications_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.notifications
    ADD CONSTRAINT notifications_pkey PRIMARY KEY (id);


--
-- Name: solutions solutions_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.solutions
    ADD CONSTRAINT solutions_pkey PRIMARY KEY (id);


--
-- Name: status_logs status_logs_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.status_logs
    ADD CONSTRAINT status_logs_pkey PRIMARY KEY (id);


--
-- Name: system_settings system_settings_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.system_settings
    ADD CONSTRAINT system_settings_pkey PRIMARY KEY (id);


--
-- Name: system_settings system_settings_setting_key_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.system_settings
    ADD CONSTRAINT system_settings_setting_key_key UNIQUE (setting_key);


--
-- Name: technician_locations technician_locations_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.technician_locations
    ADD CONSTRAINT technician_locations_pkey PRIMARY KEY (technician_id);


--
-- Name: technician_performance technician_performance_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.technician_performance
    ADD CONSTRAINT technician_performance_pkey PRIMARY KEY (id);


--
-- Name: technician_workload technician_workload_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.technician_workload
    ADD CONSTRAINT technician_workload_pkey PRIMARY KEY (id);


--
-- Name: users users_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_pkey PRIMARY KEY (id);


--
-- Name: users users_telegram_id_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.users
    ADD CONSTRAINT users_telegram_id_key UNIQUE (telegram_id);


--
-- Name: zayavka_transfers zayavka_transfers_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.zayavka_transfers
    ADD CONSTRAINT zayavka_transfers_pkey PRIMARY KEY (id);


--
-- Name: zayavki zayavki_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.zayavki
    ADD CONSTRAINT zayavki_pkey PRIMARY KEY (id);


--
-- Name: idx_call_logs_created_by; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_call_logs_created_by ON public.call_logs USING btree (created_by);


--
-- Name: idx_call_logs_user_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_call_logs_user_id ON public.call_logs USING btree (user_id);


--
-- Name: idx_chat_messages_session_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_chat_messages_session_id ON public.chat_messages USING btree (session_id);


--
-- Name: idx_feedback_zayavka_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_feedback_zayavka_id ON public.feedback USING btree (zayavka_id);


--
-- Name: idx_help_requests_technician_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_help_requests_technician_id ON public.help_requests USING btree (technician_id);


--
-- Name: idx_issued_items_material_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_issued_items_material_id ON public.issued_items USING btree (material_id);


--
-- Name: idx_issued_items_zayavka_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_issued_items_zayavka_id ON public.issued_items USING btree (zayavka_id);


--
-- Name: idx_materials_category; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_materials_category ON public.materials USING btree (category);


--
-- Name: idx_materials_low_stock; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_materials_low_stock ON public.materials USING btree (quantity, min_quantity) WHERE (quantity <= min_quantity);


--
-- Name: idx_notification_queue_sent; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_notification_queue_sent ON public.notification_queue USING btree (sent);


--
-- Name: idx_solutions_zayavka_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_solutions_zayavka_id ON public.solutions USING btree (zayavka_id);


--
-- Name: idx_status_logs_zayavka_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_status_logs_zayavka_id ON public.status_logs USING btree (zayavka_id);


--
-- Name: idx_technician_workload_technician; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_technician_workload_technician ON public.technician_workload USING btree (technician_id);


--
-- Name: idx_users_phone; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_users_phone ON public.users USING btree (phone_number);


--
-- Name: idx_users_role; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_users_role ON public.users USING btree (role);


--
-- Name: idx_users_role_updated; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_users_role_updated ON public.users USING btree (role);


--
-- Name: idx_users_telegram_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_users_telegram_id ON public.users USING btree (telegram_id);


--
-- Name: idx_zayavki_assigned_to; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_zayavki_assigned_to ON public.zayavki USING btree (assigned_to);


--
-- Name: idx_zayavki_created_at; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_zayavki_created_at ON public.zayavki USING btree (created_at);


--
-- Name: idx_zayavki_location; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_zayavki_location ON public.zayavki USING btree (latitude, longitude);


--
-- Name: idx_zayavki_status; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_zayavki_status ON public.zayavki USING btree (status);


--
-- Name: idx_zayavki_user_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_zayavki_user_id ON public.zayavki USING btree (user_id);


--
-- Name: equipment_requests update_equipment_requests_updated_at; Type: TRIGGER; Schema: public; Owner: postgres
--

CREATE TRIGGER update_equipment_requests_updated_at BEFORE UPDATE ON public.equipment_requests FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();


--
-- Name: help_requests update_help_requests_updated_at; Type: TRIGGER; Schema: public; Owner: postgres
--

CREATE TRIGGER update_help_requests_updated_at BEFORE UPDATE ON public.help_requests FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();


--
-- Name: materials update_materials_updated_at; Type: TRIGGER; Schema: public; Owner: postgres
--

CREATE TRIGGER update_materials_updated_at BEFORE UPDATE ON public.materials FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();


--
-- Name: users update_users_updated_at; Type: TRIGGER; Schema: public; Owner: postgres
--

CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON public.users FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();


--
-- Name: zayavki update_zayavki_updated_at; Type: TRIGGER; Schema: public; Owner: postgres
--

CREATE TRIGGER update_zayavki_updated_at BEFORE UPDATE ON public.zayavki FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();


--
-- Name: call_logs call_logs_created_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.call_logs
    ADD CONSTRAINT call_logs_created_by_fkey FOREIGN KEY (created_by) REFERENCES public.users(id) ON DELETE SET NULL;


--
-- Name: call_logs call_logs_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.call_logs
    ADD CONSTRAINT call_logs_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE SET NULL;


--
-- Name: chat_messages chat_messages_sender_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.chat_messages
    ADD CONSTRAINT chat_messages_sender_id_fkey FOREIGN KEY (sender_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: chat_messages chat_messages_session_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.chat_messages
    ADD CONSTRAINT chat_messages_session_id_fkey FOREIGN KEY (session_id) REFERENCES public.chat_sessions(id) ON DELETE CASCADE;


--
-- Name: chat_sessions chat_sessions_operator_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.chat_sessions
    ADD CONSTRAINT chat_sessions_operator_id_fkey FOREIGN KEY (operator_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: chat_sessions chat_sessions_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.chat_sessions
    ADD CONSTRAINT chat_sessions_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: equipment_requests equipment_requests_approved_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.equipment_requests
    ADD CONSTRAINT equipment_requests_approved_by_fkey FOREIGN KEY (approved_by) REFERENCES public.users(id) ON DELETE SET NULL;


--
-- Name: equipment_requests equipment_requests_technician_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.equipment_requests
    ADD CONSTRAINT equipment_requests_technician_id_fkey FOREIGN KEY (technician_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: feedback feedback_created_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.feedback
    ADD CONSTRAINT feedback_created_by_fkey FOREIGN KEY (created_by) REFERENCES public.users(id) ON DELETE SET NULL;


--
-- Name: feedback feedback_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.feedback
    ADD CONSTRAINT feedback_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: feedback feedback_zayavka_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.feedback
    ADD CONSTRAINT feedback_zayavka_id_fkey FOREIGN KEY (zayavka_id) REFERENCES public.zayavki(id) ON DELETE CASCADE;


--
-- Name: help_requests help_requests_assigned_to_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.help_requests
    ADD CONSTRAINT help_requests_assigned_to_fkey FOREIGN KEY (assigned_to) REFERENCES public.users(id) ON DELETE SET NULL;


--
-- Name: help_requests help_requests_technician_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.help_requests
    ADD CONSTRAINT help_requests_technician_id_fkey FOREIGN KEY (technician_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: issued_items issued_items_issued_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.issued_items
    ADD CONSTRAINT issued_items_issued_by_fkey FOREIGN KEY (issued_by) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: issued_items issued_items_issued_to_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.issued_items
    ADD CONSTRAINT issued_items_issued_to_fkey FOREIGN KEY (issued_to) REFERENCES public.users(id) ON DELETE SET NULL;


--
-- Name: issued_items issued_items_material_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.issued_items
    ADD CONSTRAINT issued_items_material_id_fkey FOREIGN KEY (material_id) REFERENCES public.materials(id) ON DELETE CASCADE;


--
-- Name: issued_items issued_items_zayavka_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.issued_items
    ADD CONSTRAINT issued_items_zayavka_id_fkey FOREIGN KEY (zayavka_id) REFERENCES public.zayavki(id) ON DELETE CASCADE;


--
-- Name: material_receipts material_receipts_material_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.material_receipts
    ADD CONSTRAINT material_receipts_material_id_fkey FOREIGN KEY (material_id) REFERENCES public.materials(id) ON DELETE CASCADE;


--
-- Name: material_receipts material_receipts_received_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.material_receipts
    ADD CONSTRAINT material_receipts_received_by_fkey FOREIGN KEY (received_by) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: notification_templates notification_templates_updated_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.notification_templates
    ADD CONSTRAINT notification_templates_updated_by_fkey FOREIGN KEY (updated_by) REFERENCES public.users(id) ON DELETE SET NULL;


--
-- Name: solutions solutions_instander_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.solutions
    ADD CONSTRAINT solutions_instander_id_fkey FOREIGN KEY (instander_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: solutions solutions_zayavka_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.solutions
    ADD CONSTRAINT solutions_zayavka_id_fkey FOREIGN KEY (zayavka_id) REFERENCES public.zayavki(id) ON DELETE CASCADE;


--
-- Name: status_logs status_logs_changed_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.status_logs
    ADD CONSTRAINT status_logs_changed_by_fkey FOREIGN KEY (changed_by) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: status_logs status_logs_zayavka_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.status_logs
    ADD CONSTRAINT status_logs_zayavka_id_fkey FOREIGN KEY (zayavka_id) REFERENCES public.zayavki(id) ON DELETE CASCADE;


--
-- Name: system_settings system_settings_updated_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.system_settings
    ADD CONSTRAINT system_settings_updated_by_fkey FOREIGN KEY (updated_by) REFERENCES public.users(id) ON DELETE SET NULL;


--
-- Name: technician_locations technician_locations_technician_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.technician_locations
    ADD CONSTRAINT technician_locations_technician_id_fkey FOREIGN KEY (technician_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: zayavki zayavki_assigned_to_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.zayavki
    ADD CONSTRAINT zayavki_assigned_to_fkey FOREIGN KEY (assigned_to) REFERENCES public.users(id) ON DELETE SET NULL;


--
-- Name: zayavki zayavki_created_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.zayavki
    ADD CONSTRAINT zayavki_created_by_fkey FOREIGN KEY (created_by) REFERENCES public.users(id) ON DELETE SET NULL;


--
-- Name: zayavki zayavki_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.zayavki
    ADD CONSTRAINT zayavki_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- PostgreSQL database dump complete
--

