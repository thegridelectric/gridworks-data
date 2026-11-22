"""The hourly functions read each reading's unit from unit_scale

gridworks.retrieve_readings_1s reads a channel's rows across layout eras
as one lineage: one row per channel per second, the latest reading with
its own unit, so a retired row's last value is not carried past the next
row's first reading. gridworks.in_unit converts a stored integer to the unit a column wants
through its unit_scale row. calc_energy_1hr and calc_hourly_data join
readings to unit_scale on (unit_type, unit) and select by channel name
and quantity, so a channel recorded in either unit enum, in any layout
era, feeds its hourly column. Their bodies are the misc scripts; the
return tables are unchanged, so cached_hourly_data is as it was and the
cache is refreshed by hand (refresh_all_cached_hourly_data.py) to fill
the hours the unit literals left empty.

Revision ID: c5d7e9f2a4b6
Revises: b8c4d2e6f1a3
"""

import os
from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "c5d7e9f2a4b6"
down_revision: Union[str, Sequence[str], None] = "b8c4d2e6f1a3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

MISC = os.path.join(os.path.dirname(__file__), "../../src/gw_data/db/scripts/misc/")
SCRIPTS = [
    "create_udf_retrieve_readings_1s.sql",
    "create_udf_in_unit.sql",
    "create_udf_calc_energy_1hr.sql",
    "create_udf_calc_hourly_data.sql",
]


def upgrade() -> None:
    for script in SCRIPTS:
        with open(os.path.join(MISC, script)) as f:
            op.execute(f.read().strip())


def downgrade() -> None:
    # retrieve_readings_1s keeps the lineage body; the per-row body it replaces is not restored.
    op.execute("DROP FUNCTION gridworks.calc_hourly_data(timestamp with time zone, timestamp with time zone);")
    op.execute("DROP FUNCTION gridworks.calc_energy_1hr(timestamp with time zone, timestamp with time zone);")
    op.execute("DROP FUNCTION gridworks.in_unit(float, bigint, text, text);")
