"""Refill gridworks.cached_hourly_data over a window, one day at a time,
newest day first: each day's rows are deleted and recomputed through
gridworks.calc_hourly_data, so the refresh is idempotent and a re-run
over hours that exist does not duplicate them (the table has no key).

    uv run python src/gw_data/db/scripts/misc/refresh_all_cached_hourly_data.py [START] [FINAL]

START and FINAL are UTC dates or timestamps; the window is FINAL <= hour
< START. START defaults to the current hour, FINAL to 2024-10-13, the
first journaled hour.
"""

import logging
import sys
from datetime import datetime, timedelta, timezone

import dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from gw_data.config import Settings

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
logger = logging.getLogger(__name__)

FIRST_JOURNALED = datetime(2024, 10, 13, tzinfo=timezone.utc)


def utc(arg: str) -> datetime:
    t = datetime.fromisoformat(arg)
    return t.replace(tzinfo=timezone.utc) if t.tzinfo is None else t.astimezone(timezone.utc)


def main() -> None:
    dotenv.load_dotenv()
    settings = Settings()
    engine = create_engine(settings.db_url.get_secret_value(), echo=False)
    db_session = sessionmaker(bind=engine)()

    t_start = utc(sys.argv[1]) if len(sys.argv) > 1 else datetime.now(timezone.utc).replace(minute=0, second=0, microsecond=0)
    t_final = utc(sys.argv[2]) if len(sys.argv) > 2 else FIRST_JOURNALED
    logger.info(f"Refreshing cached_hourly_data for {t_final.isoformat()} <= hour < {t_start.isoformat()}")

    while t_start > t_final:
        t_end = t_start
        t_start = max(t_end - timedelta(days=1), t_final)
        logger.info(f"{t_start.isoformat()} to {t_end.isoformat()}")
        deleted = db_session.execute(
            text("DELETE FROM gridworks.cached_hourly_data WHERE time_bucket >= :t_start AND time_bucket < :t_end"),
            {"t_start": t_start, "t_end": t_end},
        )
        inserted = db_session.execute(
            text("""
            INSERT INTO gridworks.cached_hourly_data
            WITH hourly_data AS MATERIALIZED (
                SELECT * FROM gridworks.calc_hourly_data(t_start => :t_calc, t_end => :t_end)
            )
            SELECT * FROM hourly_data
            WHERE time_bucket >= :t_start AND time_bucket < :t_end
            """),
            {"t_calc": t_start - timedelta(hours=1), "t_start": t_start, "t_end": t_end},
        )
        db_session.commit()
        logger.info(f"deleted {deleted.rowcount}, inserted {inserted.rowcount}")


if __name__ == "__main__":
    main()
