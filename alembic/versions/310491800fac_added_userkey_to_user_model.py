"""Added userkey to User model.

Revision ID: 310491800fac
Revises: f3df4e5d91da
Create Date: 2016-12-30 18:31:54.050606

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '310491800fac'
down_revision = 'f3df4e5d91da'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('user', sa.Column('userkey', sa.String(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('user', 'userkey')
    # ### end Alembic commands ###