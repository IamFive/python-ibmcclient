# Copyright 2019 HUAWEI, Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.

# Version 0.0.2

import logging

from .api.system import IBMCSystemClient
from .connector import Connector

__version__ = "0.1.0"

LOG = logging.getLogger(__name__)


def connect(address, username, password, verify_ca=True):
    return IBMCClient(address, username, password, verify_ca)


class IBMCClient(object):
    """iBMC API Client"""

    def __init__(self, address, username, password, verify_ca):
        self.address = address
        self.username = username
        self.password = password
        self.verify_ca = verify_ca
        self.connector = Connector(address, username, password, verify_ca)

        # initial iBMC resource client
        self._system = IBMCSystemClient(self.connector)

    def __enter__(self):
        self.connector.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.connector.disconnect()

    @property
    def system(self):
        return self._system
