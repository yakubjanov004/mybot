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
-- Name: access_control_logs; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.access_control_logs (
    id integer NOT NULL,
    user_id integer NOT NULL,
    action character varying(100) NOT NULL,
    resource character varying(200) NOT NULL,
    granted boolean DEFAULT false NOT NULL,
    reason text,
    "timestamp" timestamp with time zone DEFAULT now() NOT NULL,
    ip_address inet,
    user_agent text,
    session_id character varying(100)
);


ALTER TABLE public.access_control_logs OWNER TO postgres;

--
-- Name: TABLE access_control_logs; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON TABLE public.access_control_logs IS 'Audit trail for workflow access control attempts';


--
-- Name: access_control_logs_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.access_control_logs_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.access_control_logs_id_seq OWNER TO postgres;

--
-- Name: access_control_logs_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.access_control_logs_id_seq OWNED BY public.access_control_logs.id;


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
-- Name: client_selection_data; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.client_selection_data (
    id integer NOT NULL,
    search_method character varying(20) DEFAULT 'phone'::character varying NOT NULL,
    search_value character varying(255),
    client_id integer,
    new_client_data jsonb DEFAULT '{}'::jsonb,
    verified boolean DEFAULT false,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_search_method CHECK (((search_method)::text = ANY ((ARRAY['phone'::character varying, 'name'::character varying, 'id'::character varying, 'new'::character varying])::text[]))),
    CONSTRAINT client_selection_data_search_method_check CHECK (((search_method)::text = ANY ((ARRAY['phone'::character varying, 'name'::character varying, 'id'::character varying, 'new'::character varying])::text[])))
);


ALTER TABLE public.client_selection_data OWNER TO postgres;

--
-- Name: TABLE client_selection_data; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON TABLE public.client_selection_data IS 'Data about client selection during staff application creation';


--
-- Name: COLUMN client_selection_data.search_method; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.client_selection_data.search_method IS 'Method used to search/select client';


--
-- Name: COLUMN client_selection_data.search_value; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.client_selection_data.search_value IS 'Value used for client search';


--
-- Name: COLUMN client_selection_data.new_client_data; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.client_selection_data.new_client_data IS 'Data for newly created clients';


--
-- Name: client_selection_data_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.client_selection_data_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.client_selection_data_id_seq OWNER TO postgres;

--
-- Name: client_selection_data_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.client_selection_data_id_seq OWNED BY public.client_selection_data.id;


--
-- Name: staff_application_audit; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.staff_application_audit (
    id integer NOT NULL,
    application_id character varying(36),
    creator_id integer NOT NULL,
    creator_role character varying(50) NOT NULL,
    client_id integer,
    application_type character varying(50),
    creation_timestamp timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    client_notified boolean DEFAULT false,
    client_notified_at timestamp with time zone,
    workflow_initiated boolean DEFAULT false,
    workflow_initiated_at timestamp with time zone,
    metadata jsonb DEFAULT '{}'::jsonb,
    ip_address inet,
    user_agent text,
    session_id character varying(255),
    CONSTRAINT chk_application_type CHECK (((application_type)::text = ANY ((ARRAY['connection_request'::character varying, 'technical_service'::character varying])::text[]))),
    CONSTRAINT chk_creator_role CHECK (((creator_role)::text = ANY ((ARRAY['manager'::character varying, 'junior_manager'::character varying, 'controller'::character varying, 'call_center'::character varying, 'admin'::character varying])::text[]))),
    CONSTRAINT staff_application_audit_application_type_check CHECK (((application_type)::text = ANY ((ARRAY['connection_request'::character varying, 'technical_service'::character varying])::text[]))),
    CONSTRAINT staff_application_audit_creator_role_check CHECK (((creator_role)::text = ANY ((ARRAY['admin'::character varying, 'call_center'::character varying, 'call_center_supervisor'::character varying, 'technician'::character varying, 'manager'::character varying, 'junior_manager'::character varying, 'controller'::character varying, 'warehouse'::character varying, 'client'::character varying, 'blocked'::character varying])::text[])))
);


ALTER TABLE public.staff_application_audit OWNER TO postgres;

--
-- Name: TABLE staff_application_audit; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON TABLE public.staff_application_audit IS 'Audit log for staff-created applications';


--
-- Name: COLUMN staff_application_audit.application_id; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.staff_application_audit.application_id IS 'ID of the created application';


--
-- Name: COLUMN staff_application_audit.creator_id; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.staff_application_audit.creator_id IS 'ID of staff member who created the application';


--
-- Name: COLUMN staff_application_audit.creator_role; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.staff_application_audit.creator_role IS 'Role of the staff member';


--
-- Name: COLUMN staff_application_audit.client_id; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.staff_application_audit.client_id IS 'ID of the client for whom application was created';


--
-- Name: COLUMN staff_application_audit.application_type; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.staff_application_audit.application_type IS 'Type of application (connection_request, technical_service)';


--
-- Name: COLUMN staff_application_audit.metadata; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.staff_application_audit.metadata IS 'Additional audit data in JSON format';


--
-- Name: COLUMN staff_application_audit.session_id; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.staff_application_audit.session_id IS 'Session ID for tracking related audit events';


--
-- Name: creator_performance_summary; Type: VIEW; Schema: public; Owner: postgres
--

CREATE VIEW public.creator_performance_summary AS
 SELECT creator_id,
    creator_role,
    count(*) AS total_applications,
    count(
        CASE
            WHEN client_notified THEN 1
            ELSE NULL::integer
        END) AS notified_applications,
    count(
        CASE
            WHEN workflow_initiated THEN 1
            ELSE NULL::integer
        END) AS workflow_applications,
    count(
        CASE
            WHEN (client_notified AND workflow_initiated) THEN 1
            ELSE NULL::integer
        END) AS successful_applications,
    round((((count(
        CASE
            WHEN (client_notified AND workflow_initiated) THEN 1
            ELSE NULL::integer
        END))::numeric / (count(*))::numeric) * (100)::numeric), 2) AS success_rate,
    count(
        CASE
            WHEN ((metadata ->> 'event_type'::text) = 'error_occurred'::text) THEN 1
            ELSE NULL::integer
        END) AS error_count,
    min(creation_timestamp) AS first_application,
    max(creation_timestamp) AS last_application
   FROM public.staff_application_audit
  WHERE (creation_timestamp >= (CURRENT_DATE - '30 days'::interval))
  GROUP BY creator_id, creator_role
  ORDER BY (count(*)) DESC;


ALTER VIEW public.creator_performance_summary OWNER TO postgres;

--
-- Name: VIEW creator_performance_summary; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON VIEW public.creator_performance_summary IS 'Performance metrics for individual creators';


--
-- Name: daily_audit_stats; Type: VIEW; Schema: public; Owner: postgres
--

CREATE VIEW public.daily_audit_stats AS
 SELECT date(creation_timestamp) AS audit_date,
    count(*) AS total_applications,
    count(DISTINCT creator_id) AS active_creators,
    count(DISTINCT client_id) AS affected_clients,
    count(
        CASE
            WHEN ((application_type)::text = 'connection_request'::text) THEN 1
            ELSE NULL::integer
        END) AS connection_requests,
    count(
        CASE
            WHEN ((application_type)::text = 'technical_service'::text) THEN 1
            ELSE NULL::integer
        END) AS technical_services,
    count(
        CASE
            WHEN (client_notified AND workflow_initiated) THEN 1
            ELSE NULL::integer
        END) AS successful_applications,
    round((((count(
        CASE
            WHEN (client_notified AND workflow_initiated) THEN 1
            ELSE NULL::integer
        END))::numeric / (count(*))::numeric) * (100)::numeric), 2) AS daily_success_rate
   FROM public.staff_application_audit
  WHERE (creation_timestamp >= (CURRENT_DATE - '90 days'::interval))
  GROUP BY (date(creation_timestamp))
  ORDER BY (date(creation_timestamp)) DESC;


ALTER VIEW public.daily_audit_stats OWNER TO postgres;

--
-- Name: VIEW daily_audit_stats; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON VIEW public.daily_audit_stats IS 'Daily statistics for audit activities';


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
-- Name: error_records; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.error_records (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    category character varying(50) NOT NULL,
    severity character varying(20) NOT NULL,
    message text NOT NULL,
    details jsonb DEFAULT '{}'::jsonb,
    context jsonb DEFAULT '{}'::jsonb,
    stack_trace text,
    occurred_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    resolved_at timestamp with time zone,
    resolution_notes text,
    retry_count integer DEFAULT 0,
    max_retries integer DEFAULT 3
);


ALTER TABLE public.error_records OWNER TO postgres;

