CREATE TABLE IF NOT EXISTS profiles_cache
(
    id        INTEGER PRIMARY KEY,
    username  TEXT UNIQUE ON CONFLICT REPLACE,
    full_name TEXT,
    userid    INT,
    success   TEXT
)