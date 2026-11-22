"""hourly weather columns

calc_hourly_data's oat_f and ws_mph are the weather station's observation
(kmlt-temperature, kmlt-windspeed under the weather GNode's alias), the
model gridpoint's (ommillinocket-*) where the station has none, and the
house's own forecast channels where neither exists; ghi_w_m2 is the
gridpoint's irradiance; oat_source and ws_source name the channel each
hour's value was read from. The three new columns are appended to
cached_hourly_data, and the function is dropped before it is re-created
because its return table changes. The body is the misc script. The whole
table is refilled by hand afterwards (refresh_all_cached_hourly_data.py
with no arguments), and the hourly aggregate is refreshed over the
archived weather window first where it was not materialized.

Revision ID: e3f5a7b9c1d2
Revises: d2e4f6a8b0c1
"""

import os
from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "e3f5a7b9c1d2"
down_revision: Union[str, Sequence[str], None] = "d2e4f6a8b0c1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

MISC = os.path.join(os.path.dirname(__file__), "../../src/gw_data/db/scripts/misc/")


def upgrade() -> None:
    # IF NOT EXISTS: a chain run from empty creates the table from the
    # current script, which has the columns already.
    op.execute(
        "ALTER TABLE gridworks.cached_hourly_data "
        "ADD COLUMN IF NOT EXISTS ghi_w_m2 float, "
        "ADD COLUMN IF NOT EXISTS oat_source text, "
        "ADD COLUMN IF NOT EXISTS ws_source text"
    )
    op.execute("DROP FUNCTION gridworks.calc_hourly_data(timestamp with time zone, timestamp with time zone)")
    with open(os.path.join(MISC, "create_udf_calc_hourly_data.sql")) as f:
        op.execute(f.read().strip())


def downgrade() -> None:
    # The function keeps this body and the table its columns.
    pass
