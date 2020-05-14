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
from typing import Union

import ibmc_client
from ibmc_client.resources import CollectionResource


class BaseApiClient(object):
    """iBMC base API Client"""

    def __init__(self, connector, ibmc_client):
        # type: (ibmc_client.Connector, ibmc_client.IBMCClient) -> None
        self.connector = connector
        self.ibmc_client = ibmc_client

    def load_odata(self, odata_id, odata_type):
        """Load odata resource from odata id

        :param odata_id:    indicates the id of odata
        :param odata_type:  indicates the type of odata (python model class)
        :return: A python model class object represents the odata
        """
        return self.ibmc_client.load_odata(odata_id, odata_type)

    def load_collection_resource(self, collection_odata_id):
        # type: (Union[str, dict]) -> CollectionResource
        """load odata collection resource

        :param collection_odata_id: indicates the id of odata collection
        :return: A :class:`ibmc_client.resources.CollectionResource` object
        """
        return self.ibmc_client.load_collection_resource(collection_odata_id)

    def load_odata_collection(
            self,
            collection_odata_id,  # type: Union[str, dict]
            odata_type  # type: ibmc_client.BaseResource
    ):
        # type: (...) -> list[ibmc_client.BaseResource]
        """load odata collection list by collection odata id

        :param collection_odata_id: indicates the id of odata collection
        :param odata_type: indicates the type of odata (python model class)
        :return: a list of :class:`ibmc_client.resources.BaseResource`
            object which represents the odata collection
        """
        return self.ibmc_client.load_odata_collection(collection_odata_id,
                                                      odata_type)

    def delete_odata(self, odata_id):
        """delete odata resource

        :param odata_id:    indicates the id of odata
        :return response of redfish HTTP delete request
        """
        return self.ibmc_client.delete_odata(odata_id)
