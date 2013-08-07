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

from neutron.api import extensions
from neutron.openstack.common import jsonutils
from neutron import wsgi

class TopologyController(wsgi.Controller):

    def index(self, request):
        return "All your controller are belong to us"


class TopologyPluginInterface(extensions.PluginInterface):

    @abstractmethod
    def create_group(self):
        pass


class Topology(object):

    def __init__(self):
        pass

    def get_plugin_interface(self):
        return TopologyPluginInterface

    def get_name(self):
        return "Neutron Topology API"

    def get_alias(self):
        return "TOPOLOGY"

    def get_description(self):
        return "Create networks using logical topology semantics"

    def get_namespace(self):
        return "http://www.foundry.att.com/api/ext/pie/v1.0"

    def get_updated(self):
        return "2013-08-06T16:06:00-08:00"

    def get_resources(self):
        resources = []
        resource = extensions.ResourceExtension('topology',
                                                TopologyController())
        resources.append(resource)
        return resources

    def get_actions(self):
        return [extensions.ActionExtension('topology_resources',
                                           'TOPOLOGY:add_group',
                                           self._add_group_handler),
                extensions.ActionExtension('topology_resources',
                                           'TOPOLOGY:delete_group',
                                           self._delete_group_handler)]

    def get_request_extensions(self):
        request_exts = []

        def _group_handler(req, res):
            #NOTE: This only handles JSON responses.
            # You can use content type header to test for XML.
            data = jsonutils.loads(res.body)
            data['TOPOLOGY:groups'] = req.GET.get('groups')
            res.body = jsonutils.dumps(data)
            return res

        req_ext1 = extensions.RequestExtension('GET',
                                               '/topology_resources/:(id)',
                                               _group_handler)
        request_exts.append(req_ext1)

        def _policy_handler(req, res):
            #NOTE: This only handles JSON responses.
            # You can use content type header to test for XML.
            data = jsonutils.loads(res.body)
            data['TOPOLOGY:policies'] = req.GET.get('policies')
            res.body = jsonutils.dumps(data)
            return res

        req_ext2 = extensions.RequestExtension('GET', 
                                               '/topology_resources/:(id)',
                                               _policy_handler)
        request_exts.append(req_ext2)
        return request_exts

    def _add_group_handler(self, input_dict, req, id):
        return "Group {0} Added.".format(
            input_dict['TOPOLOGY:add_group']['name'])

    def _delete_group_handler(self, input_dict, req, id):
        return "Group {0} Deleted.".format(
            input_dict['TOPOLOGY:delete_group']['name'])
