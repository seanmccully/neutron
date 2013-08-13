# vim: tabstop=4 shiftwidth=4 softtabstop=4
#

import sqlalchemy as sa
from neutron.db import model_base
from neutron.db import models_v2
from neutron.extensions import topology
from neutron.db import db_base_plugin_v2 as base_db


class Affinity(model_base.BASEV2, models_v2.HasId, models_v2.HasTenant):
    """Represents a Network Policy Group """

    name = sa.Column(sa.String(255))
    description = sa.Column(sa.String(255))


class TopologyDbMixin(TopologyPluginBase,
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
        except exc.NoResultFound:
            if issubclass(model, Vip):
                raise loadbalancer.VipNotFound(vip_id=id)
            elif issubclass(model, Pool):
                raise loadbalancer.PoolNotFound(pool_id=id)
            elif issubclass(model, Member):
                raise loadbalancer.MemberNotFound(member_id=id)
            elif issubclass(model, HealthMonitor):
                raise loadbalancer.HealthMonitorNotFound(monitor_id=id)
            else:
                raise
        return r

    def _get_group(self, context, id):
        try:
            group = self._get_by_id(context, Affinity, id)
        except exc.NoResultFound:
            raise topology.AffinityNotFound(affinity=id)
        return group

    def get_group(self, context, id, fields=None):   
        group = self._get_group(context, id)
        return self._make_group_dict(group, fields)

    def get_groups(self, context, filters=None, fields=None, limit=None,
                    marker=None, sorts=None, page_reverse=False):   
        marker_obj = self._get_marker_obj(context, 'group', limit, marker)
        return self._get_collection(context, Affinity,
                                    self._make_group_dict,
                                    filters=filters, fields=fields,
                                    sorts=sorts,
                                    limit=limit,
                                    marker_obj=marker_obj,
                                    page_reverse=page_reverse)

    def create_group(self, context, group):
        """Handle creation of a group""" 
        # single request processing
        group = group['group']
        tenant_id = self._get_tenant_id_for_create(context, group)
        with context.session.begin(subtransactions=True):
            args = {'tenant_id': tenant_id,
                    'id': group.get('id') or uuidutils.generate_uuid(),
                    'name': group['name'],
                    'description': group['description']}
            group = Affinity(**args)
            context.session.add(group)

        return self._make_group_dict(group)

    def update_group(self, context, id, group):
        """Handle update of a group"""
        group_dict = group['group']
        with context.session.begin(subtransactions=True):
            group = self._get_group(context, id)
            group.update(group_dict)
        return self._make_group_dict(group)

    def delete_group(self, context, id):
        with context.session.begin(subtransactions=True):
            group = self._get_group(context, id)
            context.session.delete(group)

    def _make_group_dict(self, group, fields=None):
            res = { 'id': group['id'],
                    'tenant_id': group['tenant_id'],
                    'name' : group['name'],
                    'description': group['description']}

            return self._fields(res, fields)
