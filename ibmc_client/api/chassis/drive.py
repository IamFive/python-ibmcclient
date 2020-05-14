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
from ibmc_client.api import BaseApiClient
from ibmc_client.constants import GET
from ibmc_client.resources.chassis.drive import Drive


class IbmcDriveClient(BaseApiClient):
    """iBMC drive API Client"""

    def __init__(self, connector, ibmc_client=None):
        """Initial a iBMC drive Resource Client

        :param connector: iBMC http connector
        :param ibmc_client: a reference to global
            :class:`~ibmc_client.IBMCClient` object
        """
        super(IbmcDriveClient, self).__init__(connector, ibmc_client)

    def get(self, drive_id):
        """get drive by id

        :param drive_id: indicates the id of drive
        :return: A Drive (:class:`~ibmc_client.resources.chassis.drive.Drive`)
                 object
        """
        url = '%s/Drives/%s' % (self.connector.chassis_base_url, drive_id)
        resp = self.connector.request(GET, url)
        return Drive(resp, ibmc_client=self.ibmc_client)

    def list(self, storage_id):
        """list all drives belong to a storage

        :param storage_id: indicates the id of RAID storage
        :return: A list of  Drive (:class:`~ibmc_client.resources.chassis.drive
            .Drive`) object
        """
        storage = self.ibmc_client.system.storage.get(storage_id)
        return storage.drives()
