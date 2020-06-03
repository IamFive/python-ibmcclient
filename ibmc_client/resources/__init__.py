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

# Resource Property keys
import ibmc_client as ibmc
from ibmc_client import constants

PROP_RESOURCE_ID = '@odata.id'
"""resource(Odata) Id of redfish resource"""

PROP_COLLECTION_MEMBER_COUNT = 'Members@odata.count'
"""collection resource member count"""


class BaseResource(object):
    """iBMC Resource Base Model"""

    _resp = None
    _json = None
    _oem = None
    etag = None

    def __init__(self, resp, ibmc_client=None):
        # type: (dict, ibmc.IBMCClient) -> None
        """Initial a iBMC resource

        :param resp: redfish resource HTTP response from redfish API
        :param ibmc_client: a reference to global
            :class:`~ibmc_client.IBMCClient` object
        """
        self._ibmc_client = ibmc_client
        self._connector = self._ibmc_client.connector if ibmc_client else None
        self.refresh(resp)

    def extra_init_action(self):
        """Per Resource customer init action

        :return:
        """
        pass

    def refresh(self, resp):
        self._resp = resp
        self._json = resp.json()
        self._oem = (self._json['Oem']['Huawei']
                     if self._json.get('Oem') else None)
        self.etag = resp.headers.get(constants.HEADER_ETAG)
        self.extra_init_action()

    @property
    def odata_id(self):
        """get odata id of current resource

        :return: odata id of current resource
        """
        return self._json.get(PROP_RESOURCE_ID)

    def get_action_uri(self, action_name):
        actions = self._json.get('Actions', None)
        _action_name = '#' + action_name
        if _action_name in actions:
            return actions[_action_name]['target']
        elif actions.get('Oem', None):
            actions = actions['Oem']['Huawei']
            if _action_name in actions:
                return actions[_action_name]['target']
        return None  # pragma: no cover

    def to_str(self):
        """
        Returns the string representation of the model
        """
        return pformat(self._json)  # pragma: no cover

    def __repr__(self):
        """
        For `print` and `pprint`
        """
        return self.to_str()


class CollectionResource(BaseResource):
    """iBMC System Resource Model"""

    @property
    def count(self):
        """get all resource odata id of a collection

        :return:
        """
        return self._json.get(PROP_COLLECTION_MEMBER_COUNT, 0)

    @property
    def resources(self):
        """get all resource odata id of a collection

        :return:
        """
        return [member.get(PROP_RESOURCE_ID)
                for member in self._json.get('Members', [])]


class Status(object):
    """iBMC Resource Status Model"""

    def __init__(self, status):
        self._status = status

    @property
    def state(self):
        return self._status.get('State', None)

    @property
    def health(self):
        return self._status.get('Health', None)
