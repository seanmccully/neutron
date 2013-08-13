# vim: tabstop=4 shiftwidth=4 softtabstop=4

# Copyright 2011 OpenStack Foundation.
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

from abc import abstractmethod
import abc

from oslo.config import cfg
from neutron import manager
from neutron.api.v2 import attributes

from neutron.api.extensions import ExtensionDescriptor
from neutron.api.extensions import ResourceExtension
from neutron.api.extensions import PluginInterface
from neutron.openstack.common import jsonutils
from neutron.api.v2.base import create_resource
from neutron.wsgi import Controller

from neutron.plugins.common import constants
from neutron.services.service_base import ServicePluginBase
from neutron.common.exceptions import NotFound


RESOURCE_ATTRIBUTE_MAP = {
    'groups' : {
        'id': {'allow_post': False, 'allow_put': False,
               'validate': {'type:uuid': None},
               'is_visible': True,
               'primary_key': True},
        'name': {'allow_post': True, 'allow_put': True,
                 'validate': {'type:string': None},
                 'default': '', 'is_visible': True},
        'description': {'allow_post': True, 'allow_put': True,
                 'validate': {'type:string': None},
                 'default': '', 'is_visible': True},
        'tenant_id': {'allow_post': True, 'allow_put': False,
                      'validate': {'type:string': None},
                      'required_by_policy': True,
                      'is_visible': True},

        },
}


class AffinityNotFound(NotFound):
    message = _("Affinity %(affinity_id)s could not be found")


class TopologyController(Controller):

    def index(self, request):
        return "All your controller are belong to us"


class TopologyPluginInterface(PluginInterface):

    @abstractmethod
    def create_group(self):
        pass


class TopologyPluginBase(object):
    __metaclass__ = abc.ABCMeta

    def get_plugin_name(self):
        return constants.SDN

    def get_plugin_type(self):
        return constants.SDN

    def get_plugin_description(self):
        return 'Topology service plugin'


class Topology(ExtensionDescriptor):
    path_prefix = '/'

    @classmethod
    def get_name(cls):
        return "Topology Service"

    @classmethod
    def get_alias(cls):
        return "topology"

    @classmethod
    def get_description(cls):
        return "Extension for Topologies service"

    @classmethod
    def get_namespace(cls):
        return "http://www.foundry.att.com/api/ext/pie/v1.0"

    @classmethod
    def get_updated(cls):
        return "2013-08-07T10:00:00-00:00"



    @classmethod
    def get_resources(cls):
        """Returns Ext Resources."""
        my_plurals = [(key, key[:-1]) for key in RESOURCE_ATTRIBUTE_MAP.keys()]
        attributes.PLURALS.update(dict(my_plurals))
        exts = []
        plugin = manager.NeutronManager.get_plugin()
        for resource_name in RESOURCE_ATTRIBUTE_MAP:
            collection_name = resource_name
            params = RESOURCE_ATTRIBUTE_MAP.get(collection_name, dict())

            member_actions = {}

            controller = create_resource(
                collection_name, resource_name, plugin, params,
                member_actions=member_actions,
                allow_pagination=cfg.CONF.allow_pagination,
                allow_sorting=cfg.CONF.allow_sorting)

            ex = ResourceExtension(collection_name,
                                              controller,
                                              member_actions=member_actions,
                                              attr_map=params)
            exts.append(ex)

        return exts

    @classmethod
    def get_plugin_interface(cls):
        return TopologyPluginBase

    def update_attributes_map(self, attributes):
        super(Topology, self).update_attributes_map(
            attributes, extension_attrs_map=RESOURCE_ATTRIBUTE_MAP)

    def get_extended_resources(self, version):
        if version == "2.0":
            return RESOURCE_ATTRIBUTE_MAP
        else:
            return {}


