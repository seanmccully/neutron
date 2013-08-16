# vim: tabstop=4 shiftwidth=4 softtabstop=4
#
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

from neutron.db.topology import TopologyDbMixin

class TopologyCallbacks(TopologyDbMixin):

    RPC_API_VERSION = '1.0'

    def __init__(self, plugin):
        self.plugin = plugin

    def create_rpc_dispatcher(self):
        return p_rpc.PluginRpcDispatcher([self])



