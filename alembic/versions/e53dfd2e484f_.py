"""empty message

Revision ID: e53dfd2e484f
Revises: 2257a258ea37
Create Date: 2024-05-29 15:57:38.856730

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e53dfd2e484f'
down_revision: Union[str, None] = '2257a258ea37'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('tenant',
    sa.Column('tenant_id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('tenant', sa.String(length=100), nullable=True),
    sa.Column('payment_method', sa.String(length=3000), nullable=True),
    sa.PrimaryKeyConstraint('tenant_id')
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('tenant')
    # ### end Alembic commands ###