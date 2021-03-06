"""rich text posts

Revision ID: 13db22a7a5ab
Revises: 50c192f04076
Create Date: 2015-04-07 22:31:21.162359

"""

# revision identifiers, used by Alembic.
revision = '13db22a7a5ab'
down_revision = '50c192f04076'

from alembic import op
import sqlalchemy as sa


def upgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.add_column('posts', sa.Column('body_html', sa.Text(), nullable=True))
    ### end Alembic commands ###


def downgrade():
    ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('posts', 'body_html')
    ### end Alembic commands ###
