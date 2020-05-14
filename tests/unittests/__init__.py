import json
import logging
import os
import unittest
import uuid

import mock
import requests
import responses

from ibmc_client.constants import GET, POST, DELETE, HEADER_ETAG, \
    HEADER_AUTH_TOKEN

requests.packages.urllib3.disable_warnings()
fmt = ('%(asctime)-15s [%(filename)s#%(funcName)s:%(lineno)s] '
       '%(message)s')
logging.basicConfig(format=fmt)
root_log = logging.getLogger()
root_log.setLevel(logging.INFO)


class BaseUnittest(unittest.TestCase):
    address = "https://server1.ibmc.com"
    username = "username"
    password = "password"
    token = str(uuid.uuid4())
    etag = str(uuid.uuid4())
    session_location = "/redfish/v1/SessionService/Sessions/" + token

    def setUp(self):
        self.server = dict(
            address=self.address,
            username=self.username,
            password=self.password,
        )
        self.base_path = os.path.dirname(os.path.realpath(__file__))

    def tearDown(self):
        pass

    def load_json_file(self, filename):
        with open('%s/data/%s' % (self.base_path, filename)) as data_file:
            data = json.load(data_file)
            return data

    @staticmethod
    def get_test_api_request(index):
        return responses.calls[index + 3 - 1].request

    def start_mocked_http_server(self, test_api_responses):
        # redfish root api
        responses.add(responses.Response(
            method=GET,
            url=self.address + '/redfish/v1',
            json=self.load_json_file('redfish.json')
        ))

        # fetch session credential api
        responses.add(self.get_mocked_new_session_response(
            self.session_location))

        # get manager api
        responses.add(responses.Response(
            method=GET,
            url=self.address + '/redfish/v1/Managers',
            json=self.load_json_file('manager-collection.json')
        ))

        for res in test_api_responses:
            responses.add(res)

        # delete session credential api
        responses.add(responses.Response(
            method=DELETE,
            url=self.address + self.session_location
        ))

    def get_mocked_new_session_response(self, location):
        return responses.Response(
            method=POST,
            url=self.address + '/redfish/v1/SessionService/Sessions',
            headers={
                HEADER_AUTH_TOKEN: self.token,
                "Location": location
            },
            content_type='application/json'
        )

    @staticmethod
    def get_request_body(request):
        body = request.body
        if isinstance(body, bytes):
            body = body.decode('utf-8')
        return body

    def new_mocked_response(self, resp_json_file_name, etag=None):
        """create a new mocked response

        :param resp_json_file_name: indicates the response json content file
            name
        :param etag:
        :return:
        """
        _json = self.load_json_file(resp_json_file_name)
        return mock.Mock(json=mock.Mock(return_value=_json),
                         headers={HEADER_ETAG: etag if etag else self.etag})
