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

from ibmc_client.api.chassis import IbmcChassisClient
from ibmc_client.api.task.task import IbmcTaskClient
from ibmc_client import constants
from ibmc_client.resources import CollectionResource, BaseResource
from .api.system import IbmcSystemClient
from .connector import Connector

__version__ = "0.2.5.1"

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
        self._system = IbmcSystemClient(self.connector, ibmc_client=self)
        self._chassis = IbmcChassisClient(self.connector, ibmc_client=self)
        self._task = IbmcTaskClient(self.connector, ibmc_client=self)

    def __enter__(self):
        self.connector.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.connector.disconnect()

    def load_odata(self, odata_id, odata_type):
        """Load odata resource from odata id

        :param odata_id:    indicates the id of odata
        :param odata_type:  indicates the type of odata (python model class)
        :return: A python model class object represents the odata
        """
        url = self.connector.get_url(odata_id)
        resp = self.connector.request(constants.GET, url)
        return odata_type(resp, ibmc_client=self)

    def load_collection_resource(self, collection_odata_id):
        # type: (str|dict) -> CollectionResource
        """load odata collection resource

        :param collection_odata_id: indicates the id of odata collection
        :return: A :class:`ibmc_client.resources.CollectionResource` object
        """
        return self.load_odata(collection_odata_id, CollectionResource)

    def load_odata_collection(self, collection_odata_id, odata_type):
        # type: (str|dict, BaseResource) -> list[BaseResource]
        """load odata collection list by collection odata id

        :param collection_odata_id: indicates the id of odata collection
        :param odata_type: indicates the type of odata (python model class)
        :return: a list of :class:`ibmc_client.resources.BaseResource`
            object which represents the odata collection
        """
        odata_collection = self.load_collection_resource(collection_odata_id)
        return [self.load_odata(odata, odata_type)
                for odata in odata_collection.resources]

    def delete_odata(self, odata_id):
        """delete odata resource

        :param odata_id:    indicates the id of odata
        :return response of redfish HTTP delete request
        """
        url = self.connector.get_url(odata_id)
        return self.connector.request(constants.DELETE, url)

    @property
    def system(self):
        """reference to ibmc system resource client

        :return: ibmc system resource client
        """
        return self._system

    @property
    def chassis(self):
        """reference to ibmc chassis resource client

        :return: ibmc chassis resource client
        """
        return self._chassis

    @property
    def task(self):
        """reference to ibmc task-service resource client

        :return: ibmc task-service resource client
        """
        return self._task
