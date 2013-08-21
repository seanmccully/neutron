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

"""empty message

Revision ID: 4b0b5689d693
Revises: f9263d6df56
Create Date: 2013-08-14 09:37:38.539661

"""

# revision identifiers, used by Alembic.
revision = '4b0b5689d693'
down_revision = '569e98a8132b'

# Change to ['*'] if this migration applies to all plugins

migration_for_plugins = [
    'neutron.plugins.openvswitch.ovs_neutron_plugin.OVSNeutronPluginV2'
]

from alembic import op
import sqlalchemy as sa

from neutron.db import topology
from neutron.db import migration


def upgrade(active_plugins=None, options=None):
    if not migration.should_run(active_plugins, migration_for_plugins):
        return

    
    op.create_table(
        'affinitys',
        sa.Column('id', sa.String(length=36), nullable=False, primary_key=True),
        sa.Column('tenant_id', sa.String(length=255), nullable=True, primary_key=True),
        sa.Column('name', sa.String(length=255), nullable=True),
        sa.Column('status', sa.String(length=16), nullable=False),
        sa.Column('status_description', sa.String(length=255), nullable=True),
        sa.PrimaryKeyConstraint('id', 'tenant_id', name='affinitys_pk'))

    op.create_table(
        'affinitypolicys',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('affinity_id', sa.String(length=36), nullable=False, primary_key=True),
        sa.Column('tenant_id', sa.String(length=255), nullable=True, primary_key=True),
        sa.Column('proto', sa.String(length=10), nullable=True, primary_key=True),
        sa.Column('policy', sa.Text(), nullable=False),
        sa.Column('meta', sa.Text(), nullable=True),
        sa.Column('status', sa.String(length=16), nullable=False),
        sa.Column('status_description', sa.String(length=255), nullable=True),
        sa.ForeignKeyConstraint(['affinity_id'], ['affinitys.id'], name='affinitys_affinitypolicys_fk'),
        sa.PrimaryKeyConstraint('affinity_id', 'tenant_id', 'proto', name='affinitypolicys_pk'))

    op.create_table(
        'affinitymappers',
        sa.Column('affinity_id', sa.String(36), nullable=False, primary_key=True),
        sa.Column('map_type_id', sa.String(36), nullable=False),
        sa.Column('map_types', sa.Enum(*topology.AFFINITY_MAP_TYPES), nullable=False),
        sa.ForeignKeyConstraint(['affinity_id'], ['affinitys.id'], name='affinitys_affinitymappers_fk'))




def downgrade(active_plugins=None, options=None):
    if not migration.should_run(active_plugins, migration_for_plugins):
        return

    op.drop_table('affinitypolicys')
    op.drop_table('affinitys')
    op.drop_table('affinitymappers')
