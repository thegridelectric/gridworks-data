-- gridworks.messages: the gw.weather.forecast rows journaled at 001 under
-- an id of sender, type and created time, before the row id included the
-- bundle name. An S3 load re-journals the same sends under the bundle-keyed
-- id, so these rows go first or every bobcat hour would hold two. Hand-run,
-- once per database, before that load: tsdb_tap first, then production,
-- both operators consenting. The script refuses to run once bundle-keyed
-- 001 rows are present (a bundle other than bobcat at 001). Run inside the
-- transaction and inspect the two counts before COMMIT.
--
--   psql "$URL" -v ON_ERROR_STOP=1 -f forecast_rows_before_bundle_keyed_ids.sql
--
BEGIN;
SET LOCAL lock_timeout = '5s';
SET LOCAL statement_timeout = '30s';

\echo === before
SELECT payload->>'BundleName' AS bundle, payload->>'Version' AS version, count(*)
  FROM gridworks.messages WHERE message_type_name = 'gw.weather.forecast'
 GROUP BY 1, 2 ORDER BY 1, 2;

DO $$
BEGIN
  IF EXISTS (SELECT 1 FROM gridworks.messages
              WHERE message_type_name = 'gw.weather.forecast'
                AND payload->>'Version' = '001'
                AND payload->>'BundleName' <> 'us.me.millinocket.bobcat') THEN
    RAISE EXCEPTION 'bundle-keyed 001 rows are present; this script has already run here';
  END IF;
END $$;

DELETE FROM gridworks.messages
 WHERE message_type_name = 'gw.weather.forecast' AND payload->>'Version' = '001';

\echo === after
SELECT payload->>'BundleName' AS bundle, payload->>'Version' AS version, count(*)
  FROM gridworks.messages WHERE message_type_name = 'gw.weather.forecast'
 GROUP BY 1, 2 ORDER BY 1, 2;

COMMIT;
