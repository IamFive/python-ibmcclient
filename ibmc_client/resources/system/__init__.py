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
import logging

from ibmc_client import exceptions
from ibmc_client.resources import BaseResource
from ibmc_client.resources.system.boot_source_override import BootSourceOverride

LOG = logging.getLogger(__name__)


class System(BaseResource):
    """iBMC System Resource Model"""

    @property
    def power_state(self):
        return self._json['PowerState']

    @property
    def boot_source_override(self):
        _boot = self._json['Boot']
        return BootSourceOverride(_boot)

    @property
    def boot_sequence(self):
        if self._json.get('Bios', None):  # v5 series server
            return self._ibmc_client.system.bios.get().boot_sequence
        else:  # V3 series server
            _seq = self._oem['BootupSequence']
            return _seq

    @property
    def is_storage_ready(self):
        key = 'StorageConfigReady'
        # only supported in latest ibmc
        if key in self._oem:
            return self._oem['StorageConfigReady'] == 1
        else:
            feature = 'get StorageConfigReady attribute from System Resource'
            raise exceptions.FeatureNotSupported(feature=feature)
