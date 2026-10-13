-- Product v1 is intentionally namespaced: existing PoC tables are untouched.
CREATE TABLE IF NOT EXISTS v1_vehicles (
  vehicle_id uuid PRIMARY KEY, display_name text NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE IF NOT EXISTS v1_devices (
  device_id uuid PRIMARY KEY,
  vehicle_id uuid NOT NULL REFERENCES v1_vehicles(vehicle_id),
  token_sha256 char(64) NOT NULL UNIQUE,
  revoked_at timestamptz,
  created_at timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE IF NOT EXISTS v1_profile_revisions (
  profile_revision_id uuid PRIMARY KEY,
  device_id uuid NOT NULL REFERENCES v1_devices(device_id),
  vehicle_id uuid NOT NULL REFERENCES v1_vehicles(vehicle_id),
  payload jsonb NOT NULL,
  content_hash char(64) NOT NULL,
  created_at timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE IF NOT EXISTS v1_runs (
  run_id uuid PRIMARY KEY,
  device_id uuid NOT NULL REFERENCES v1_devices(device_id),
  vehicle_id uuid NOT NULL REFERENCES v1_vehicles(vehicle_id),
  created_at timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE IF NOT EXISTS v1_segments (
  segment_id uuid PRIMARY KEY,
  run_id uuid NOT NULL REFERENCES v1_runs(run_id),
  profile_revision_id uuid REFERENCES v1_profile_revisions(profile_revision_id),
  created_at timestamptz NOT NULL DEFAULT now()
);
CREATE TABLE IF NOT EXISTS v1_ingest_clock (
  vehicle_id uuid PRIMARY KEY REFERENCES v1_vehicles(vehicle_id),
  last_seq bigint NOT NULL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS v1_records (
  record_id uuid PRIMARY KEY,
  device_id uuid NOT NULL REFERENCES v1_devices(device_id),
  vehicle_id uuid NOT NULL REFERENCES v1_vehicles(vehicle_id),
  run_id uuid NOT NULL REFERENCES v1_runs(run_id),
  segment_id uuid REFERENCES v1_segments(segment_id),
  kind text NOT NULL CHECK (kind IN ('observation','event','gap')),
  sequence bigint,
  captured_at timestamptz NOT NULL,
  source_kind text NOT NULL CHECK (source_kind IN ('ecu','synthetic','agent')),
  profile_revision_id uuid REFERENCES v1_profile_revisions(profile_revision_id),
  content_hash char(64) NOT NULL,
  payload jsonb NOT NULL,
  ingest_seq bigint NOT NULL,
  received_at timestamptz NOT NULL DEFAULT now(),
  CHECK (
    (kind='observation' AND sequence IS NOT NULL AND sequence>=0
      AND profile_revision_id IS NOT NULL AND segment_id IS NOT NULL
      AND source_kind IN ('ecu','synthetic'))
    OR (kind IN ('event','gap') AND sequence IS NULL AND profile_revision_id IS NULL)
  )
);
CREATE UNIQUE INDEX IF NOT EXISTS v1_observation_run_seq
  ON v1_records(run_id,sequence) WHERE kind='observation';
CREATE UNIQUE INDEX IF NOT EXISTS v1_records_vehicle_ingest_seq
  ON v1_records(vehicle_id,ingest_seq);
CREATE INDEX IF NOT EXISTS v1_records_vehicle_time
  ON v1_records(vehicle_id,captured_at,record_id);
CREATE TABLE IF NOT EXISTS v1_values (
  record_id uuid NOT NULL REFERENCES v1_records(record_id),
  parameter_id text NOT NULL,
  value double precision NOT NULL CHECK (isfinite(value)),
  PRIMARY KEY (record_id,parameter_id)
);
CREATE INDEX IF NOT EXISTS v1_values_filter
  ON v1_values(parameter_id,value,record_id);
CREATE TABLE IF NOT EXISTS v1_device_status (
  device_id uuid PRIMARY KEY REFERENCES v1_devices(device_id),
  vehicle_id uuid NOT NULL REFERENCES v1_vehicles(vehicle_id),
  reported_at timestamptz NOT NULL,
  received_at timestamptz NOT NULL DEFAULT now(),
  state jsonb NOT NULL
);
