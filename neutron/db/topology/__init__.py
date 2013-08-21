# Copyright 2013 Sean McCully
# All Rights Reserved.
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


import sqlalchemy as sa
from neutron.db import model_base
from neutron.db import models_v2
from neutron.extensions import topology
from neutron.db import db_base_plugin_v2 as base_db
from neutron.openstack.common import uuidutils

AFFINITY_MAP_TYPES = ("PORTS", "ROUTERS", "NETWORKS", )
AFFINITY_MAP_PORTS = 0
AFFINITY_MAP_ROUTERS = 1
AFFINITY_MAP_NETWORKS = 2

def get_affinity_map_label(idx):
    try:
        return AFFINITY_MAP_TYPES[idx]
    except IndexError:
        return None

class Affinity(model_base.BASEV2, models_v2.HasId, models_v2.HasTenant, models_v2.HasStatusDescription):
    """Represents a Network Policy Group """

    name = sa.Column(sa.String(255))


class AffinityPolicy(model_base.BASEV2, models_v2.HasId, models_v2.HasTenant, models_v2.HasStatusDescription):
    """Represents a Network Policy"""

    affinity_id = sa.Column(sa.String(36),
                                   sa.ForeignKey('affinitys.id',
                                                 ondelete="CASCADE"),
                                   nullable=False, primary_key=True)
    proto = sa.Column(sa.String(10), nullable=True, primary_key=True)
    policy = sa.Column(sa.Text(), nullable=True, primary_key=True)
    meta = sa.Column(sa.Text(), nullable=True)
    affinity= sa.orm.relationship(Affinity, backref='policies',
                                  lazy='joined',
                                   cascade="delete")


class AffinityMapper(model_base.BASEV2):

    affinity_id = sa.Column(sa.String(36), 
                            sa.ForeignKey('affinitys.id', ondelete="CASCADE"),
                            nullable=False, primary_key=True)
    map_types = sa.Column(sa.Enum(*AFFINITY_MAP_TYPES), nullable=False)
    map_type_id = sa.Column(sa.String(36))


