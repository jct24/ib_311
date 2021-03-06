CREATE TABLE IF NOT EXISTS public.service_requests (
    case_summary text NULL,
    case_status text NULL,
    case_source text NULL,
    case_created_date date NULL,
    case_created_dttm timestamp NULL,
    case_closed_date date NULL,
    case_closed_dttm timestamp NULL,
    first_call_resolution text NULL,
    customer_zip_code text NULL,
    incident_address_1 text NULL,
    incident_address_2 textNULL,
    incident_intersection_1 text NULL,
    incident_intersection_2 text NULL,
    incident_zip_code text NULL,
    longitude float8 NULL,
    latitude float8 NULL,
    agency text NULL,
    -- division NULL,
    -- major_area NULL,
    type text NULL,
    -- topic NULL,
    council_district int NULL,
    police_district int NULL,
    neighborhood text NULL,
    load_date date NOT NULL,
    case_id serial NOT NULL
);