--
-- Name: feedback; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.feedback (
    id integer NOT NULL,
    zayavka_id integer NOT NULL,
    user_id integer NOT NULL,
    rating integer NOT NULL,
    comment text,
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
-- Name: inventory_transactions; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.inventory_transactions (
    id integer NOT NULL,
    request_id character varying(50),
    equipment_id integer,
    quantity_used integer DEFAULT 0 NOT NULL,
    transaction_type character varying(50) DEFAULT 'consume'::character varying NOT NULL,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    created_by integer
);


ALTER TABLE public.inventory_transactions OWNER TO postgres;

--
-- Name: inventory_transactions_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.inventory_transactions_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.inventory_transactions_id_seq OWNER TO postgres;

--
-- Name: inventory_transactions_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.inventory_transactions_id_seq OWNED BY public.inventory_transactions.id;


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
-- Name: messages; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.messages (
    id integer NOT NULL,
    zayavka_id integer,
    sender_id integer,
    recipient_role character varying(30) NOT NULL,
    recipient_user_id integer,
    message_text text NOT NULL,
    message_type character varying(20) DEFAULT 'text'::character varying,
    is_read boolean DEFAULT false,
    is_urgent boolean DEFAULT false,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.messages OWNER TO postgres;

--
-- Name: messages_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.messages_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.messages_id_seq OWNER TO postgres;

--
-- Name: messages_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.messages_id_seq OWNED BY public.messages.id;


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
-- Name: notification_retry_queue; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.notification_retry_queue (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    role character varying(50) NOT NULL,
    request_id uuid NOT NULL,
    workflow_type character varying(100) NOT NULL,
    retry_count integer DEFAULT 0,
    max_retries integer DEFAULT 5,
    next_retry_at timestamp with time zone NOT NULL,
    last_error text,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    status character varying(20) DEFAULT 'pending'::character varying
);


ALTER TABLE public.notification_retry_queue OWNER TO postgres;

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
    title text,
    notification_type character varying(50) DEFAULT 'info'::character varying,
    related_id integer,
    related_type character varying(50),
    is_read boolean DEFAULT false,
    read_at timestamp with time zone,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
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
-- Name: pending_notifications; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.pending_notifications (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    user_id integer NOT NULL,
    request_id uuid NOT NULL,
    workflow_type character varying(100) NOT NULL,
    role character varying(50) NOT NULL,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    is_handled boolean DEFAULT false,
    handled_at timestamp with time zone
);


ALTER TABLE public.pending_notifications OWNER TO postgres;

--
-- Name: role_change_logs; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.role_change_logs (
    id integer NOT NULL,
    user_telegram_id bigint NOT NULL,
    old_role character varying(20) NOT NULL,
    new_role character varying(20) NOT NULL,
    changed_by bigint NOT NULL,
    changed_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.role_change_logs OWNER TO postgres;

--
-- Name: role_change_logs_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.role_change_logs_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.role_change_logs_id_seq OWNER TO postgres;

--
-- Name: role_change_logs_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.role_change_logs_id_seq OWNED BY public.role_change_logs.id;


--
-- Name: service_requests; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.service_requests (
    id character varying(50) NOT NULL,
    workflow_type character varying(50) NOT NULL,
    client_id integer,
    role_current character varying(50),
    current_status character varying(50) DEFAULT 'created'::character varying NOT NULL,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    priority character varying(20) DEFAULT 'medium'::character varying NOT NULL,
    description text,
    location text,
    contact_info jsonb DEFAULT '{}'::jsonb,
    state_data jsonb DEFAULT '{}'::jsonb,
    equipment_used jsonb DEFAULT '[]'::jsonb,
    inventory_updated boolean DEFAULT false,
    completion_rating integer,
    feedback_comments text,
    created_by_staff boolean DEFAULT false,
    staff_creator_id integer,
    staff_creator_role character varying(50),
    creation_source character varying(50) DEFAULT 'client'::character varying,
    client_notified_at timestamp with time zone,
    CONSTRAINT chk_creation_source CHECK (((creation_source)::text = ANY ((ARRAY['client'::character varying, 'manager'::character varying, 'junior_manager'::character varying, 'controller'::character varying, 'call_center'::character varying])::text[]))),
    CONSTRAINT chk_staff_creator_role CHECK (((staff_creator_role)::text = ANY ((ARRAY['admin'::character varying, 'call_center'::character varying, 'call_center_supervisor'::character varying, 'technician'::character varying, 'manager'::character varying, 'junior_manager'::character varying, 'controller'::character varying, 'warehouse'::character varying, 'client'::character varying, 'blocked'::character varying])::text[]))),
    CONSTRAINT service_requests_creation_source_check CHECK (((creation_source)::text = ANY ((ARRAY['client'::character varying, 'manager'::character varying, 'junior_manager'::character varying, 'controller'::character varying, 'call_center'::character varying])::text[]))),
    CONSTRAINT service_requests_staff_creator_role_check CHECK (((staff_creator_role)::text = ANY ((ARRAY['admin'::character varying, 'call_center'::character varying, 'call_center_supervisor'::character varying, 'technician'::character varying, 'manager'::character varying, 'junior_manager'::character varying, 'controller'::character varying, 'warehouse'::character varying, 'client'::character varying, 'blocked'::character varying])::text[])))
);


ALTER TABLE public.service_requests OWNER TO postgres;

--
-- Name: COLUMN service_requests.created_by_staff; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.service_requests.created_by_staff IS 'Flag indicating if this request was created by staff on behalf of a client';


--
-- Name: COLUMN service_requests.staff_creator_id; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.service_requests.staff_creator_id IS 'ID of the staff member who created this request';


--
-- Name: COLUMN service_requests.staff_creator_role; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.service_requests.staff_creator_role IS 'Role of the staff member who created this request';


--
-- Name: COLUMN service_requests.creation_source; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.service_requests.creation_source IS 'Source of request creation (client, manager, junior_manager, controller, call_center)';


--
-- Name: COLUMN service_requests.client_notified_at; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON COLUMN public.service_requests.client_notified_at IS 'Timestamp when client was notified about staff-created request';


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
-- Name: staff_application_audit_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.staff_application_audit_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.staff_application_audit_id_seq OWNER TO postgres;

--
-- Name: staff_application_audit_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.staff_application_audit_id_seq OWNED BY public.staff_application_audit.id;


--
-- Name: staff_audit_summary; Type: VIEW; Schema: public; Owner: postgres
--

CREATE VIEW public.staff_audit_summary AS
 SELECT creator_role,
    application_type,
    date(creation_timestamp) AS audit_date,
    count(*) AS total_applications,
    count(
        CASE
            WHEN client_notified THEN 1
            ELSE NULL::integer
        END) AS notified_applications,
    count(
        CASE
            WHEN workflow_initiated THEN 1
            ELSE NULL::integer
        END) AS workflow_applications,
    count(
        CASE
            WHEN (client_notified AND workflow_initiated) THEN 1
            ELSE NULL::integer
        END) AS successful_applications,
    round((((count(
        CASE
            WHEN (client_notified AND workflow_initiated) THEN 1
            ELSE NULL::integer
        END))::numeric / (count(*))::numeric) * (100)::numeric), 2) AS success_rate
   FROM public.staff_application_audit
  WHERE (creation_timestamp >= (CURRENT_DATE - '30 days'::interval))
  GROUP BY creator_role, application_type, (date(creation_timestamp))
  ORDER BY (date(creation_timestamp)) DESC, creator_role, application_type;


ALTER VIEW public.staff_audit_summary OWNER TO postgres;

--
-- Name: VIEW staff_audit_summary; Type: COMMENT; Schema: public; Owner: postgres
--

COMMENT ON VIEW public.staff_audit_summary IS 'Summary of staff application creation by role, type, and date';


--
-- Name: state_transitions; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.state_transitions (
    id integer NOT NULL,
    request_id character varying(50) NOT NULL,
    from_role character varying(50),
    to_role character varying(50),
    action character varying(100),
    actor_id integer,
    transition_data jsonb DEFAULT '{}'::jsonb,
    comments text,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP
);


ALTER TABLE public.state_transitions OWNER TO postgres;

--
-- Name: state_transitions_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.state_transitions_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.state_transitions_id_seq OWNER TO postgres;

--
-- Name: state_transitions_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.state_transitions_id_seq OWNED BY public.state_transitions.id;


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
-- Name: system_health_snapshots; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.system_health_snapshots (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    snapshot_time timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    active_requests integer DEFAULT 0,
    pending_notifications integer DEFAULT 0,
    active_transactions integer DEFAULT 0,
    error_count_24h integer DEFAULT 0,
    inventory_discrepancies integer DEFAULT 0,
    stuck_workflows integer DEFAULT 0,
    system_status character varying(20) DEFAULT 'healthy'::character varying,
    metrics jsonb DEFAULT '{}'::jsonb,
    notes text
);


ALTER TABLE public.system_health_snapshots OWNER TO postgres;

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
-- Name: transaction_log; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.transaction_log (
    id uuid DEFAULT gen_random_uuid() NOT NULL,
    transaction_id uuid NOT NULL,
    operation_type character varying(100) NOT NULL,
    operation_data jsonb DEFAULT '{}'::jsonb,
    rollback_data jsonb DEFAULT '{}'::jsonb,
    status character varying(20) DEFAULT 'pending'::character varying,
    started_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    completed_at timestamp with time zone,
    error_message text
);


ALTER TABLE public.transaction_log OWNER TO postgres;

--
-- Name: user_action_logs; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.user_action_logs (
    id integer NOT NULL,
    user_telegram_id bigint NOT NULL,
    action character varying(50) NOT NULL,
    performed_by bigint NOT NULL,
    performed_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP NOT NULL
);


ALTER TABLE public.user_action_logs OWNER TO postgres;

--
-- Name: user_action_logs_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.user_action_logs_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.user_action_logs_id_seq OWNER TO postgres;

--
-- Name: user_action_logs_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.user_action_logs_id_seq OWNED BY public.user_action_logs.id;


--
-- Name: users; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.users (
    id integer NOT NULL,
    telegram_id bigint NOT NULL,
    full_name text,
    username text,
    phone_number text,
    role character varying(30) NOT NULL,
    abonent_id character varying(50),
    language character varying(2) DEFAULT 'uz'::character varying NOT NULL,
    is_active boolean DEFAULT true NOT NULL,
    address text,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    permissions text,
    CONSTRAINT users_language_check CHECK (((language)::text = ANY ((ARRAY['uz'::character varying, 'ru'::character varying])::text[]))),
    CONSTRAINT users_role_check CHECK (((role)::text = ANY ((ARRAY['admin'::character varying, 'call_center'::character varying, 'call_center_supervisor'::character varying, 'technician'::character varying, 'manager'::character varying, 'junior_manager'::character varying, 'controller'::character varying, 'warehouse'::character varying, 'client'::character varying, 'blocked'::character varying])::text[])))
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
-- Name: zayavka_status_history; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.zayavka_status_history (
    id integer NOT NULL,
    zayavka_id integer NOT NULL,
    old_status character varying(30) NOT NULL,
    new_status character varying(30) NOT NULL,
    changed_by integer NOT NULL,
    changed_by_role character varying(30),
    changed_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    comment text
);


ALTER TABLE public.zayavka_status_history OWNER TO postgres;

--
-- Name: zayavka_status_history_id_seq; Type: SEQUENCE; Schema: public; Owner: postgres
--

CREATE SEQUENCE public.zayavka_status_history_id_seq
    AS integer
    START WITH 1
    INCREMENT BY 1
    NO MINVALUE
    NO MAXVALUE
    CACHE 1;


ALTER SEQUENCE public.zayavka_status_history_id_seq OWNER TO postgres;

--
-- Name: zayavka_status_history_id_seq; Type: SEQUENCE OWNED BY; Schema: public; Owner: postgres
--

ALTER SEQUENCE public.zayavka_status_history_id_seq OWNED BY public.zayavka_status_history.id;


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
    public_id character varying(20),
    zayavka_type character varying(10) NOT NULL,
    user_id integer NOT NULL,
    description text NOT NULL,
    status character varying(30) DEFAULT 'new'::character varying NOT NULL,
    role_current character varying(30),
    current_user_id integer,
    address text,
    latitude numeric(10,8),
    longitude numeric(11,8),
    abonent_id character varying(50),
    phone_number text,
    priority integer DEFAULT 1 NOT NULL,
    created_by integer,
    created_by_role character varying(30),
    assigned_at timestamp with time zone,
    completed_at timestamp with time zone,
    closed_at timestamp with time zone,
    created_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone DEFAULT CURRENT_TIMESTAMP,
    assigned_to integer,
    CONSTRAINT zayavki_priority_check CHECK (((priority >= 1) AND (priority <= 5))),
    CONSTRAINT zayavki_zayavka_type_check CHECK (((zayavka_type)::text = ANY ((ARRAY['ul'::character varying, 'tx'::character varying])::text[])))
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
-- Name: access_control_logs id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.access_control_logs ALTER COLUMN id SET DEFAULT nextval('public.access_control_logs_id_seq'::regclass);


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
-- Name: client_selection_data id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.client_selection_data ALTER COLUMN id SET DEFAULT nextval('public.client_selection_data_id_seq'::regclass);


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
-- Name: inventory_transactions id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.inventory_transactions ALTER COLUMN id SET DEFAULT nextval('public.inventory_transactions_id_seq'::regclass);


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
-- Name: messages id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.messages ALTER COLUMN id SET DEFAULT nextval('public.messages_id_seq'::regclass);


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
-- Name: role_change_logs id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.role_change_logs ALTER COLUMN id SET DEFAULT nextval('public.role_change_logs_id_seq'::regclass);


--
-- Name: solutions id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.solutions ALTER COLUMN id SET DEFAULT nextval('public.solutions_id_seq'::regclass);


--
-- Name: staff_application_audit id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.staff_application_audit ALTER COLUMN id SET DEFAULT nextval('public.staff_application_audit_id_seq'::regclass);


--
-- Name: state_transitions id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.state_transitions ALTER COLUMN id SET DEFAULT nextval('public.state_transitions_id_seq'::regclass);


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
-- Name: user_action_logs id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.user_action_logs ALTER COLUMN id SET DEFAULT nextval('public.user_action_logs_id_seq'::regclass);


--
-- Name: users id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.users ALTER COLUMN id SET DEFAULT nextval('public.users_id_seq'::regclass);


--
-- Name: zayavka_status_history id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.zayavka_status_history ALTER COLUMN id SET DEFAULT nextval('public.zayavka_status_history_id_seq'::regclass);


--
-- Name: zayavka_transfers id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.zayavka_transfers ALTER COLUMN id SET DEFAULT nextval('public.zayavka_transfers_id_seq'::regclass);


--
-- Name: zayavki id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.zayavki ALTER COLUMN id SET DEFAULT nextval('public.zayavki_id_seq'::regclass);


--
-- Data for Name: access_control_logs; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.access_control_logs (id, user_id, action, resource, granted, reason, "timestamp", ip_address, user_agent, session_id) FROM stdin;
\.


--
-- Data for Name: admin_action_logs; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.admin_action_logs (id, admin_id, action, details, performed_at) FROM stdin;
1	1978574076	admin_login	\N	2025-07-04 17:36:07.488688
2	1978574076	admin_login	\N	2025-07-07 10:12:35.046055
3	1978574076	admin_login	\N	2025-07-07 10:12:51.808329
4	1978574076	admin_login	\N	2025-07-07 11:43:48.437888
5	1978574076	admin_login	\N	2025-07-07 11:46:50.650668
6	1978574076	admin_login	\N	2025-07-07 11:54:01.277252
7	1978574076	admin_login	\N	2025-07-07 14:14:08.412129
8	1978574076	admin_login	\N	2025-07-07 14:16:15.237427
9	1978574076	admin_login	\N	2025-07-07 14:34:28.379844
10	1978574076	admin_login	\N	2025-07-07 15:16:19.530415
11	1978574076	admin_login	\N	2025-07-07 15:27:19.956108
12	1978574076	admin_login	\N	2025-07-07 15:33:23.465314
13	1978574076	admin_login	\N	2025-07-07 15:33:27.255936
14	1978574076	admin_login	\N	2025-07-07 15:33:34.595961
15	1978574076	admin_login	\N	2025-07-07 15:33:38.320871
16	1978574076	admin_login	\N	2025-07-07 15:33:42.70824
17	1978574076	admin_login	\N	2025-07-07 15:33:45.737262
18	1978574076	admin_login	\N	2025-07-07 15:33:54.918544
19	1978574076	admin_login	\N	2025-07-07 15:34:01.588682
20	1978574076	admin_login	\N	2025-07-07 15:34:05.435655
21	1978574076	admin_login	\N	2025-07-07 15:34:08.097011
22	1978574076	admin_login	\N	2025-07-07 15:34:13.108254
23	1978574076	admin_login	\N	2025-07-07 15:35:34.260764
24	1978574076	admin_login	\N	2025-07-07 15:35:47.182057
25	1978574076	admin_login	\N	2025-07-07 15:35:49.103863
26	1978574076	admin_login	\N	2025-07-07 15:35:54.645428
27	1978574076	admin_login	\N	2025-07-07 15:37:04.849364
28	1978574076	admin_login	\N	2025-07-07 15:37:11.022366
29	1978574076	admin_login	\N	2025-07-07 15:37:18.308088
30	1978574076	admin_login	\N	2025-07-07 15:37:20.746228
31	1978574076	admin_login	\N	2025-07-07 15:37:23.530444
32	1978574076	admin_login	\N	2025-07-07 15:37:35.841992
33	1978574076	admin_login	\N	2025-07-07 15:37:58.673539
34	1978574076	admin_login	\N	2025-07-07 15:38:02.756067
35	1978574076	admin_login	\N	2025-07-07 15:38:09.225389
36	1978574076	admin_login	\N	2025-07-07 15:38:23.737786
37	1978574076	admin_login	\N	2025-07-07 15:39:13.295758
38	1978574076	admin_login	\N	2025-07-07 15:39:18.888421
39	1978574076	admin_login	\N	2025-07-07 15:39:29.45957
40	1978574076	admin_login	\N	2025-07-07 15:39:38.53073
41	1978574076	admin_login	\N	2025-07-07 15:41:42.330873
42	1978574076	admin_login	\N	2025-07-07 15:52:17.114174
43	1978574076	admin_login	\N	2025-07-07 15:56:16.470043
44	1978574076	admin_login	\N	2025-07-07 15:58:57.743744
45	1978574076	admin_login	\N	2025-07-07 16:01:12.537587
46	1978574076	admin_login	\N	2025-07-07 16:01:39.059669
47	1978574076	admin_login	\N	2025-07-07 16:02:42.869241
48	1978574076	admin_login	\N	2025-07-07 16:03:33.986889
49	1978574076	admin_login	\N	2025-07-07 16:04:48.816333
50	1978574076	admin_login	\N	2025-07-07 16:06:11.208065
51	1978574076	admin_login	\N	2025-07-07 16:07:24.666203
52	1978574076	admin_login	\N	2025-07-07 16:08:21.403977
53	1978574076	admin_login	\N	2025-07-07 16:09:52.649099
54	1978574076	admin_login	\N	2025-07-08 10:43:42.351707
55	1978574076	admin_login	\N	2025-07-08 10:56:57.308001
56	1978574076	admin_login	\N	2025-07-08 10:59:17.874512
57	1978574076	admin_login	\N	2025-07-08 11:01:24.526612
58	1978574076	admin_login	\N	2025-07-08 11:04:05.312841
59	1978574076	admin_login	\N	2025-07-08 11:05:56.862686
60	1978574076	admin_login	\N	2025-07-08 11:26:21.336651
61	1978574076	admin_login	\N	2025-07-08 11:29:59.743977
62	1978574076	admin_login	\N	2025-07-08 11:30:29.324586
63	1978574076	admin_login	\N	2025-07-08 11:34:03.922329
64	1978574076	admin_login	\N	2025-07-08 11:37:01.675055
65	1978574076	admin_login	\N	2025-07-08 11:41:50.208674
66	1978574076	admin_login	\N	2025-07-08 11:45:41.409751
67	1978574076	admin_login	\N	2025-07-08 11:47:02.075984
68	1978574076	admin_login	\N	2025-07-08 11:54:23.855931
69	1978574076	admin_login	\N	2025-07-08 11:56:07.340027
70	1978574076	admin_login	\N	2025-07-08 11:57:18.888162
71	1978574076	admin_login	\N	2025-07-08 11:58:23.41394
72	1978574076	role_change	{"user_id": 5955605892, "new_role": "warehouse", "old_role": "manager"}	2025-07-08 11:58:50.969452
73	1978574076	admin_login	\N	2025-07-08 11:59:36.370172
74	1978574076	role_change	{"user_id": 5955605892, "new_role": "warehouse", "old_role": "manager"}	2025-07-08 12:00:07.473267
75	1978574076	admin_login	\N	2025-07-08 12:00:21.42362
76	1978574076	admin_login	\N	2025-07-08 12:06:12.517025
77	1978574076	admin_login	\N	2025-07-08 12:08:30.101764
78	1978574076	admin_login	\N	2025-07-08 12:10:20.777605
79	1978574076	admin_login	\N	2025-07-08 12:12:32.056315
80	1978574076	role_change	{"user_id": 5955605892, "new_role": "manager", "old_role": "warehouse"}	2025-07-08 12:12:47.959032
81	1978574076	admin_login	\N	2025-07-08 13:07:53.454946
82	1978574076	admin_login	\N	2025-07-08 13:08:36.501612
83	1978574076	admin_login	\N	2025-07-08 13:09:48.835005
84	1978574076	admin_login	\N	2025-07-08 13:14:57.968055
85	1978574076	admin_login	\N	2025-07-08 13:25:39.5384
86	1978574076	admin_login	\N	2025-07-08 13:28:08.803667
87	1978574076	admin_login	\N	2025-07-08 13:31:12.935969
88	1978574076	admin_login	\N	2025-07-08 13:32:08.32494
89	1978574076	admin_login	\N	2025-07-08 13:32:31.758829
90	1978574076	admin_login	\N	2025-07-08 13:33:00.637286
91	1978574076	admin_login	\N	2025-07-08 13:36:43.397954
92	1978574076	change_language	{"new_language": "uz"}	2025-07-08 13:36:49.666409
93	1978574076	admin_login	\N	2025-07-08 13:36:52.497249
94	1978574076	change_language	{"new_language": "ru"}	2025-07-08 13:36:56.769848
95	1978574076	admin_login	\N	2025-07-08 13:37:09.178304
96	1978574076	admin_login	\N	2025-07-08 13:39:39.260178
97	1978574076	change_language	{"new_language": "uz"}	2025-07-08 13:39:46.001298
98	1978574076	admin_login	\N	2025-07-08 13:40:28.529205
99	1978574076	admin_login	\N	2025-07-08 13:47:06.332594
100	1978574076	admin_login	\N	2025-07-08 13:55:04.993224
101	1978574076	admin_login	\N	2025-07-08 14:09:15.738524
102	1978574076	admin_login	\N	2025-07-08 14:16:49.700157
103	1978574076	admin_login	\N	2025-07-08 14:17:09.600941
104	1978574076	admin_login	\N	2025-07-08 14:23:28.028271
105	1978574076	admin_login	\N	2025-07-08 14:49:25.427747
106	1978574076	admin_login	\N	2025-07-08 14:50:07.255447
107	1978574076	admin_login	\N	2025-07-08 14:50:36.232393
108	1978574076	admin_login	\N	2025-07-08 14:51:12.378751
109	1978574076	admin_login	\N	2025-07-08 14:51:32.141119
110	1978574076	admin_login	\N	2025-07-08 14:52:24.988126
111	1978574076	admin_login	\N	2025-07-08 14:54:34.138476
112	1978574076	admin_login	\N	2025-07-08 14:55:48.287378
113	1978574076	admin_login	\N	2025-07-08 14:56:13.518977
114	1978574076	admin_login	\N	2025-07-08 15:10:03.829678
115	1978574076	admin_login	\N	2025-07-08 15:11:46.575386
116	1978574076	admin_login	\N	2025-07-08 15:13:01.867805
117	1978574076	admin_login	\N	2025-07-08 15:13:37.732525
118	1978574076	admin_login	\N	2025-07-08 15:14:49.225561
119	1978574076	admin_login	\N	2025-07-08 15:16:13.827811
120	1978574076	admin_login	\N	2025-07-08 15:17:04.361831
121	1978574076	admin_login	\N	2025-07-08 15:17:33.263884
122	1978574076	admin_login	\N	2025-07-08 15:18:11.377651
123	1978574076	admin_login	\N	2025-07-08 15:18:55.014796
124	1978574076	admin_login	\N	2025-07-08 15:19:29.493858
125	1978574076	admin_login	\N	2025-07-08 15:20:09.594689
126	1978574076	admin_login	\N	2025-07-08 15:20:44.925276
127	1978574076	admin_login	\N	2025-07-08 15:32:23.2261
128	1978574076	admin_login	\N	2025-07-08 15:36:28.605069
129	1978574076	admin_login	\N	2025-07-08 15:36:40.301698
130	1978574076	admin_login	\N	2025-07-08 15:38:59.247687
131	1978574076	admin_login	\N	2025-07-08 15:42:06.652304
132	1978574076	admin_login	\N	2025-07-08 15:44:03.432083
133	1978574076	admin_login	\N	2025-07-08 15:47:17.865892
134	1978574076	admin_login	\N	2025-07-08 15:53:47.913545
135	1978574076	admin_login	\N	2025-07-08 15:54:30.561486
136	1978574076	role_change	{"user_id": 5955605892, "new_role": "manager", "old_role": "client"}	2025-07-08 15:55:46.930906
137	1978574076	admin_login	\N	2025-07-09 10:50:31.897927
138	1978574076	admin_login	\N	2025-07-09 10:51:18.278991
139	1978574076	admin_login	\N	2025-07-09 10:52:27.426829
140	1978574076	admin_login	\N	2025-07-09 10:52:40.271897
141	1978574076	admin_login	\N	2025-07-09 10:58:12.96926
142	1978574076	admin_login	\N	2025-07-09 11:00:40.020464
143	1978574076	role_change	{"user_id": 7793341014, "new_role": "technician", "old_role": "client"}	2025-07-09 11:00:51.892474
144	1978574076	role_change	{"user_id": 7793341014, "new_role": "controller", "old_role": "technician"}	2025-07-09 12:00:15.67046
145	1978574076	role_change	{"user_id": 7793341014, "new_role": "warehouse", "old_role": "controller"}	2025-07-09 13:34:13.694348
146	1978574076	role_change	{"user_id": 7793341014, "new_role": "controller", "old_role": "warehouse"}	2025-07-09 15:47:48.751132
147	1978574076	role_change	{"user_id": 7793341014, "new_role": "controller", "old_role": "controller"}	2025-07-09 15:47:51.111809
148	1978574076	role_change	{"user_id": 7793341014, "new_role": "call_center", "old_role": "controller"}	2025-07-09 15:50:55.080989
149	1978574076	admin_login	\N	2025-07-10 09:42:03.750602
150	1978574076	admin_login	\N	2025-07-10 09:43:12.798678
151	1978574076	admin_login	\N	2025-07-10 09:44:32.931551
152	1978574076	admin_login	\N	2025-07-10 09:46:02.850072
153	1978574076	admin_login	\N	2025-07-10 09:47:35.78965
154	1978574076	role_change	{"user_id": 5955605892, "new_role": "controller", "old_role": "manager"}	2025-07-10 09:48:48.943019
155	1978574076	role_change	{"user_id": 5955605892, "new_role": "controller", "old_role": "controller"}	2025-07-10 09:49:10.162338
156	1978574076	admin_login	\N	2025-07-10 09:49:22.864251
157	1978574076	role_change	{"user_id": 5955605892, "new_role": "warehouse", "old_role": "controller"}	2025-07-10 10:13:38.935575
158	1978574076	role_change	{"user_id": 5955605892, "new_role": "technician", "old_role": "warehouse"}	2025-07-10 10:58:47.401021
159	1978574076	admin_login	\N	2025-07-10 15:34:30.348395
160	1978574076	role_change	{"user_id": 7793341014, "new_role": "controller", "old_role": "call_center"}	2025-07-10 15:35:09.672709
161	1978574076	role_change	{"user_id": 5955605892, "new_role": "manager", "old_role": "technician"}	2025-07-10 15:35:38.61177
162	1978574076	admin_login	\N	2025-07-10 16:29:41.358828
163	1978574076	admin_login	\N	2025-07-10 17:47:42.219656
164	1978574076	role_change	{"user_id": 5955605892, "new_role": "warehouse", "old_role": "manager"}	2025-07-10 17:47:58.982392
165	1978574076	role_change	{"user_id": 5955605892, "new_role": "technician", "old_role": "warehouse"}	2025-07-10 17:57:30.143585
166	1978574076	role_change	{"user_id": 5955605892, "new_role": "call_center", "old_role": "technician"}	2025-07-10 17:59:11.944118
167	1978574076	role_change	{"user_id": 5955605892, "new_role": "manager", "old_role": "call_center"}	2025-07-11 11:44:01.79564
168	1978574076	admin_login	\N	2025-07-15 10:54:31.356504
169	1978574076	admin_login	\N	2025-07-15 10:57:30.967253
170	1978574076	admin_login	\N	2025-07-15 11:05:38.398757
171	1978574076	admin_login	\N	2025-07-15 11:05:42.270703
172	1978574076	admin_login	\N	2025-07-15 11:09:48.466179
173	1978574076	admin_login	\N	2025-07-15 11:14:39.854404
174	1978574076	role_change	{"user_id": 5955605892, "new_role": "manager", "old_role": "client"}	2025-07-15 11:14:54.078841
175	1978574076	role_change	{"user_id": 7793341014, "new_role": "junior_manager", "old_role": "client"}	2025-07-15 11:15:18.950885
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
-- Data for Name: client_selection_data; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.client_selection_data (id, search_method, search_value, client_id, new_client_data, verified, created_at) FROM stdin;
\.


--
-- Data for Name: equipment_requests; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.equipment_requests (id, technician_id, equipment_type, quantity, reason, status, approved_by, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: error_records; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.error_records (id, category, severity, message, details, context, stack_trace, occurred_at, resolved_at, resolution_notes, retry_count, max_retries) FROM stdin;
\.


--
-- Data for Name: feedback; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.feedback (id, zayavka_id, user_id, rating, comment, created_at) FROM stdin;
\.


--
-- Data for Name: help_requests; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.help_requests (id, technician_id, help_type, description, status, priority, assigned_to, resolution, created_at, updated_at, resolved_at) FROM stdin;
1	14	equipment	33	pending	medium	\N	\N	2025-07-10 11:00:15.450163+05	2025-07-10 11:00:15.450163+05	\N
\.


--
-- Data for Name: inventory_transactions; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.inventory_transactions (id, request_id, equipment_id, quantity_used, transaction_type, created_at, created_by) FROM stdin;
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
-- Data for Name: messages; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.messages (id, zayavka_id, sender_id, recipient_role, recipient_user_id, message_text, message_type, is_read, is_urgent, created_at, updated_at) FROM stdin;
\.


--
-- Data for Name: notification_queue; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.notification_queue (id, user_id, message, zayavka_id, notification_type, sent, created_at) FROM stdin;
\.


--
-- Data for Name: notification_retry_queue; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.notification_retry_queue (id, role, request_id, workflow_type, retry_count, max_retries, next_retry_at, last_error, created_at, status) FROM stdin;
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

COPY public.notifications (id, user_id, zayavka_id, message, sent_at, channel, title, notification_type, related_id, related_type, is_read, read_at, created_at) FROM stdin;
\.


--
-- Data for Name: pending_notifications; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.pending_notifications (id, user_id, request_id, workflow_type, role, created_at, is_handled, handled_at) FROM stdin;
\.


--
-- Data for Name: role_change_logs; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.role_change_logs (id, user_telegram_id, old_role, new_role, changed_by, changed_at) FROM stdin;
1	5955605892	manager	manager	1978574076	2025-07-07 16:10:04.234025+05
2	5955605892	manager	warehouse	1978574076	2025-07-08 12:00:07.47226+05
3	5955605892	warehouse	warehouse	1978574076	2025-07-08 12:00:07.474081+05
4	5955605892	warehouse	manager	1978574076	2025-07-08 12:12:47.95771+05
5	5955605892	manager	manager	1978574076	2025-07-08 12:12:47.959956+05
6	5955605892	manager	client	1978574076	2025-07-08 13:15:07.627978+05
7	5955605892	client	blocked	1978574076	2025-07-08 13:15:17.173637+05
8	5955605892	blocked	client	1978574076	2025-07-08 15:44:13.80648+05
9	5955605892	client	manager	1978574076	2025-07-08 15:55:46.929699+05
10	5955605892	manager	manager	1978574076	2025-07-08 15:55:46.93429+05
11	7793341014	client	technician	1978574076	2025-07-09 11:00:51.888992+05
12	7793341014	technician	technician	1978574076	2025-07-09 11:00:51.893527+05
13	7793341014	technician	controller	1978574076	2025-07-09 12:00:15.668159+05
14	7793341014	controller	controller	1978574076	2025-07-09 12:00:15.673354+05
15	7793341014	controller	warehouse	1978574076	2025-07-09 13:34:13.69262+05
16	7793341014	warehouse	warehouse	1978574076	2025-07-09 13:34:13.696859+05
17	7793341014	warehouse	controller	1978574076	2025-07-09 15:47:48.746958+05
18	7793341014	controller	controller	1978574076	2025-07-09 15:47:48.754824+05
19	7793341014	controller	controller	1978574076	2025-07-09 15:47:51.111151+05
20	7793341014	controller	controller	1978574076	2025-07-09 15:47:51.112941+05
21	7793341014	controller	call_center	1978574076	2025-07-09 15:50:55.080346+05
22	7793341014	call_center	call_center	1978574076	2025-07-09 15:50:55.082103+05
23	5955605892	manager	controller	1978574076	2025-07-10 09:48:48.941989+05
24	5955605892	controller	controller	1978574076	2025-07-10 09:48:48.94488+05
25	5955605892	controller	controller	1978574076	2025-07-10 09:49:10.161647+05
26	5955605892	controller	controller	1978574076	2025-07-10 09:49:10.163497+05
27	5955605892	controller	warehouse	1978574076	2025-07-10 10:13:38.934545+05
28	5955605892	warehouse	warehouse	1978574076	2025-07-10 10:13:38.937204+05
29	5955605892	warehouse	technician	1978574076	2025-07-10 10:58:47.399934+05
30	5955605892	technician	technician	1978574076	2025-07-10 10:58:47.403096+05
31	7793341014	call_center	controller	1978574076	2025-07-10 15:35:09.671419+05
32	7793341014	controller	controller	1978574076	2025-07-10 15:35:09.673688+05
33	5955605892	technician	manager	1978574076	2025-07-10 15:35:38.611216+05
34	5955605892	manager	manager	1978574076	2025-07-10 15:35:38.612791+05
35	5955605892	manager	warehouse	1978574076	2025-07-10 17:47:58.981183+05
36	5955605892	warehouse	warehouse	1978574076	2025-07-10 17:47:58.983089+05
37	5955605892	warehouse	technician	1978574076	2025-07-10 17:57:30.142477+05
38	5955605892	technician	technician	1978574076	2025-07-10 17:57:30.144625+05
39	5955605892	technician	call_center	1978574076	2025-07-10 17:59:11.943621+05
40	5955605892	call_center	call_center	1978574076	2025-07-10 17:59:11.944862+05
41	5955605892	call_center	manager	1978574076	2025-07-11 11:44:01.794096+05
42	5955605892	manager	manager	1978574076	2025-07-11 11:44:01.799603+05
43	5955605892	client	manager	1978574076	2025-07-15 11:14:54.075491+05
44	5955605892	manager	manager	1978574076	2025-07-15 11:14:54.080579+05
45	7793341014	client	junior_manager	1978574076	2025-07-15 11:15:18.950429+05
46	7793341014	junior_manager	junior_manager	1978574076	2025-07-15 11:15:18.951858+05
\.


--
-- Data for Name: service_requests; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.service_requests (id, workflow_type, client_id, role_current, current_status, created_at, updated_at, priority, description, location, contact_info, state_data, equipment_used, inventory_updated, completion_rating, feedback_comments, created_by_staff, staff_creator_id, staff_creator_role, creation_source, client_notified_at) FROM stdin;
\.


--
-- Data for Name: solutions; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.solutions (id, zayavka_id, instander_id, solution_text, media, created_at) FROM stdin;
\.


--
-- Data for Name: staff_application_audit; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.staff_application_audit (id, application_id, creator_id, creator_role, client_id, application_type, creation_timestamp, client_notified, client_notified_at, workflow_initiated, workflow_initiated_at, metadata, ip_address, user_agent, session_id) FROM stdin;
\.


--
-- Data for Name: state_transitions; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.state_transitions (id, request_id, from_role, to_role, action, actor_id, transition_data, comments, created_at) FROM stdin;
\.


--
-- Data for Name: status_logs; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.status_logs (id, zayavka_id, old_status, new_status, changed_by, changed_at) FROM stdin;
1	1	new	in_progress	14	2025-07-09 09:55:56.019108+05
2	1	in_progress	in_progress	14	2025-07-09 10:53:35.602842+05
3	1	in_progress	new	14	2025-07-09 10:53:36.966159+05
4	1	new	completed	14	2025-07-09 10:53:39.664608+05
5	1	completed	in_progress	14	2025-07-09 10:53:40.557332+05
6	1	in_progress	new	14	2025-07-09 10:53:41.005302+05
7	2	new	in_progress	14	2025-07-10 17:07:35.26407+05
\.


--
-- Data for Name: system_health_snapshots; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.system_health_snapshots (id, snapshot_time, active_requests, pending_notifications, active_transactions, error_count_24h, inventory_discrepancies, stuck_workflows, system_status, metrics, notes) FROM stdin;
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
-- Data for Name: transaction_log; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.transaction_log (id, transaction_id, operation_type, operation_data, rollback_data, status, started_at, completed_at, error_message) FROM stdin;
\.


--
-- Data for Name: user_action_logs; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.user_action_logs (id, user_telegram_id, action, performed_by, performed_at) FROM stdin;
1	5955605892	unblocked	1978574076	2025-07-08 13:09:56.829889
2	5955605892	blocked	1978574076	2025-07-08 13:09:59.397903
3	5955605892	unblocked	1978574076	2025-07-08 13:15:07.630208
4	5955605892	blocked	1978574076	2025-07-08 13:15:17.175909
5	5955605892	unblocked	1978574076	2025-07-08 15:44:13.809615
\.


--
-- Data for Name: users; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.users (id, telegram_id, full_name, username, phone_number, role, abonent_id, language, is_active, address, created_at, updated_at, permissions) FROM stdin;
3	8188731606	Ism	bratuuha	998881249327	client	\N	uz	t	\N	2025-07-15 11:04:57.541899+05	2025-07-15 11:05:03.224187+05	\N
1	5955605892	Yoqubjonova Gulsara	gulsara_yakubjanova	998900047294	manager	\N	uz	t	\N	2025-07-15 10:59:12.016054+05	2025-07-15 11:14:54.080249+05	\N
2	7793341014	Bakirali	bakiralizokirov	998937490211	junior_manager	\N	uz	t	\N	2025-07-15 11:03:48.57779+05	2025-07-15 11:15:18.951515+05	\N
\.


--
-- Data for Name: zayavka_status_history; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.zayavka_status_history (id, zayavka_id, old_status, new_status, changed_by, changed_by_role, changed_at, comment) FROM stdin;
\.


--
-- Data for Name: zayavka_transfers; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.zayavka_transfers (id, zayavka_id, from_technician_id, to_technician_id, transferred_by, reason, transferred_at) FROM stdin;
\.


--
-- Data for Name: zayavki; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.zayavki (id, public_id, zayavka_type, user_id, description, status, role_current, current_user_id, address, latitude, longitude, abonent_id, phone_number, priority, created_by, created_by_role, assigned_at, completed_at, closed_at, created_at, updated_at, assigned_to) FROM stdin;
\.


--
-- Name: access_control_logs_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.access_control_logs_id_seq', 1, false);


--
-- Name: admin_action_logs_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.admin_action_logs_id_seq', 175, true);


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
-- Name: client_selection_data_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.client_selection_data_id_seq', 1, false);


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

SELECT pg_catalog.setval('public.help_requests_id_seq', 1, true);


--
-- Name: inventory_transactions_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.inventory_transactions_id_seq', 1, false);


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
-- Name: messages_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.messages_id_seq', 1, false);


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
-- Name: role_change_logs_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.role_change_logs_id_seq', 46, true);


--
-- Name: solutions_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.solutions_id_seq', 1, false);


--
-- Name: staff_application_audit_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.staff_application_audit_id_seq', 1, true);


--
-- Name: state_transitions_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.state_transitions_id_seq', 1, false);


--
-- Name: status_logs_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.status_logs_id_seq', 7, true);


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
-- Name: user_action_logs_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.user_action_logs_id_seq', 5, true);


--
-- Name: users_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.users_id_seq', 3, true);


--
-- Name: zayavka_status_history_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.zayavka_status_history_id_seq', 1, false);


--
-- Name: zayavka_transfers_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.zayavka_transfers_id_seq', 1, false);


--
-- Name: zayavki_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.zayavki_id_seq', 1, false);


--
-- Name: access_control_logs access_control_logs_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.access_control_logs
    ADD CONSTRAINT access_control_logs_pkey PRIMARY KEY (id);


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
-- Name: client_selection_data client_selection_data_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.client_selection_data
    ADD CONSTRAINT client_selection_data_pkey PRIMARY KEY (id);


--
-- Name: equipment_requests equipment_requests_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.equipment_requests
    ADD CONSTRAINT equipment_requests_pkey PRIMARY KEY (id);


--
-- Name: error_records error_records_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.error_records
    ADD CONSTRAINT error_records_pkey PRIMARY KEY (id);


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
-- Name: inventory_transactions inventory_transactions_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.inventory_transactions
    ADD CONSTRAINT inventory_transactions_pkey PRIMARY KEY (id);


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
-- Name: messages messages_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.messages
    ADD CONSTRAINT messages_pkey PRIMARY KEY (id);


--
-- Name: notification_queue notification_queue_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.notification_queue
    ADD CONSTRAINT notification_queue_pkey PRIMARY KEY (id);


--
-- Name: notification_retry_queue notification_retry_queue_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.notification_retry_queue
    ADD CONSTRAINT notification_retry_queue_pkey PRIMARY KEY (id);


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
-- Name: pending_notifications pending_notifications_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.pending_notifications
    ADD CONSTRAINT pending_notifications_pkey PRIMARY KEY (id);


--
-- Name: role_change_logs role_change_logs_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.role_change_logs
    ADD CONSTRAINT role_change_logs_pkey PRIMARY KEY (id);


--
-- Name: service_requests service_requests_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.service_requests
    ADD CONSTRAINT service_requests_pkey PRIMARY KEY (id);


--
-- Name: solutions solutions_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.solutions
    ADD CONSTRAINT solutions_pkey PRIMARY KEY (id);


--
-- Name: staff_application_audit staff_application_audit_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.staff_application_audit
    ADD CONSTRAINT staff_application_audit_pkey PRIMARY KEY (id);


--
-- Name: state_transitions state_transitions_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.state_transitions
    ADD CONSTRAINT state_transitions_pkey PRIMARY KEY (id);


--
-- Name: status_logs status_logs_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.status_logs
    ADD CONSTRAINT status_logs_pkey PRIMARY KEY (id);


--
-- Name: system_health_snapshots system_health_snapshots_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.system_health_snapshots
    ADD CONSTRAINT system_health_snapshots_pkey PRIMARY KEY (id);


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
-- Name: transaction_log transaction_log_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.transaction_log
    ADD CONSTRAINT transaction_log_pkey PRIMARY KEY (id);


--
-- Name: user_action_logs user_action_logs_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.user_action_logs
    ADD CONSTRAINT user_action_logs_pkey PRIMARY KEY (id);


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
-- Name: zayavka_status_history zayavka_status_history_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.zayavka_status_history
    ADD CONSTRAINT zayavka_status_history_pkey PRIMARY KEY (id);


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
-- Name: zayavki zayavki_public_id_key; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.zayavki
    ADD CONSTRAINT zayavki_public_id_key UNIQUE (public_id);


--
-- Name: idx_access_logs_action; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_access_logs_action ON public.access_control_logs USING btree (action);


--
-- Name: idx_access_logs_failed_attempts; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_access_logs_failed_attempts ON public.access_control_logs USING btree (user_id, "timestamp") WHERE (granted = false);


--
-- Name: idx_access_logs_granted; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_access_logs_granted ON public.access_control_logs USING btree (granted);


--
-- Name: idx_access_logs_resource; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_access_logs_resource ON public.access_control_logs USING btree (resource);


--
-- Name: idx_access_logs_resource_granted; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_access_logs_resource_granted ON public.access_control_logs USING btree (resource, granted, "timestamp");


--
-- Name: idx_access_logs_timestamp; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_access_logs_timestamp ON public.access_control_logs USING btree ("timestamp");


--
-- Name: idx_access_logs_user_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_access_logs_user_id ON public.access_control_logs USING btree (user_id);


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
-- Name: idx_client_selection_client_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_client_selection_client_id ON public.client_selection_data USING btree (client_id);


--
-- Name: idx_client_selection_created_at; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_client_selection_created_at ON public.client_selection_data USING btree (created_at);


--
-- Name: idx_client_selection_data_client_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_client_selection_data_client_id ON public.client_selection_data USING btree (client_id);


--
-- Name: idx_client_selection_data_created_at; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_client_selection_data_created_at ON public.client_selection_data USING btree (created_at);


--
-- Name: idx_client_selection_data_search_method; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_client_selection_data_search_method ON public.client_selection_data USING btree (search_method);


--
-- Name: idx_client_selection_method; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_client_selection_method ON public.client_selection_data USING btree (search_method);


--
-- Name: idx_error_records_category; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_error_records_category ON public.error_records USING btree (category);


--
-- Name: idx_error_records_occurred_at; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_error_records_occurred_at ON public.error_records USING btree (occurred_at);


--
-- Name: idx_error_records_resolved_at; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_error_records_resolved_at ON public.error_records USING btree (resolved_at);


--
-- Name: idx_error_records_severity; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_error_records_severity ON public.error_records USING btree (severity);


--
-- Name: idx_feedback_rating_created; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_feedback_rating_created ON public.feedback USING btree (rating, created_at DESC);


--
-- Name: idx_help_requests_status_priority; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_help_requests_status_priority ON public.help_requests USING btree (status, priority, created_at DESC);


--
-- Name: idx_help_requests_technician_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_help_requests_technician_id ON public.help_requests USING btree (technician_id);


--
-- Name: idx_inventory_transactions_created_at; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_inventory_transactions_created_at ON public.inventory_transactions USING btree (created_at DESC);


--
-- Name: idx_inventory_transactions_equipment_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_inventory_transactions_equipment_id ON public.inventory_transactions USING btree (equipment_id);


--
-- Name: idx_inventory_transactions_request_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_inventory_transactions_request_id ON public.inventory_transactions USING btree (request_id);


--
-- Name: idx_issued_items_material_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_issued_items_material_id ON public.issued_items USING btree (material_id);


--
-- Name: idx_issued_items_zayavka_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_issued_items_zayavka_id ON public.issued_items USING btree (zayavka_id);


--
-- Name: idx_materials_active_category; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_materials_active_category ON public.materials USING btree (category, is_active) WHERE (is_active = true);


--
-- Name: idx_materials_category; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_materials_category ON public.materials USING btree (category);


--
-- Name: idx_messages_recipient_role; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_messages_recipient_role ON public.messages USING btree (recipient_role);


--
-- Name: idx_messages_recipient_user_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_messages_recipient_user_id ON public.messages USING btree (recipient_user_id);


--
-- Name: idx_notification_queue_sent; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_notification_queue_sent ON public.notification_queue USING btree (sent);


--
-- Name: idx_notification_retry_queue_next_retry_at; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_notification_retry_queue_next_retry_at ON public.notification_retry_queue USING btree (next_retry_at);


--
-- Name: idx_notification_retry_queue_request_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_notification_retry_queue_request_id ON public.notification_retry_queue USING btree (request_id);


--
-- Name: idx_notification_retry_queue_status; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_notification_retry_queue_status ON public.notification_retry_queue USING btree (status);


--
-- Name: idx_notifications_created_at; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_notifications_created_at ON public.notifications USING btree (created_at DESC);


--
-- Name: idx_notifications_related_type_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_notifications_related_type_id ON public.notifications USING btree (related_type, related_id);


--
-- Name: idx_notifications_user_id_unread; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_notifications_user_id_unread ON public.notifications USING btree (user_id) WHERE (is_read = false);


--
-- Name: idx_pending_notifications_is_handled; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_pending_notifications_is_handled ON public.pending_notifications USING btree (is_handled);


--
-- Name: idx_pending_notifications_request_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_pending_notifications_request_id ON public.pending_notifications USING btree (request_id);


--
-- Name: idx_pending_notifications_user_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_pending_notifications_user_id ON public.pending_notifications USING btree (user_id);


--
-- Name: idx_role_change_logs_user_telegram_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_role_change_logs_user_telegram_id ON public.role_change_logs USING btree (user_telegram_id);


--
-- Name: idx_service_requests_client_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_service_requests_client_id ON public.service_requests USING btree (client_id);


--
-- Name: idx_service_requests_created_at; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_service_requests_created_at ON public.service_requests USING btree (created_at DESC);


--
-- Name: idx_service_requests_created_by_staff; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_service_requests_created_by_staff ON public.service_requests USING btree (created_by_staff);


--
-- Name: idx_service_requests_creation_source; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_service_requests_creation_source ON public.service_requests USING btree (creation_source);


--
-- Name: idx_service_requests_current_status; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_service_requests_current_status ON public.service_requests USING btree (current_status);


--
-- Name: idx_service_requests_role_current; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_service_requests_role_current ON public.service_requests USING btree (role_current);


--
-- Name: idx_service_requests_staff_creator_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_service_requests_staff_creator_id ON public.service_requests USING btree (staff_creator_id);


--
-- Name: idx_service_requests_status_role; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_service_requests_status_role ON public.service_requests USING btree (current_status, role_current);


--
-- Name: idx_service_requests_workflow_type; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_service_requests_workflow_type ON public.service_requests USING btree (workflow_type);


--
-- Name: idx_solutions_zayavka_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_solutions_zayavka_id ON public.solutions USING btree (zayavka_id);


--
-- Name: idx_staff_application_audit_application_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_staff_application_audit_application_id ON public.staff_application_audit USING btree (application_id);


--
-- Name: idx_staff_application_audit_client_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_staff_application_audit_client_id ON public.staff_application_audit USING btree (client_id);


--
-- Name: idx_staff_application_audit_creation_timestamp; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_staff_application_audit_creation_timestamp ON public.staff_application_audit USING btree (creation_timestamp);


--
-- Name: idx_staff_application_audit_creator_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_staff_application_audit_creator_id ON public.staff_application_audit USING btree (creator_id);


--
-- Name: idx_staff_audit_application_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_staff_audit_application_id ON public.staff_application_audit USING btree (application_id);


--
-- Name: idx_staff_audit_application_type; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_staff_audit_application_type ON public.staff_application_audit USING btree (application_type);


--
-- Name: idx_staff_audit_client_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_staff_audit_client_id ON public.staff_application_audit USING btree (client_id);


--
-- Name: idx_staff_audit_creation_timestamp; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_staff_audit_creation_timestamp ON public.staff_application_audit USING btree (creation_timestamp);


--
-- Name: idx_staff_audit_creator_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_staff_audit_creator_id ON public.staff_application_audit USING btree (creator_id);


--
-- Name: idx_staff_audit_creator_role; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_staff_audit_creator_role ON public.staff_application_audit USING btree (creator_role);


--
-- Name: idx_staff_audit_creator_timestamp; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_staff_audit_creator_timestamp ON public.staff_application_audit USING btree (creator_id, creation_timestamp);


--
-- Name: idx_staff_audit_role_timestamp; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_staff_audit_role_timestamp ON public.staff_application_audit USING btree (creator_role, creation_timestamp);


--
-- Name: idx_staff_audit_session_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_staff_audit_session_id ON public.staff_application_audit USING btree (session_id);


--
-- Name: idx_staff_audit_type_timestamp; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_staff_audit_type_timestamp ON public.staff_application_audit USING btree (application_type, creation_timestamp);


--
-- Name: idx_state_transitions_created_at; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_state_transitions_created_at ON public.state_transitions USING btree (created_at DESC);


--
-- Name: idx_state_transitions_request_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_state_transitions_request_id ON public.state_transitions USING btree (request_id);


--
-- Name: idx_state_transitions_to_role; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_state_transitions_to_role ON public.state_transitions USING btree (to_role);


--
-- Name: idx_status_logs_zayavka_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_status_logs_zayavka_id ON public.status_logs USING btree (zayavka_id);


--
-- Name: idx_system_health_snapshots_snapshot_time; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_system_health_snapshots_snapshot_time ON public.system_health_snapshots USING btree (snapshot_time);


--
-- Name: idx_system_health_snapshots_system_status; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_system_health_snapshots_system_status ON public.system_health_snapshots USING btree (system_status);


--
-- Name: idx_technician_workload_technician; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_technician_workload_technician ON public.technician_workload USING btree (technician_id);


--
-- Name: idx_transaction_log_started_at; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_transaction_log_started_at ON public.transaction_log USING btree (started_at);


--
-- Name: idx_transaction_log_status; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_transaction_log_status ON public.transaction_log USING btree (status);


--
-- Name: idx_transaction_log_transaction_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_transaction_log_transaction_id ON public.transaction_log USING btree (transaction_id);


--
-- Name: idx_users_role; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_users_role ON public.users USING btree (role);


--
-- Name: idx_users_role_active; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_users_role_active ON public.users USING btree (role) WHERE (is_active = true);


--
-- Name: idx_users_telegram_id_role; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_users_telegram_id_role ON public.users USING btree (telegram_id, role);


--
-- Name: idx_zayavka_status_history_zayavka_id; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_zayavka_status_history_zayavka_id ON public.zayavka_status_history USING btree (zayavka_id);


--
-- Name: idx_zayavki_created_priority; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_zayavki_created_priority ON public.zayavki USING btree (created_at DESC, priority);


--
-- Name: idx_zayavki_current_role; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_zayavki_current_role ON public.zayavki USING btree (role_current);


--
-- Name: idx_zayavki_role_current_status; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_zayavki_role_current_status ON public.zayavki USING btree (role_current, status);


--
-- Name: idx_zayavki_status; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_zayavki_status ON public.zayavki USING btree (status);


--
-- Name: idx_zayavki_status_assigned; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_zayavki_status_assigned ON public.zayavki USING btree (status, assigned_to);


--
-- Name: idx_zayavki_user_status; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_zayavki_user_status ON public.zayavki USING btree (user_id, status);


--
-- Name: client_selection_data update_client_selection_updated_at; Type: TRIGGER; Schema: public; Owner: postgres
--

CREATE TRIGGER update_client_selection_updated_at BEFORE UPDATE ON public.client_selection_data FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();


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
-- Name: messages update_messages_updated_at; Type: TRIGGER; Schema: public; Owner: postgres
--

CREATE TRIGGER update_messages_updated_at BEFORE UPDATE ON public.messages FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();


--
-- Name: staff_application_audit update_staff_audit_updated_at; Type: TRIGGER; Schema: public; Owner: postgres
--

CREATE TRIGGER update_staff_audit_updated_at BEFORE UPDATE ON public.staff_application_audit FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();


--
-- Name: users update_users_updated_at; Type: TRIGGER; Schema: public; Owner: postgres
--

CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON public.users FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();


--
-- Name: zayavki update_zayavki_updated_at; Type: TRIGGER; Schema: public; Owner: postgres
--

CREATE TRIGGER update_zayavki_updated_at BEFORE UPDATE ON public.zayavki FOR EACH ROW EXECUTE FUNCTION public.update_updated_at_column();


--
-- Name: chat_messages chat_messages_session_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.chat_messages
    ADD CONSTRAINT chat_messages_session_id_fkey FOREIGN KEY (session_id) REFERENCES public.chat_sessions(id) ON DELETE CASCADE;


--
-- Name: client_selection_data client_selection_data_client_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.client_selection_data
    ADD CONSTRAINT client_selection_data_client_id_fkey FOREIGN KEY (client_id) REFERENCES public.users(id);


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
-- Name: access_control_logs fk_access_logs_user_id; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.access_control_logs
    ADD CONSTRAINT fk_access_logs_user_id FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: client_selection_data fk_client_selection_client; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.client_selection_data
    ADD CONSTRAINT fk_client_selection_client FOREIGN KEY (client_id) REFERENCES public.users(id) ON DELETE SET NULL;


--
-- Name: service_requests fk_service_requests_staff_creator; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.service_requests
    ADD CONSTRAINT fk_service_requests_staff_creator FOREIGN KEY (staff_creator_id) REFERENCES public.users(id);


--
-- Name: staff_application_audit fk_staff_audit_application; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.staff_application_audit
    ADD CONSTRAINT fk_staff_audit_application FOREIGN KEY (application_id) REFERENCES public.service_requests(id) ON DELETE CASCADE;


--
-- Name: staff_application_audit fk_staff_audit_client; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.staff_application_audit
    ADD CONSTRAINT fk_staff_audit_client FOREIGN KEY (client_id) REFERENCES public.users(id) ON DELETE SET NULL;


--
-- Name: staff_application_audit fk_staff_audit_creator; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.staff_application_audit
    ADD CONSTRAINT fk_staff_audit_creator FOREIGN KEY (creator_id) REFERENCES public.users(id) ON DELETE SET NULL;


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
-- Name: messages messages_recipient_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.messages
    ADD CONSTRAINT messages_recipient_user_id_fkey FOREIGN KEY (recipient_user_id) REFERENCES public.users(id) ON DELETE SET NULL;


--
-- Name: messages messages_sender_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.messages
    ADD CONSTRAINT messages_sender_id_fkey FOREIGN KEY (sender_id) REFERENCES public.users(id) ON DELETE SET NULL;


--
-- Name: messages messages_zayavka_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.messages
    ADD CONSTRAINT messages_zayavka_id_fkey FOREIGN KEY (zayavka_id) REFERENCES public.zayavki(id) ON DELETE CASCADE;


--
-- Name: pending_notifications pending_notifications_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.pending_notifications
    ADD CONSTRAINT pending_notifications_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- Name: service_requests service_requests_staff_creator_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.service_requests
    ADD CONSTRAINT service_requests_staff_creator_id_fkey FOREIGN KEY (staff_creator_id) REFERENCES public.users(id);


--
-- Name: staff_application_audit staff_application_audit_application_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.staff_application_audit
    ADD CONSTRAINT staff_application_audit_application_id_fkey FOREIGN KEY (application_id) REFERENCES public.service_requests(id) ON DELETE CASCADE;


--
-- Name: staff_application_audit staff_application_audit_client_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.staff_application_audit
    ADD CONSTRAINT staff_application_audit_client_id_fkey FOREIGN KEY (client_id) REFERENCES public.users(id);


--
-- Name: staff_application_audit staff_application_audit_creator_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.staff_application_audit
    ADD CONSTRAINT staff_application_audit_creator_id_fkey FOREIGN KEY (creator_id) REFERENCES public.users(id);


--
-- Name: zayavka_status_history zayavka_status_history_changed_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.zayavka_status_history
    ADD CONSTRAINT zayavka_status_history_changed_by_fkey FOREIGN KEY (changed_by) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- Name: zayavka_status_history zayavka_status_history_zayavka_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.zayavka_status_history
    ADD CONSTRAINT zayavka_status_history_zayavka_id_fkey FOREIGN KEY (zayavka_id) REFERENCES public.zayavki(id) ON DELETE CASCADE;


--
-- Name: zayavki zayavki_assigned_to_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.zayavki
    ADD CONSTRAINT zayavki_assigned_to_fkey FOREIGN KEY (assigned_to) REFERENCES public.users(id);


--
-- Name: zayavki zayavki_created_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.zayavki
    ADD CONSTRAINT zayavki_created_by_fkey FOREIGN KEY (created_by) REFERENCES public.users(id) ON DELETE SET NULL;


--
-- Name: zayavki zayavki_current_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.zayavki
    ADD CONSTRAINT zayavki_current_user_id_fkey FOREIGN KEY (current_user_id) REFERENCES public.users(id) ON DELETE SET NULL;


--
-- Name: zayavki zayavki_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.zayavki
    ADD CONSTRAINT zayavki_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id) ON DELETE CASCADE;


--
-- PostgreSQL database dump complete
--