class TopologyDbMixin(topology.TopologyPluginBase,
                           base_db.CommonDbMixin):
    """Wraps loadbalancer with SQLAlchemy models.

    A class that wraps the implementation of the Neutron loadbalancer
    plugin database access interface using SQLAlchemy models.
    """

    @property
    def _core_plugin(self):
        return manager.NeutronManager.get_plugin()

    def update_status(self, context, model, id, status,
                      status_description=None):
        with context.session.begin(subtransactions=True):
            v_db = self._get_resource(context, model, id)
            v_db.status = status
            # update status_description in two cases:
            # - new value is passed
            # - old value is not None (needs to be updated anyway)
            if status_description or v_db['status_description']:
                v_db.status_description = status_description

    def _get_resource(self, context, model, id):
        try:
            r = self._get_by_id(context, model, id)
        except exc.NoResultFound as _exc:
            if issubclass(model, AffinityPolicy):
                raise topology.AffinityPolicyNotFound(affinity_policy_id=id)
            elif issubclass(model, Affinity):
                raise topology.AffinityNotFound(affinity_id=id)
            else:
                raise _exc
        return r

    def _get_affinity(self, context, id):
        try:
            affinity = self._get_by_id(context, Affinity, id)
        except exc.NoResultFound:
            raise topology.AffinityNotFound(affinity_id=id)
        return affinity

    def get_affinity(self, context, id, fields=None):   
        affinity = self._get_affinity(context, id)
        return self._make_affinity_dict(affinity, fields)

    def get_affinities(self, context, filters=None, fields=None, limit=None,
                    marker=None, sorts=None, page_reverse=False):   
        marker_obj = self._get_marker_obj(context, 'affinity', limit, marker)
        return self._get_collection(context, Affinity,
                                    self._make_affinity_dict,
                                    filters=filters, fields=fields,
                                    sorts=sorts,
                                    limit=limit,
                                    marker_obj=marker_obj,
                                    page_reverse=page_reverse)

    def create_affinity(self, context, affinity):
        """Handle creation of a affinity""" 
        # single request processing
        affinity = affinity['affinity']
        tenant_id = self._get_tenant_id_for_create(context, affinity)
        with context.session.begin(subtransactions=True):
            args = self._sanitize_affinity_dict(affinity)
            affinity = Affinity(**args)
            context.session.add(affinity)
        return self._make_affinity_dict(affinity)

    def update_affinity(self, context, id, affinity):
        """Handle update of a affinity"""
        affinity_dict = affinity['affinity']
        with context.session.begin(subtransactions=True):
            affinity = self._get_affinity(context, id)
            affinity.update(affinity_dict)
            type = sa.Column(sa.String(36), nullable=True, primary_key=True)
        return self._make_affinity_dict(affinity)

    def delete_affinity(self, context, id):
        with context.session.begin(subtransactions=True):
            affinity = self._get_affinity(context, id)
            context.session.delete(affinity)

    def _sanitize_affinity_dict(self, affinity_data):
        res = { 'tenant_id': affinity_data['tenant_id'],
                'name' : affinity_data['name'],
                'status': affinity_data['status']}

        if 'description' in affinity_data:
            res.update({'status_description', affinity_data['description']})
        else:
            res.update({ 'status_description' : affinity_data['status_description']})

        try:
            if 'id' in affinity_data or affinity_data.id:
                res.update({ 'id' : affinity_data['id']})
        except AttributeError as exc:
            pass

        return res 

    def _make_affinity_dict(self, affinity, fields=None):
        res = self._sanitize_affinity_dict(affinity)            
        return self._fields(res, fields)

    def _get_affinity_policy(self, context, id):
        try:
            affinity_policy = self._get_by_id(context, AffinityPolicy, id)
        except exc.NoResultFound:
            raise topology.AffinityPolicyNotFound(affinity_policy_id=id)

        return affinity_policy

    def get_affinity_policy(self, context, id, fields=None):   
        affinity = self._get_affinity_policy(context, id)
        return self._make_affinity_policy_dict(affinity, fields)

    def get_affinity_policies(self, context, filters=None, fields=None, limit=None,
                    marker=None, sorts=None, page_reverse=False):   
        marker_obj = self._get_marker_obj(context, 'affinity_policies', limit, marker)
        return self._get_collection(context, AffinityPolicy,
                                    self._make_affinity_policy_dict,
                                    filters=filters, fields=fields,
                                    sorts=sorts,
                                    limit=limit,
                                    marker_obj=marker_obj,
                                    page_reverse=page_reverse)

    def create_affinity_policy(self, context, affinity_policy):
        """Handle creation of a affinity""" 
        # single request processing
        policy = affinity_policy['affinity_policy']
        tenant_id = self._get_tenant_id_for_create(context, policy)
        with context.session.begin(subtransactions=True):
            args = self._sanitize_affinity_policy(policy)
            affinity_policy = AffinityPolicy(**args)
            context.session.add(affinity_policy)

        return self._make_affinity_policy_dict(affinity)

    def update_affinity_policy(self, context, id, affinity_policy):
        """Handle update of a affinity"""
        affinity_policy_dict = affinity_policy['affinity_policy']
        with context.session.begin(subtransactions=True):
            affinity = self._get_affinity_policy(context, id)
            affinity.update(affinity_policy_dict)
        return self._make_affinity_policy_dict(affinity)

    def delete_affinity_policy(self, context, id):
        with context.session.begin(subtransactions=True):
            affinity = self._get_affinity_policy(context, id)
            context.session.delete(affinity)

    def _sanitize_affinity_policy(self, affinity_policy_data):
        res = { 'tenant_id': affinity_policy_data['tenant_id'],
                'affinity_id' : affinity_policy_data['affinity_id'],
                'policy': affinity_policy_data['policy'],
                'proto' : affinity_policy_data['proto'],
                'status' : affinity_policy_data['status']}
        
        if 'description' in affinity_policy_data:
            res.update({'status_description', affinity_policy_data['description']})
        else:
            res.update({ 'status_description' : affinity_policy_data['status_description']})
        
        try:
            if 'meta' in affinity_policy_data or \
                    affinity_policy_data.meta:
                res.update({ 'meta' : affinity_policy_data['meta']})
        except AttributeError:
            pass

        try:
            if 'id' in affinity_policy_data or affinity_policy_data.id:
                res.update({ 'id' : affinity_policy_data['id']})
        except AttributeError as exc:
            pass

        return res 


    def _make_affinity_policy_dict(self, affinity_policy, fields=None):
        res = self._sanitize_affinity_policy(affinity_policy)
        return self._fields(res, fields)


    def _process_affinity_port_map(self, context, affinity_id, port):
        affinity_map = AffinityMapper(map_type_id=port['id'],
                                      affinity_id=affinity_id,
                                      map_types=\
                                    get_affinity_map_label(AFFINITY_MAP_PORTS))
        context.session.add(affinity_map)



