# Copyright 2019 HUAWEI, Inc. All Rights Reserved.
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

# Version 0.0.2
from ibmc_client.api import BaseApiClient
from ibmc_client.constants import GET
from ibmc_client.resources.system.bios import Bios


class IBMCBiosClient(BaseApiClient):
    """iBMC BIOS API Client"""

    def __init__(self, connector, ibmc_client=None):
        """Initial a iBMC System Resource Client

        :param connector: iBMC http connector
        :param ibmc_client: a reference to global
            :class:`~ibmc_client.IBMCClient` object
        """
        super(IBMCBiosClient, self).__init__(connector, ibmc_client)

    def get(self):
        # TODO (qianbiao.ng) should we detect resource odata id from root?
        # keep it hardcode here for now.
        uri = '%s/Bios' % self.connector.system_base_url
        resp = self.connector.request(GET, uri)
        return Bios(resp, ibmc_client=self.ibmc_client)
