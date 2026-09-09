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
('species.crystal_filterer','species','Crystal Filterer','2026-09-09T00:00:00Z','2026-09-09T00:00:00Z'),
('species.shellback','species','Desert Shellback','2026-09-09T00:00:00Z','2026-09-09T00:00:00Z'),
('entity.global_only','record','Global Only','2026-09-09T00:00:00Z','2026-09-09T00:00:00Z');

INSERT INTO fields VALUES
('f_habitat','habitat','Habitat','text','','active','2026-09-09T00:00:00Z','2026-09-09T00:00:00Z','game.alien_lineage','habitat'),
('f_feeding','feeding','Feeding','text','','converged','2026-09-09T00:00:00Z','2026-09-09T00:00:00Z','game.alien_lineage','feeding'),
('f_draft','draft_trait','Draft Trait','text','','proposed','2026-09-09T00:00:00Z','2026-09-09T00:00:00Z','game.alien_lineage','draft_trait'),
('f_old','old_trait','Old Trait','text','','deprecated','2026-09-09T00:00:00Z','2026-09-09T00:00:00Z','game.alien_lineage','old_trait'),
('f_global','description','Description','text','','active','2026-09-09T00:00:00Z','2026-09-09T00:00:00Z','global','description');

INSERT INTO cells VALUES
('species.crystal_filterer','f_habitat','"abyss"','seed',1.0,'2026-09-09T00:00:00Z'),
('species.crystal_filterer','f_feeding','"filter"','seed',1.0,'2026-09-09T00:00:00Z'),
('species.crystal_filterer','f_draft','"candidate-only"','ai',0.5,'2026-09-09T00:00:00Z'),
('species.crystal_filterer','f_old','"legacy"','seed',1.0,'2026-09-09T00:00:00Z'),
('species.crystal_filterer','f_global','"A filter feeder"','seed',1.0,'2026-09-09T00:00:00Z'),
('species.shellback','f_habitat','"desert"','seed',1.0,'2026-09-09T00:00:00Z'),
('entity.global_only','f_global','"Global"','seed',1.0,'2026-09-09T00:00:00Z');
