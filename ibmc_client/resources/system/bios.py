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
from ibmc_client import constants
from ibmc_client.resources import BaseResource

_BOOT_SEQUENCE_MAP = {
    'HardDiskDrive': constants.BOOT_SOURCE_TARGET_HDD,
    'DVDROMDrive': constants.BOOT_SOURCE_TARGET_CD,
    'PXE': constants.BOOT_SOURCE_TARGET_PXE,
}


class Bios(BaseResource):
    """iBMC System Resource Model"""

    def __init__(self, json):
        """Initial a iBMC System Resource Client

        :param json: bios attribute resource json format data
        """
        super(Bios, self).__init__(json)
        self._attrs = self._json['Attributes']

    @property
    def boot_sequence(self):
        # v5 series server
        keys = [k for k in self._attrs.keys()
                if k.startswith('BootTypeOrder')]
        seq = [self._attrs.get(t) for t in sorted(keys)]
        return [_BOOT_SEQUENCE_MAP.get(t, t) for t in seq]
