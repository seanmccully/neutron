# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2012 Nicira Networks, Inc.
# All rights reserved.
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
# @author: Dan Wendlandt, Nicira, Inc
#

from abc import ABCMeta
from abc import abstractmethod
from oslo.config import cfg

from neutron.api import extensions
from neutron.api.v2 import attributes as attr
from neutron.api.v2 import base
from neutron.common import exceptions as qexception
from neutron import manager
from neutron.plugins.common import constants
from neutron import quota
from neutron.services.service_base import ServicePluginBase


# L3 Exceptions
class RouterNotFound(qexception.NotFound):
    message = _("Router %(router_id)s could not be found")


class RouterInUse(qexception.InUse):
    message = _("Router %(router_id)s still has active ports")


class RouterInterfaceNotFound(qexception.NotFound):
    message = _("Router %(router_id)s does not have "
                "an interface with id %(port_id)s")


class RouterInterfaceNotFoundForSubnet(qexception.NotFound):
    message = _("Router %(router_id)s has no interface "
                "on subnet %(subnet_id)s")


class RouterInterfaceInUseByFloatingIP(qexception.InUse):
    message = _("Router interface for subnet %(subnet_id)s on router "
                "%(router_id)s cannot be deleted, as it is required "
                "by one or more floating IPs.")


class FloatingIPNotFound(qexception.NotFound):
    message = _("Floating IP %(floatingip_id)s could not be found")


class ExternalGatewayForFloatingIPNotFound(qexception.NotFound):
    message = _("External network %(external_network_id)s is not reachable "
                "from subnet %(subnet_id)s.  Therefore, cannot associate "
                "Port %(port_id)s with a Floating IP.")


class FloatingIPPortAlreadyAssociated(qexception.InUse):
    message = _("Cannot associate floating IP %(floating_ip_address)s "
                "(%(fip_id)s) with port %(port_id)s "
                "using fixed IP %(fixed_ip)s, as that fixed IP already "
                "has a floating IP on external network %(net_id)s.")


class L3PortInUse(qexception.InUse):
    message = _("Port %(port_id)s has owner %(device_owner)s and therefore"
                " cannot be deleted directly via the port API.")


class RouterExternalGatewayInUseByFloatingIp(qexception.InUse):
    message = _("Gateway cannot be updated for router %(router_id)s, since a "
                "gateway to external network %(net_id)s is required by one or "
                "more floating IPs.")

ROUTERS = 'routers'
EXTERNAL_GW_INFO = 'external_gateway_info'

RESOURCE_ATTRIBUTE_MAP = {
    ROUTERS: {
        'id': {'allow_post': False, 'allow_put': False,
               'validate': {'type:uuid': None},
               'is_visible': True,
               'primary_key': True},
        'name': {'allow_post': True, 'allow_put': True,
                 'validate': {'type:string': None},
                 'is_visible': True, 'default': ''},
        'admin_state_up': {'allow_post': True, 'allow_put': True,
                           'default': True,
                           'convert_to': attr.convert_to_boolean,
                           'is_visible': True},
        'status': {'allow_post': False, 'allow_put': False,
                   'is_visible': True},
        'tenant_id': {'allow_post': True, 'allow_put': False,
                      'required_by_policy': True,
                      'validate': {'type:string': None},
                      'is_visible': True},
        EXTERNAL_GW_INFO: {'allow_post': True, 'allow_put': True,
                           'is_visible': True, 'default': None,
                           'enforce_policy': True}
    },
    'floatingips': {
        'id': {'allow_post': False, 'allow_put': False,
               'validate': {'type:uuid': None},
               'is_visible': True,
               'primary_key': True},
        'floating_ip_address': {'allow_post': False, 'allow_put': False,
                                'validate': {'type:ip_address_or_none': None},
                                'is_visible': True},
        'floating_network_id': {'allow_post': True, 'allow_put': False,
                                'validate': {'type:uuid': None},
                                'is_visible': True},
        'router_id': {'allow_post': False, 'allow_put': False,
                      'validate': {'type:uuid_or_none': None},
                      'is_visible': True, 'default': None},
        'port_id': {'allow_post': True, 'allow_put': True,
                    'validate': {'type:uuid_or_none': None},
                    'is_visible': True, 'default': None},
        'fixed_ip_address': {'allow_post': True, 'allow_put': True,
                             'validate': {'type:ip_address_or_none': None},
                             'is_visible': True, 'default': None},
        'tenant_id': {'allow_post': True, 'allow_put': False,
                      'required_by_policy': True,
                      'validate': {'type:string': None},
                      'is_visible': True}
    },
}

