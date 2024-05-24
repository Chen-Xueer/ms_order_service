"""empty message

Revision ID: 3ab1cd059f4c
Revises: d196053a8917
Create Date: 2024-05-23 18:18:54.923258

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3ab1cd059f4c'
down_revision: Union[str, None] = 'd196053a8917'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('order', sa.Column('request_id', sa.String(length=255), nullable=True))
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('order', 'request_id')
    # ### end Alembic commands ###
