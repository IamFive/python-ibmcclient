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
from pprint import pformat

from ibmc_client.resources import BaseResource


class BootSourceOverride(BaseResource):
    """iBMC Boot Source Override Resource Model"""

    def __init__(self, json):
        """Initial a iBMC System Resource Client

        :param json: system resource json format data
        """
        super(BootSourceOverride, self).__init__(json)

    @property
    def target(self):
        return self._json['BootSourceOverrideTarget']

    @property
    def enabled(self):
        return self._json['BootSourceOverrideEnabled']

    @property
    def mode(self):
        return self._json['BootSourceOverrideMode']

    @property
    def supported_boot_devices(self):
        return self._json['BootSourceOverrideTarget@Redfish.AllowableValues']

    def to_str(self):
        """
        Returns the string representation of the model
        """
        return pformat(self._json)

    def __repr__(self):
        """
        For `print` and `pprint`
        """
        return self.to_str()