l3_quota_opts = [
    cfg.IntOpt('quota_router',
               default=10,
               help=_('Number of routers allowed per tenant, -1 for '
                      'unlimited')),
    cfg.IntOpt('quota_floatingip',
               default=50,
               help=_('Number of floating IPs allowed per tenant, '
                      '-1 for unlimited')),
]
cfg.CONF.register_opts(l3_quota_opts, 'QUOTAS')


class L3(extensions.ExtensionDescriptor):

    @classmethod
    def get_name(cls):
        return "Neutron L3 Router"

    @classmethod
    def get_alias(cls):
        return "router"

    @classmethod
    def get_description(cls):
        return ("Router abstraction for basic L3 forwarding"
                " between L2 Neutron networks and access to external"
                " networks via a NAT gateway.")

    @classmethod
    def get_namespace(cls):
        return "http://docs.openstack.org/ext/neutron/router/api/v1.0"

    @classmethod
    def get_updated(cls):
        return "2012-07-20T10:00:00-00:00"

    @classmethod
    def get_resources(cls):
        """Returns Ext Resources."""
        my_plurals = [(key, key[:-1]) for key in RESOURCE_ATTRIBUTE_MAP.keys()]
        attr.PLURALS.update(dict(my_plurals))
        exts = []
        plugin = manager.NeutronManager.get_service_plugins()[
            constants.L3_ROUTER_NAT]
        for resource_name in ['router', 'floatingip']:
            collection_name = resource_name + "s"
            params = RESOURCE_ATTRIBUTE_MAP.get(collection_name, dict())

            member_actions = {}
            if resource_name == 'router':
                member_actions = {'add_router_interface': 'PUT',
                                  'remove_router_interface': 'PUT'}

            quota.QUOTAS.register_resource_by_name(resource_name)

            controller = base.create_resource(
                collection_name, resource_name, plugin, params,
                member_actions=member_actions,
                allow_pagination=cfg.CONF.allow_pagination,
                allow_sorting=cfg.CONF.allow_sorting)

            ex = extensions.ResourceExtension(collection_name,
                                              controller,
                                              member_actions=member_actions,
                                              attr_map=params)
            exts.append(ex)

        return exts

    def update_attributes_map(self, attributes):
        super(L3, self).update_attributes_map(
            attributes, extension_attrs_map=RESOURCE_ATTRIBUTE_MAP)

    def get_extended_resources(self, version):
        if version == "2.0":
            return RESOURCE_ATTRIBUTE_MAP
        else:
            return {}

    @classmethod
    def get_plugin_interface(cls):
        return RouterPluginBase


class RouterPluginBase(ServicePluginBase):
    __metaclass__ = ABCMeta

    def get_plugin_description(self):
        return 'Router Description'

    def get_plugin_name(self):
        return constants.CORE

    def get_plugin_type(self):
        return constants.CORE

    @abstractmethod
    def create_router(self, context, router):
        pass

    @abstractmethod
    def update_router(self, context, id, router):
        pass

    @abstractmethod
    def get_router(self, context, id, fields=None):
        pass

    @abstractmethod
    def delete_router(self, context, id):
        pass

    @abstractmethod
    def get_routers(self, context, filters=None, fields=None,
                    sorts=None, limit=None, marker=None, page_reverse=False):
        pass

    @abstractmethod
    def add_router_interface(self, context, router_id, interface_info):
        pass

    @abstractmethod
    def remove_router_interface(self, context, router_id, interface_info):
        pass

    @abstractmethod
    def create_floatingip(self, context, floatingip):
        pass

    @abstractmethod
    def update_floatingip(self, context, id, floatingip):
        pass

    @abstractmethod
    def get_floatingip(self, context, id, fields=None):
        pass

    @abstractmethod
    def delete_floatingip(self, context, id):
        pass

    @abstractmethod
    def get_floatingips(self, context, filters=None, fields=None,
                        sorts=None, limit=None, marker=None,
                        page_reverse=False):
        pass

    def get_routers_count(self, context, filters=None):
        raise NotImplementedError()

    def get_floatingips_count(self, context, filters=None):
        raise NotImplementedError()
