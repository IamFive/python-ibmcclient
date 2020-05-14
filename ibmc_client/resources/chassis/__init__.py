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

from ibmc_client.resources import BaseResource, PROP_RESOURCE_ID

LOG = logging.getLogger(__name__)


class Chassis(BaseResource):
    """iBMC Chassis Resource Model"""

    @property
    def drives(self):
        _drives = []
        drive_links = self._json.get('Links', {}).get('Drives', [])
        for drive_link in drive_links:
            url = drive_link.get(PROP_RESOURCE_ID)
            drive_id = url.split('/')[-1]
            drive = self._ibmc_client.chassis.drive.get(drive_id)
            _drives.append(drive)

        return _drives
