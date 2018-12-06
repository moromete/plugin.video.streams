ALTER TABLE channels ADD COLUMN last_online TEXT;
ALTER TABLE channels ADD COLUMN checked INTEGER;

PRAGMA user_version=0002;