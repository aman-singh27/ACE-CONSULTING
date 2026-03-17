"""drop unique constraint on actor_configs.actor_id

Revision ID: b4e1f2c3d5a6
Revises: a3c2a669d63e
Create Date: 2026-03-07 14:50:00.000000
"""

from typing import Sequence, Union
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "b4e1f2c3d5a6"
down_revision: Union[str, None] = "a3c2a669d63e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_constraint("actor_configs_actor_id_key", "actor_configs", type_="unique")


def downgrade() -> None:
    op.create_unique_constraint("actor_configs_actor_id_key", "actor_configs", ["actor_id"])
