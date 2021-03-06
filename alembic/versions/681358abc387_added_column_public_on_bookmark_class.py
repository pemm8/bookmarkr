"""Added column public on Bookmark class

Revision ID: 681358abc387
Revises: d81f4f39ee8c
Create Date: 2016-12-28 22:33:02.323741

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '681358abc387'
down_revision = 'd81f4f39ee8c'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('bookmark', sa.Column('public', sa.Boolean(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('bookmark', 'public')
    # ### end Alembic commands ###
