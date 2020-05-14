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

# Version 0.0.3
import logging

from ibmc_client import api
from ibmc_client.api.chassis import drive
from ibmc_client.constants import GET
from ibmc_client.resources.chassis import Chassis

LOG = logging.getLogger(__name__)


class IbmcChassisClient(api.BaseApiClient):
    """iBMC chassis API Client"""

    def __init__(self, connector, ibmc_client=None):
        """Initial a iBMC chassis Resource Client

        :param connector: iBMC http connector
        :param ibmc_client: a reference to global
               :class:`~ibmc_client.IBMCClient` object
        """
        super(IbmcChassisClient, self).__init__(connector,
                                                ibmc_client=ibmc_client)
        self._drive_client = drive.IbmcDriveClient(connector,
                                                   ibmc_client=ibmc_client)

    def get(self):
        url = self.connector.chassis_base_url
        resp = self.connector.request(GET, url)
        return Chassis(resp, ibmc_client=self.ibmc_client)

    @property
    def drive(self):
        """Get iBMC chassis drive client
        :return:
        """
        return self._drive_client
