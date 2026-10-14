CREATE TABLE IF NOT EXISTS swims (
    swim_date      TEXT    NOT NULL,   -- YYYY-MM-DD
    stroke         TEXT    NOT NULL CHECK (stroke IN ('freestyle', 'backstroke')),
    distance_m     INTEGER NOT NULL CHECK (distance_m > 0),
    time_sec       REAL    NOT NULL CHECK (time_sec > 0),
    pace_per_100m  REAL    NOT NULL,
    pool_length_m  INTEGER NOT NULL DEFAULT 25
);

CREATE INDEX IF NOT EXISTS idx_swims_stroke_dist ON swims (stroke, distance_m, swim_date);
