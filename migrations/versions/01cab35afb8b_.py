"""empty message

Revision ID: 01cab35afb8b
Revises: 
Create Date: 2020-05-27 01:17:00.333974

"""
from alembic import op
import sqlalchemy as sa
import json

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import models


# revision identifiers, used by Alembic.
revision = '01cab35afb8b'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    pass
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    pass
    # ### end Alembic commands ###
