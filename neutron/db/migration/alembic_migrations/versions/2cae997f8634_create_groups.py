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

"""Creates groups Table

Revision ID: 2cae997f8634
Revises: 52ff27f7567a
Create Date: 2013-08-05 11:38:08.593098

"""

# revision identifiers, used by Alembic.
revision = '2cae997f8634'
down_revision = '569e98a8132b'

# Change to ['*'] if this migration applies to all plugins

migration_for_plugins = [
    'neutron.plugins.openvswitch.ovs_neutron_plugin.OVSNeutronPluginV2'
]

from alembic import op
import sqlalchemy as sa


from neutron.db import migration


def upgrade(active_plugin=None, options=None):
    if not migration.should_run(active_plugin, migration_for_plugins):
        return

    op.create_table(
        'groups',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('tenant_id', sa.String(length=255), nullable=True),
        sa.Column('name', sa.String(length=255), nullable=True),
        sa.Column('description', sa.String(length=255), nullable=True))



def downgrade(active_plugin=None, options=None):
    if not migration.should_run(active_plugin, migration_for_plugins):
        return

    op.drop_table('groups')
