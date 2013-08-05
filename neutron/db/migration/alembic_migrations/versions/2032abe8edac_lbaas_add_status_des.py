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

"""LBaaS add status description

Revision ID: 2032abe8edac
Revises: 477a4488d3f4
Create Date: 2013-06-24 06:51:47.308545

"""

# revision identifiers, used by Alembic.
revision = '2032abe8edac'
down_revision = '477a4488d3f4'

# Change to ['*'] if this migration applies to all plugins

migration_for_plugins = [
    'neutron.services.loadbalancer.plugin.LoadBalancerPlugin',
]

from alembic import context
from alembic import op
import sqlalchemy as sa

from neutron.db import migration

ENTITIES = ['vips', 'pools', 'members', 'healthmonitors']


def upgrade(active_plugins=None, options=None):
    if not migration.should_run(active_plugins, migration_for_plugins):
        return

    for entity in ENTITIES:
        op.add_column(entity, sa.Column('status_description', sa.String(255)))


def downgrade(active_plugins=None, options=None):
    if not migration.should_run(active_plugins, migration_for_plugins):
        return

    engine_name = migration.migration_engine(context)
    for entity in ENTITIES:
        if engine_name != 'sqlite':
            op.drop_column(entity, 'status_description')
        else:
            migration.rename_table(entity)
            if entity == 'vips':
                migration.create_table(
                    unicode(entity),
                    sa.Column(u'tenant_id', sa.String(255), nullable=True),
                    sa.Column(u'id', sa.String(36), nullable=False),
                    sa.Column(u'name', sa.String(255), nullable=True),
                    sa.Column(u'description', sa.String(255), nullable=True),
                    sa.Column(u'port_id', sa.String(36), nullable=True),
                    sa.Column(u'protocol_port', sa.Integer(), nullable=False),
                    sa.Column(u'protocol',
                              sa.Enum("HTTP", "HTTPS", "TCP",
                                      name="lb_protocols"),
                              nullable=False),
                    sa.Column(u'pool_id', sa.String(36), nullable=False),
                    sa.Column(u'status', sa.String(16), nullable=False),
                    sa.Column(u'admin_state_up', sa.Boolean(), nullable=False),
                    sa.Column(u'connection_limit', sa.Integer(),
                              nullable=True),
                    sa.ForeignKeyConstraint(['port_id'], ['ports.id'], ),
                    sa.UniqueConstraint('pool_id'),
                    sa.PrimaryKeyConstraint(u'id'),
                    op=op)
            elif entity == 'pools':
                migration.create_table(
                    unicode(entity),
                    sa.Column(u'tenant_id', sa.String(255), nullable=True),
                    sa.Column(u'id', sa.String(36), nullable=False),
                    sa.Column(u'vip_id', sa.String(36), nullable=True),
                    sa.Column(u'name', sa.String(255), nullable=True),
                    sa.Column(u'description', sa.String(255), nullable=True),
                    sa.Column(u'subnet_id', sa.String(36), nullable=False),
                    sa.Column(u'protocol',
                              sa.Enum("HTTP", "HTTPS", "TCP",
                                      name="lb_protocols"),
                              nullable=False),
                    sa.Column(u'lb_method',
                              sa.Enum("ROUND_ROBIN",
                                      "LEAST_CONNECTIONS",
                                      "SOURCE_IP",
                                      name="pools_lb_method"),
                              nullable=False),
                    sa.Column(u'status', sa.String(16), nullable=False),
                    sa.Column(u'admin_state_up', sa.Boolean(), nullable=False),
                    sa.ForeignKeyConstraint(['vip_id'], [u'vips.id'], ),
                    sa.PrimaryKeyConstraint(u'id'),
                    op=op)
            elif entity == 'members':
                migration.create_table(
                    unicode(entity),
                    sa.Column(u'tenant_id', sa.String(255), nullable=True),
                    sa.Column(u'id', sa.String(36), nullable=False),
                    sa.Column(u'pool_id', sa.String(36), nullable=False),
                    sa.Column(u'address', sa.String(64), nullable=False),
                    sa.Column(u'protocol_port', sa.Integer(), nullable=False),
                    sa.Column(u'weight', sa.Integer(), nullable=False),
                    sa.Column(u'status', sa.String(16), nullable=False),
                    sa.Column(u'admin_state_up', sa.Boolean(), nullable=False),
                    sa.ForeignKeyConstraint(['pool_id'], [u'pools.id'], ),
                    sa.PrimaryKeyConstraint(u'id'),
                    op=op)
            elif entity == 'healthmonitors':
                migration.create_table(
                    unicode(entity),
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
                    sa.Column(u'status', sa.String(16), nullable=False),
                    sa.Column(u'admin_state_up', sa.Boolean(), nullable=False),
                    sa.PrimaryKeyConstraint(u'id'),
                    op=op)
            else:
                pass
