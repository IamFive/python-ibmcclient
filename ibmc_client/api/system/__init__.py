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

from ibmc_client import constants
from ibmc_client.api.system.bios import IBMCBiosClient
from ibmc_client.resources.system import System

LOG = logging.getLogger(__name__)


class IBMCSystemClient(object):
    """iBMC API Client"""

    def __init__(self, connector):
        """Initial a iBMC System Resource Client

        :param connector: iBMC http connector
        """
        self.connector = connector
        self._bios = IBMCBiosClient(self.connector)

    def get(self):
        uri = self.connector.system_base_url
        json = self.connector.request('GET', uri).json()
        return System(json, self)

    @property
    def bios(self):
        """Only V5 series servers support this function.
        :return:
        """
        return self._bios

    def reset(self, reset_type):
        """Restart server

        :param reset_type: Reset type
        """
        action_uri = self.get().get_action_uri('ComputerSystem.Reset')
        url = self.connector.get_url(action_uri)
        payload = dict(ResetType=reset_type)
        self.connector.request('POST', url, json=payload)

    def set_boot_source(self, device, mode=None,
                        enabled=constants.BOOT_SOURCE_ENABLED_ONCE):
        """Set system boot source

        :param device: Boot device
        :param mode: Boot mode
        :param enabled: The frequency, whether to set it for the next
            reboot only (BOOT_SOURCE_ENABLED_ONCE) or persistent to all
            future reboots (BOOT_SOURCE_ENABLED_CONTINUOUS) or disabled
            (BOOT_SOURCE_ENABLED_DISABLED).
        """
        payload = {
            'Boot': {
                'BootSourceOverrideTarget': device,
                'BootSourceOverrideEnabled': enabled,
            }
        }
        if mode:
            payload['Boot']['BootSourceOverrideMode'] = mode

        self.connector.request('PATCH', self.connector.system_base_url,
                               json=payload)
        LOG.debug('Set iBMC boot source override succeed')
