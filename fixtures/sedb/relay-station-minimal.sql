CREATE TABLE entities (
    id TEXT PRIMARY KEY,
    kind TEXT NOT NULL,
    label TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
CREATE TABLE fields (
    id TEXT PRIMARY KEY,
    key TEXT NOT NULL UNIQUE,
    label TEXT NOT NULL,
    value_type TEXT NOT NULL,
    description TEXT NOT NULL,
    status TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    namespace TEXT NOT NULL,
    normalized_key TEXT
);
CREATE TABLE cells (
    entity_id TEXT NOT NULL,
    field_id TEXT NOT NULL,
    value_json TEXT NOT NULL,
    source TEXT NOT NULL,
    confidence REAL,
    updated_at TEXT NOT NULL,
    PRIMARY KEY(entity_id, field_id)
);
INSERT INTO entities VALUES
('role.relay_runner','role','Relay Runner','2026-09-09T00:00:00Z','2026-09-09T00:00:00Z'),
('facility.storm_relay','facility','Storm Relay Core','2026-09-09T00:00:00Z','2026-09-09T00:00:00Z'),
('component.phase_coupler','component','Phase Coupler','2026-09-09T00:00:00Z','2026-09-09T00:00:00Z'),
('signal.restored_link','signal','Restored Relay Link','2026-09-09T00:00:00Z','2026-09-09T00:00:00Z');
INSERT INTO fields VALUES
('f_role','operational_role','Operational Role','text','','active','2026-09-09T00:00:00Z','2026-09-09T00:00:00Z','game.relay_station','operational_role'),
('f_facility','facility_class','Facility Class','text','','active','2026-09-09T00:00:00Z','2026-09-09T00:00:00Z','game.relay_station','facility_class'),
('f_component','component_function','Component Function','text','','active','2026-09-09T00:00:00Z','2026-09-09T00:00:00Z','game.relay_station','component_function'),
('f_signal','signal_scope','Signal Scope','text','','converged','2026-09-09T00:00:00Z','2026-09-09T00:00:00Z','game.relay_station','signal_scope'),
('f_draft','draft_note','Draft Note','text','','proposed','2026-09-09T00:00:00Z','2026-09-09T00:00:00Z','game.relay_station','draft_note');
INSERT INTO cells VALUES
('role.relay_runner','f_role','"field_maintenance"','seed',1.0,'2026-09-09T00:00:00Z'),
('facility.storm_relay','f_facility','"communications_relay"','seed',1.0,'2026-09-09T00:00:00Z'),
('component.phase_coupler','f_component','"phase_alignment"','seed',1.0,'2026-09-09T00:00:00Z'),
('signal.restored_link','f_signal','"regional"','seed',1.0,'2026-09-09T00:00:00Z'),
('facility.storm_relay','f_draft','"candidate-only"','ai',0.5,'2026-09-09T00:00:00Z');
