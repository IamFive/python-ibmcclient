import json
import logging
import os
import unittest

import responses
import urllib3

urllib3.disable_warnings()
fmt = ('%(asctime)-15s [%(filename)s#%(funcName)s:%(lineno)s] '
       '%(message)s')
logging.basicConfig(format=fmt)
root_log = logging.getLogger()
root_log.setLevel(logging.INFO)


class BaseUnittest(unittest.TestCase):
    address = "https://server1.ibmc.com"
    username = "username"
    password = "password"
    token = "FakeToken"

    def setUp(self):
        self.server = dict(
            address=self.address,
            username=self.username,
            password=self.password,
        )
        self.base_path = os.path.dirname(os.path.realpath(__file__))

    def tearDown(self):
        pass

    def loadJsonFile(self, filename):
        with open('%s/data/%s' % (self.base_path, filename)) as data_file:
            data = json.load(data_file)
            return data

    @staticmethod
    def get_test_api_request(index):
        return responses.calls[index + 3 - 1].request

    def mock_responses(self, test_api_responses):
        # redfish root api
        responses.add(responses.Response(
            method='GET',
            url=self.address + '/redfish/v1',
            json=self.loadJsonFile('redfish.json')
        ))

        # fetch session credential api
        location = "/redfish/v1/SessionService/Sessions/" + self.token
        responses.add(responses.Response(
            method='POST',
            url=self.address + '/redfish/v1/SessionService/Sessions',
            headers={
                'X-Auth-Token': self.token,
                "Location": location
            },
            content_type='application/json'
        ))

        # get manager api
        responses.add(responses.Response(
            method='GET',
            url=self.address + '/redfish/v1/Managers',
            json=self.loadJsonFile('manager-collection.json')
        ))

        for res in test_api_responses:
            responses.add(res)

        # delete session credential api
        responses.add(responses.Response(
            method='DELETE',
            url=self.address + location
        ))

    @staticmethod
    def get_request_body(request):
        body = request.body
        if isinstance(body, bytes):
            body = body.decode('utf-8')
        return body
