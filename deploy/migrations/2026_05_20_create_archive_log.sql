-- depends_on: []
-- down:
-- DROP TABLE IF EXISTS archive_log;

CREATE TABLE archive_log (
    id          bigserial PRIMARY KEY,
    activity_id bigint NOT NULL,
    archived_at timestamptz NOT NULL DEFAULT now()
);

CREATE INDEX archive_log_activity_id_idx ON archive_log (activity_id);
