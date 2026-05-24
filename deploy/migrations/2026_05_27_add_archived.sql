-- depends_on: [2026_05_20_create_archive_log]
-- down:
-- DROP TRIGGER IF EXISTS activity_archive_trg ON activity;
-- DROP FUNCTION IF EXISTS activity_archive_fn();
-- ALTER TABLE activity DROP COLUMN IF EXISTS archived;

ALTER TABLE activity ADD COLUMN archived boolean NOT NULL DEFAULT false;

CREATE FUNCTION activity_archive_fn() RETURNS trigger AS $$
BEGIN
    IF NEW.archived AND NOT OLD.archived THEN
        INSERT INTO archive_log (activity_id) VALUES (NEW.id);
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER activity_archive_trg
    AFTER UPDATE ON activity
    FOR EACH ROW EXECUTE FUNCTION activity_archive_fn();
