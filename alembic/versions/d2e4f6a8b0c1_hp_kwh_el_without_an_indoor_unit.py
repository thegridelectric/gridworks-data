"""hp_kwh_el without an indoor unit

calc_hourly_data's hp_kwh_el is the sum of the heat pump's indoor and
outdoor unit power, and a house whose heat pump has no indoor unit (an
Arctic) has no hp-idu-pwr channel, so the sum was null for every hour.
The column is now the sum of whichever units the house has, null only
when neither reported. The body is the misc script; the return table is
unchanged. The hours already cached for such a house are refilled by hand
(refresh_all_cached_hourly_data.py over the window).

Revision ID: d2e4f6a8b0c1
Revises: c5d7e9f2a4b6
"""

import os
from typing import Sequence, Union

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "d2e4f6a8b0c1"
down_revision: Union[str, Sequence[str], None] = "c5d7e9f2a4b6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

MISC = os.path.join(os.path.dirname(__file__), "../../src/gw_data/db/scripts/misc/")


def upgrade() -> None:
    with open(os.path.join(MISC, "create_udf_calc_hourly_data.sql")) as f:
        op.execute(f.read().strip())


def downgrade() -> None:
    # The function keeps this body; the plain sum it replaces is not restored.
    pass
