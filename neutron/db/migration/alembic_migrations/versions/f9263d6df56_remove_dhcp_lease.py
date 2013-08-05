# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
# Copyright 2013 OpenStack Foundation
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.
#

"""remove_dhcp_lease

Revision ID: f9263d6df56
Revises: c88b6b5fea3
Create Date: 2013-07-17 12:31:33.731197

"""

# revision identifiers, used by Alembic.
revision = 'f9263d6df56'
down_revision = 'c88b6b5fea3'

# Change to ['*'] if this migration applies to all plugins

migration_for_plugins = [
    '*'
]

from alembic import context
from alembic import op
import sqlalchemy as sa

from neutron.db import migration


def upgrade(active_plugins=None, options=None):

    if migration.migration_engine(context) != 'sqlite':
        op.drop_column('ipallocations', u'expiration')
    else:
        migration.rename_table('ipallocations', op)
        migration.create_table(
            'ipallocations',
            sa.Column('port_id', sa.String(length=36), nullable=True),
            sa.Column('ip_address', sa.String(length=64), nullable=False),
            sa.Column('subnet_id', sa.String(length=36), nullable=False),
            sa.Column('network_id', sa.String(length=36), nullable=False),
            sa.ForeignKeyConstraint(['network_id'], ['networks.id'],
                                    ondelete='CASCADE'),
            sa.ForeignKeyConstraint(['port_id'], ['ports.id'],
                                    ondelete='CASCADE'),
            sa.ForeignKeyConstraint(['subnet_id'], ['subnets.id'],
                                    ondelete='CASCADE'),
            sa.PrimaryKeyConstraint('ip_address', 'subnet_id', 'network_id'),
            op=op)


def downgrade(active_plugins=None, options=None):
    op.add_column('ipallocations', sa.Column(u'expiration', sa.DATETIME(),
                  nullable=True))
