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

SET default_tablespace = '';

SET default_table_access_method = heap;

--
-- Name: feedback; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.feedback (
    id integer NOT NULL,
    zayavka_id integer,
    user_id bigint,
    rating integer,
    comment text,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
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
-- Name: issued_items; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.issued_items (
    id integer NOT NULL,
    zayavka_id integer,
    material_id integer,
    quantity integer NOT NULL,
    issued_by bigint,
    issued_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
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
-- Name: materials; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.materials (
    id integer NOT NULL,
    name text NOT NULL,
    category text,
    stock integer DEFAULT 0,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    ready_to_install boolean DEFAULT false
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
    zayavka_id integer,
    instander_id bigint,
    solution_text text,
    media text,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
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
    zayavka_id integer,
    changed_by bigint,
    old_status character varying(20),
    new_status character varying(20),
    changed_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP
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
    id bigint NOT NULL,
    telegram_id bigint NOT NULL,
    abonent_id character varying(20),
    role character varying(20) NOT NULL,
    full_name text,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    phone_number text,
    language character varying(2) DEFAULT 'uz'::character varying,
    CONSTRAINT users_role_check CHECK (((role)::text = ANY ((ARRAY['admin'::character varying, 'technician'::character varying, 'client'::character varying, 'blocked'::character varying, 'call_center'::character varying, 'manager'::character varying, 'controller'::character varying, 'warehouse'::character varying])::text[])))
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
    id bigint NOT NULL,
    user_id bigint,
    description text NOT NULL,
    address text,
    media text,
    status character varying(20) DEFAULT 'pending'::character varying NOT NULL,
    assigned_to bigint,
    ready_to_install boolean DEFAULT false,
    created_at timestamp without time zone DEFAULT CURRENT_TIMESTAMP,
    completed_at timestamp without time zone,
    latitude double precision,
    longitude double precision,
    zayavka_type character varying(50) DEFAULT 'B2C'::character varying,
    abonent_id character varying(50),
    location text,
    priority integer DEFAULT 1,
    estimated_time integer,
    actual_time integer,
    completion_notes text,
    created_by_role character varying(20),
    CONSTRAINT zayavki_status_check CHECK (((status)::text = ANY ((ARRAY['new'::character varying, 'assigned'::character varying, 'in_progress'::character varying, 'completed'::character varying, 'cancelled'::character varying, 'transferred'::character varying])::text[])))
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
-- Name: feedback id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.feedback ALTER COLUMN id SET DEFAULT nextval('public.feedback_id_seq'::regclass);


--
-- Name: issued_items id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.issued_items ALTER COLUMN id SET DEFAULT nextval('public.issued_items_id_seq'::regclass);


--
-- Name: login_logs id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.login_logs ALTER COLUMN id SET DEFAULT nextval('public.login_logs_id_seq'::regclass);


--
-- Name: materials id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.materials ALTER COLUMN id SET DEFAULT nextval('public.materials_id_seq'::regclass);


--
-- Name: notification_queue id; Type: DEFAULT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.notification_queue ALTER COLUMN id SET DEFAULT nextval('public.notification_queue_id_seq'::regclass);


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
-- Data for Name: feedback; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.feedback (id, zayavka_id, user_id, rating, comment, created_at) FROM stdin;
\.


--
-- Data for Name: issued_items; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.issued_items (id, zayavka_id, material_id, quantity, issued_by, issued_at) FROM stdin;
\.


--
-- Data for Name: login_logs; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.login_logs (id, user_id, ip_address, user_agent, logged_at) FROM stdin;
\.


--
-- Data for Name: materials; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.materials (id, name, category, stock, created_at, ready_to_install) FROM stdin;
\.


--
-- Data for Name: notification_queue; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.notification_queue (id, user_id, message, zayavka_id, notification_type, sent, created_at) FROM stdin;
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
1	2	4	Sgs	\N	2025-06-24 17:20:52.817973
2	6	4	Xaxa	\N	2025-06-26 16:00:03.313405
3	6	4	Xaxa	\N	2025-06-26 16:00:07.681983
4	7	4	Teyeye	\N	2025-06-26 16:17:34.560774
5	8	4	Eueue	\N	2025-06-26 16:29:34.238716
6	12	4	Etetwgg	\N	2025-06-26 17:03:05.681019
7	11	4	Sysys	\N	2025-06-26 17:03:20.552135
8	13	4	Ttyt	\N	2025-06-26 17:17:06.023602
\.


--
-- Data for Name: status_logs; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.status_logs (id, zayavka_id, changed_by, old_status, new_status, changed_at) FROM stdin;
1	2	3	assigned	in_progress	2025-06-24 17:20:07.617698
2	2	7793341014	assigned	accepted	2025-06-24 17:20:29.049508
3	2	7793341014	accepted	in_progress	2025-06-24 17:20:41.674719
4	2	4	assigned	completed	2025-06-24 17:20:52.817973
5	2	\N	completed	new	2025-06-26 13:50:17.934047
6	2	\N	new	completed	2025-06-26 13:50:32.493505
7	6	3	assigned	in_progress	2025-06-26 15:59:47.853773
8	6	7793341014	assigned	accepted	2025-06-26 15:59:54.348134
9	6	7793341014	accepted	in_progress	2025-06-26 15:59:56.76659
10	6	4	assigned	completed	2025-06-26 16:00:03.313405
11	6	4	completed	completed	2025-06-26 16:00:07.681983
12	7	3	assigned	in_progress	2025-06-26 16:17:18.884517
13	7	7793341014	assigned	accepted	2025-06-26 16:17:25.835948
14	7	7793341014	accepted	in_progress	2025-06-26 16:17:28.676957
15	7	4	assigned	completed	2025-06-26 16:17:34.560774
16	8	3	assigned	in_progress	2025-06-26 16:27:32.940494
17	8	7793341014	assigned	accepted	2025-06-26 16:29:25.163177
18	8	7793341014	accepted	in_progress	2025-06-26 16:29:30.093041
19	8	4	assigned	completed	2025-06-26 16:29:34.238716
20	9	3	assigned	in_progress	2025-06-26 16:43:04.482532
21	10	3	assigned	in_progress	2025-06-26 16:45:45.429785
22	11	3	assigned	in_progress	2025-06-26 16:59:07.057304
23	12	3	assigned	in_progress	2025-06-26 17:02:44.372406
24	12	7793341014	assigned	accepted	2025-06-26 17:02:54.478109
25	12	7793341014	accepted	in_progress	2025-06-26 17:02:59.374634
26	12	4	assigned	completed	2025-06-26 17:03:05.681019
27	11	7793341014	assigned	accepted	2025-06-26 17:03:09.832993
28	11	7793341014	accepted	in_progress	2025-06-26 17:03:13.978719
29	11	4	assigned	completed	2025-06-26 17:03:20.552135
30	13	3	assigned	in_progress	2025-06-26 17:16:32.551734
31	13	7793341014	assigned	accepted	2025-06-26 17:16:46.820122
32	13	7793341014	accepted	in_progress	2025-06-26 17:16:59.732497
33	13	4	assigned	completed	2025-06-26 17:17:06.023602
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

COPY public.users (id, telegram_id, abonent_id, role, full_name, created_at, phone_number, language) FROM stdin;
1	1978574076	\N	admin	Ulugbek Administrator	2025-06-20 17:14:25.700063	+998900042544	uz
2	8188731606	\N	client	Barat	2025-06-24 16:21:27.25379	+998881249327	uz
3	5955605892	\N	manager	Gulsara Yoqubjonova	2025-06-24 16:24:09.074913	+998900047294	uz
4	7793341014	\N	technician	Ал-Хабаш Шейх	2025-06-24 16:24:23.542635	+998937490211	uz
\.


--
-- Data for Name: zayavka_transfers; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.zayavka_transfers (id, zayavka_id, from_technician_id, to_technician_id, transferred_by, reason, transferred_at) FROM stdin;
\.


--
-- Data for Name: zayavki; Type: TABLE DATA; Schema: public; Owner: postgres
--

COPY public.zayavki (id, user_id, description, address, media, status, assigned_to, ready_to_install, created_at, completed_at, latitude, longitude, zayavka_type, abonent_id, location, priority, estimated_time, actual_time, completion_notes, created_by_role) FROM stdin;
1	2	Svshs	Adress	AgACAgIAAxkBAAINrGhVJ0M9PMZ9MXydhUW_yS58ztzrAAIX9zEb7l-pSh5rujbyyai0AQADAgADeQADNgQ	new	\N	f	2025-06-24 16:22:14.688522	\N	\N	\N	Физическое лицо	1234532	41.322168,69.283288	1	\N	\N	\N	\N
3	2	Svsgs	Sbdhsshs	AgACAgIAAxkBAAIUU2hamH-ahhpFq945J2KWiMx_NTnQAAJP7jEb3KrZSkWtQ-zOEBtvAQADAgADeQADNgQ	new	\N	f	2025-06-24 17:22:34.695416	\N	\N	\N	Jismoniy shaxs	24667	41.322168,69.283288	1	\N	\N	\N	\N
4	2	Orqaga	2y2u272828	AgACAgIAAxkBAAIUyWharpAIlOF2F5AmwskgLfJ4pmVgAAL-7jEb3KrZSqR_z0qY532VAQADAgADeQADNgQ	new	\N	f	2025-06-24 18:56:43.141203	\N	\N	\N	Jismoniy shaxs	53366	\N	1	\N	\N	\N	\N
2	2	Sgssh	Msnssjsj	AgACAgIAAxkBAAIUL2hal-IpiSzqbIP3vkErSb1nTFvlAAJq8zEbMtnYSii7Hb8rboJ6AQADAgADeQADNgQ	completed	4	f	2025-06-24 17:19:58.951601	2025-06-26 13:50:32.49315	\N	\N	Jismoniy shaxs	2562	41.32207,69.28337	1	\N	\N	\N	\N
5	5955605892	Tafsilot	\N	\N	new	\N	f	2025-06-26 14:53:10.412501	\N	\N	\N	B2C	\N	\N	1	\N	\N	\N	\N
6	2	Xaxaga	Manzil test	\N	completed	4	f	2025-06-26 15:59:34.314886	2025-06-26 16:00:07.681983	\N	\N	Jismoniy shaxs	123456	\N	1	\N	\N	\N	client
7	2	Svsvgs	Svsvsv	\N	completed	4	f	2025-06-26 16:17:05.95079	2025-06-26 16:17:34.560774	\N	\N	Физическое лицо	152525	\N	1	\N	\N	\N	client
8	2	Egeyey	Dgdgs	\N	completed	4	f	2025-06-26 16:25:43.858554	2025-06-26 16:29:34.238716	\N	\N	Физическое лицо	2522222	\N	1	\N	\N	\N	client
9	2	Sgsgss	Wywywuwu	\N	assigned	4	f	2025-06-26 16:42:55.886144	\N	\N	\N	Физическое лицо	25226	\N	1	\N	\N	\N	client
10	2	Svdvdvs	Bzbshshhahss	\N	assigned	4	f	2025-06-26 16:45:34.24121	\N	\N	\N	Физическое лицо	162722	\N	1	\N	\N	\N	client
12	2	Svsvgaa	Shhssus	\N	completed	4	f	2025-06-26 17:02:36.785694	2025-06-26 17:03:05.681019	\N	\N	Физическое лицо	526262	\N	1	\N	\N	\N	client
11	2	Dhdgww	Eyeywuw7w7w	\N	completed	4	f	2025-06-26 16:58:58.328039	2025-06-26 17:03:20.552135	\N	\N	Физическое лицо	36363ww	\N	1	\N	\N	\N	client
13	2	Shshsh	Svsvshh	\N	completed	4	f	2025-06-26 17:16:19.972405	2025-06-26 17:17:06.023602	\N	\N	Jismoniy shaxs	252626	\N	1	\N	\N	\N	client
\.


--
-- Name: feedback_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.feedback_id_seq', 1, false);


--
-- Name: issued_items_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.issued_items_id_seq', 1, false);


--
-- Name: login_logs_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.login_logs_id_seq', 1, false);


--
-- Name: materials_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.materials_id_seq', 1, false);


--
-- Name: notification_queue_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.notification_queue_id_seq', 1, false);


--
-- Name: notifications_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.notifications_id_seq', 1, false);


--
-- Name: solutions_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.solutions_id_seq', 8, true);


--
-- Name: status_logs_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.status_logs_id_seq', 33, true);


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

SELECT pg_catalog.setval('public.users_id_seq', 4, true);


--
-- Name: zayavka_transfers_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.zayavka_transfers_id_seq', 1, false);


--
-- Name: zayavki_id_seq; Type: SEQUENCE SET; Schema: public; Owner: postgres
--

SELECT pg_catalog.setval('public.zayavki_id_seq', 13, true);


--
-- Name: feedback feedback_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.feedback
    ADD CONSTRAINT feedback_pkey PRIMARY KEY (id);


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
-- Name: idx_notification_queue_sent; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_notification_queue_sent ON public.notification_queue USING btree (sent);


--
-- Name: idx_technician_workload_technician; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_technician_workload_technician ON public.technician_workload USING btree (technician_id);


--
-- Name: idx_zayavki_assigned_to; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_zayavki_assigned_to ON public.zayavki USING btree (assigned_to);


--
-- Name: idx_zayavki_status; Type: INDEX; Schema: public; Owner: postgres
--

CREATE INDEX idx_zayavki_status ON public.zayavki USING btree (status);


--
-- Name: feedback feedback_zayavka_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.feedback
    ADD CONSTRAINT feedback_zayavka_id_fkey FOREIGN KEY (zayavka_id) REFERENCES public.zayavki(id);


--
-- Name: issued_items issued_items_material_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.issued_items
    ADD CONSTRAINT issued_items_material_id_fkey FOREIGN KEY (material_id) REFERENCES public.materials(id);


--
-- Name: issued_items issued_items_zayavka_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.issued_items
    ADD CONSTRAINT issued_items_zayavka_id_fkey FOREIGN KEY (zayavka_id) REFERENCES public.zayavki(id);


--
-- Name: notification_queue notification_queue_user_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.notification_queue
    ADD CONSTRAINT notification_queue_user_id_fkey FOREIGN KEY (user_id) REFERENCES public.users(id);


--
-- Name: notification_queue notification_queue_zayavka_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.notification_queue
    ADD CONSTRAINT notification_queue_zayavka_id_fkey FOREIGN KEY (zayavka_id) REFERENCES public.zayavki(id);


--
-- Name: notifications notifications_zayavka_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.notifications
    ADD CONSTRAINT notifications_zayavka_id_fkey FOREIGN KEY (zayavka_id) REFERENCES public.zayavki(id);


--
-- Name: solutions solutions_zayavka_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.solutions
    ADD CONSTRAINT solutions_zayavka_id_fkey FOREIGN KEY (zayavka_id) REFERENCES public.zayavki(id);


--
-- Name: status_logs status_logs_zayavka_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.status_logs
    ADD CONSTRAINT status_logs_zayavka_id_fkey FOREIGN KEY (zayavka_id) REFERENCES public.zayavki(id);


--
-- Name: technician_performance technician_performance_technician_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.technician_performance
    ADD CONSTRAINT technician_performance_technician_id_fkey FOREIGN KEY (technician_id) REFERENCES public.users(id);


--
-- Name: technician_workload technician_workload_technician_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.technician_workload
    ADD CONSTRAINT technician_workload_technician_id_fkey FOREIGN KEY (technician_id) REFERENCES public.users(id);


--
-- Name: zayavka_transfers zayavka_transfers_from_technician_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.zayavka_transfers
    ADD CONSTRAINT zayavka_transfers_from_technician_id_fkey FOREIGN KEY (from_technician_id) REFERENCES public.users(id);


--
-- Name: zayavka_transfers zayavka_transfers_to_technician_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.zayavka_transfers
    ADD CONSTRAINT zayavka_transfers_to_technician_id_fkey FOREIGN KEY (to_technician_id) REFERENCES public.users(id);


--
-- Name: zayavka_transfers zayavka_transfers_transferred_by_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.zayavka_transfers
    ADD CONSTRAINT zayavka_transfers_transferred_by_fkey FOREIGN KEY (transferred_by) REFERENCES public.users(id);


--
-- Name: zayavka_transfers zayavka_transfers_zayavka_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.zayavka_transfers
    ADD CONSTRAINT zayavka_transfers_zayavka_id_fkey FOREIGN KEY (zayavka_id) REFERENCES public.zayavki(id);


--
-- PostgreSQL database dump complete
--

