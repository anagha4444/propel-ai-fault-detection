CREATE TABLE IF NOT EXISTS poles (
    id SERIAL PRIMARY KEY,
    name VARCHAR(120) NOT NULL,
    feeder_id INTEGER,
    transformer_id INTEGER,
    parent_pole_id INTEGER,
    latitude NUMERIC(9,6) NOT NULL,
    longitude NUMERIC(9,6) NOT NULL,
    firmware_version VARCHAR(32) DEFAULT '1.2',
    is_sensor_online BOOLEAN DEFAULT true,
    last_seen_at TIMESTAMP,
    topology_confidence NUMERIC(4,3) DEFAULT 1.0,
    extra_metadata TEXT
);

CREATE TABLE IF NOT EXISTS transformers (
    id SERIAL PRIMARY KEY,
    name VARCHAR(120) NOT NULL,
    latitude NUMERIC(9,6) NOT NULL,
    longitude NUMERIC(9,6) NOT NULL,
    feeder_id INTEGER,
    parent_pole_id INTEGER,
    topology_confidence NUMERIC(4,3) DEFAULT 1.0
);

CREATE TABLE IF NOT EXISTS feeders (
    id SERIAL PRIMARY KEY,
    name VARCHAR(120) NOT NULL,
    latitude NUMERIC(9,6) NOT NULL,
    longitude NUMERIC(9,6) NOT NULL,
    extra_metadata TEXT
);

CREATE TABLE IF NOT EXISTS telemetry (
    id SERIAL PRIMARY KEY,
    device_id VARCHAR(64) NOT NULL,
    pole_id INTEGER NOT NULL,
    sequence_number INTEGER NOT NULL,
    event_type VARCHAR(32) DEFAULT 'heartbeat',
    power_lost BOOLEAN DEFAULT false,
    power_restored BOOLEAN DEFAULT false,
    voltage NUMERIC(8,3),
    current NUMERIC(8,3),
    temperature NUMERIC(8,3),
    firmware_version VARCHAR(32) DEFAULT '1.2',
    received_at TIMESTAMP NOT NULL,
    event_time TIMESTAMP NOT NULL,
    source VARCHAR(32) DEFAULT 'simulator',
    stale_packet BOOLEAN DEFAULT false,
    clock_skew_seconds NUMERIC(8,3),
    is_out_of_order BOOLEAN DEFAULT false,
    extra_metadata TEXT
);

CREATE TABLE IF NOT EXISTS faults (
    id SERIAL PRIMARY KEY,
    fault_type VARCHAR(32) NOT NULL,
    source_pole_id INTEGER,
    affected_pole_count INTEGER DEFAULT 0,
    confidence_score NUMERIC(4,3) DEFAULT 0.0,
    status VARCHAR(32) DEFAULT 'Detected',
    detected_at TIMESTAMP NOT NULL,
    resolved_at TIMESTAMP,
    topology_confidence NUMERIC(4,3) DEFAULT 1.0,
    extra_metadata TEXT
);

CREATE TABLE IF NOT EXISTS tickets (
    id SERIAL PRIMARY KEY,
    fault_id INTEGER NOT NULL,
    status VARCHAR(32) DEFAULT 'Detected',
    crew_assigned VARCHAR(120),
    created_at TIMESTAMP NOT NULL,
    updated_at TIMESTAMP NOT NULL,
    extra_metadata TEXT
);

CREATE TABLE IF NOT EXISTS scheduled_outages (
    id SERIAL PRIMARY KEY,
    feeder_id INTEGER,
    pole_id INTEGER,
    start_time TIMESTAMP NOT NULL,
    end_time TIMESTAMP NOT NULL,
    active BOOLEAN DEFAULT true
);

CREATE TABLE IF NOT EXISTS simulation_logs (
    id SERIAL PRIMARY KEY,
    event_type VARCHAR(64) NOT NULL,
    payload TEXT,
    created_at TIMESTAMP NOT NULL
);
