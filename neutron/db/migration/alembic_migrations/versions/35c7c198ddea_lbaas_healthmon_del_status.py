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

"""remove status from HealthMonitor

Revision ID: 35c7c198ddea
Revises: 11c6e18605c8
Create Date: 2013-08-02 23:14:54.037976

"""

# revision identifiers, used by Alembic.
revision = '35c7c198ddea'
down_revision = '11c6e18605c8'

# Change to ['*'] if this migration applies to all plugins

migration_for_plugins = [
    'neutron.services.loadbalancer.plugin.LoadBalancerPlugin',
]


from alembic import context
from alembic import op
from neutron.plugins.common.constants import PENDING_CREATE
import sqlalchemy as sa

from neutron.db import migration


def upgrade(active_plugins=None, options=None):
    if not migration.should_run(active_plugins, migration_for_plugins):
        return
    if migration.migration_engine(context) != 'sqlite':
        op.drop_column('healthmonitors', 'status')
        op.drop_column('healthmonitors', 'status_description')
    else:
        migration.rename_table(entity)
        migration.create_table(
            u'healthmonitors',
            sa.Column(u'tenant_id', sa.String(255), nullable=True),
            sa.Column(u'id', sa.String(36), nullable=False),
            sa.Column(u'type',
                      sa.Enum("PING",
                              "TCP",
                              "HTTP",
                              "HTTPS",
                              name="healthmontiors_type"),
                      nullable=False),
            sa.Column(u'delay', sa.Integer(), nullable=False),
            sa.Column(u'timeout', sa.Integer(), nullable=False),
            sa.Column(u'max_retries', sa.Integer(), nullable=False),
            sa.Column(u'http_method', sa.String(16), nullable=True),
            sa.Column(u'url_path', sa.String(255), nullable=True),
            sa.Column(u'expected_codes', sa.String(64), nullable=True),
            sa.Column(u'admin_state_up', sa.Boolean(), nullable=False),
            sa.PrimaryKeyConstraint(u'id'),
            op=op)


def downgrade(active_plugins=None, options=None):
    if not migration.should_run(active_plugins, migration_for_plugins):
        return

    op.add_column('healthmonitors', sa.Column('status', sa.String(16),
                                              nullable=False,
                                              server_default=PENDING_CREATE))
    op.add_column('healthmonitors', sa.Column('status_description',
                                              sa.String(255)))
