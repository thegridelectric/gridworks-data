import logging
from datetime import datetime, timedelta, timezone
import dotenv

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from gw_data.config import Settings

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)s | %(message)s")
logger = logging.getLogger(__name__)

dotenv.load_dotenv()
settings = Settings()
engine = create_engine(settings.db_url.get_secret_value(), echo=False)

db_sessionmaker = sessionmaker(bind=engine)
db_session = db_sessionmaker()


t_start = datetime.now(timezone.utc).replace(minute=0, second=0, microsecond=0)
t_final = datetime(2026, 1, 1, tzinfo=timezone.utc)

# t_start = datetime(2026, 4, 22, tzinfo=timezone.utc)
# t_final = datetime(2026, 4, 18, tzinfo=timezone.utc)


while t_start > t_final:
    logger.info(f'Refreshing from {t_start.isoformat()}...')
    t_end = t_start
    t_start = t_end - timedelta(days=7)

    stmt = text(f"""
    INSERT INTO gridworks.cached_hourly_data
    WITH hourly_data AS MATERIALIZED (
        SELECT * FROM gridworks.calc_hourly_data(t_start => '{(t_start - timedelta(hours=1)).isoformat()}', t_end => '{t_end.isoformat()}')
    )
    SELECT * FROM hourly_data
    WHERE time_bucket >= '{t_start.isoformat()}' AND time_bucket < '{t_end.isoformat()}';
    """)

    db_result = db_session.execute(stmt)
    db_session.commit()
    logger.info(f'Inserted {db_result.rowcount} rows')

