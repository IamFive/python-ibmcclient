# coding: utf-8
from __future__ import absolute_import

import json
import unittest
from mock.mock import patch

import responses

import ibmc_client
from ibmc_client import exceptions
from ibmc_client.constants import POST, GET, PATCH, DELETE
from tests.unittests import BaseUnittest

_BOOT_SEQUENCE_MAP = {
    'HardDiskDrive': 'Hdd',
    'DVDROMDrive': 'Cd',
    'PXE': 'Pxe',
}


class TestConnect(BaseUnittest):
    """ iBMC system client unit test stubs """

    @responses.activate
    def testConnect(self):
        self.start_mocked_http_server([])
        with ibmc_client.connect(**self.server) as client:
            assert len(responses.calls) == 3

            request0 = responses.calls[0].request
            self.assertEqual(request0.url, '%s/redfish/v1' % self.address)
            self.assertEqual(client.connector.system_base_url,
                             '/redfish/v1/Systems/1')
            self.assertEqual(client.connector.manager_base_url,
                             '/redfish/v1/Managers/1')
            session_service_path = '/redfish/v1/SessionService'
            self.assertEqual(client.connector.session_service_base_url,
                             session_service_path)

            request1 = responses.calls[1].request
            session_path = "%s%s/Sessions" % (client.connector.address,
                                              session_service_path)
            self.assertEqual(request1.url, session_path)
            self.assertEqual(request1.method, POST)
            self.assertEqual(request1.headers['Content-Type'],
                             'application/json')
            self.assertEqual(json.loads(self.get_request_body(request1)), {
                'UserName': self.username,
                'Password': self.password
            })

            session = client.connector.session
            self.assertEqual(session, {
                'address': self.address,
                'token': self.token,
                'location': '/redfish/v1/SessionService/Sessions/' + self.token
            })

            request2 = responses.calls[2].request
            self.assertEqual(request2.url,
                             '%s/redfish/v1/Managers' % self.address)
            self.assertEqual(client.connector.resource_id, '1')

        assert len(responses.calls) == 4
        request3 = responses.calls[3].request
        self.assertEqual(request3.url,
                         '%s%s' % (self.address, session['location']))
        self.assertEqual(request3.method, DELETE)

    @responses.activate
    def testConnectFailed(self):
        self.start_mocked_http_server([])
        with self.assertRaises(exceptions.IBMCConnectionError):
            with ibmc_client.connect(**self.server) as client:
                client.system.get()

    @patch('ibmc_client.connector.sleep')
    @responses.activate
    def testAutoRetryFor412(self, patched_sleep):
        url = 'https://server1.ibmc.com/redfish/v1/fakepath'
        payload = {'fake': 'payload'}
        response_json = {'message': 'hello ibmc.'}
        self.start_mocked_http_server([
            responses.Response(method=GET, url=url,
                               headers={"ETag": self.etag}),
            responses.Response(method=PATCH, url=url, status=412),
            responses.Response(method=GET, url=url,
                               headers={"ETag": self.etag}),
            responses.Response(method=PATCH, url=url, json=response_json)
        ])
        with ibmc_client.connect(**self.server) as client:
            resp = client.connector.request(PATCH, url, json=payload)
            req = self.get_test_api_request(2)
            self.assertEqual(req.method, PATCH)
            self.assertEqual(req.headers['Content-Type'], 'application/json')
            self.assertEqual(req.headers['X-Auth-Token'], self.token)
            self.assertEqual(req.headers['If-Match'], self.etag)

            retry_req = self.get_test_api_request(4)
            self.assertEqual(retry_req.method, PATCH)
            self.assertEqual(retry_req.headers['Content-Type'],
                             'application/json')
            self.assertEqual(retry_req.headers['X-Auth-Token'], self.token)
            self.assertEqual(retry_req.headers['If-Match'], self.etag)

            self.assertEqual(json.loads(self.get_request_body(retry_req)),
                             payload)
            self.assertEqual(resp.json(), response_json)
            self.assertEqual(patched_sleep.call_count, 1)

    @responses.activate
    def testAutoRetryFor401(self):
        url = 'https://server1.ibmc.com/redfish/v1/fakepath'
        response_json = {'message': 'hello ibmc.'}
        self.start_mocked_http_server([
            responses.Response(method=GET, url=url, status=401,
                               json=self.load_json_file('401.json')),
            self.get_mocked_new_session_response(self.session_location),
            responses.Response(method=GET, url=url, json=response_json),
        ])
        with ibmc_client.connect(**self.server) as client:
            resp = client.connector.request(GET, url)
            req = self.get_test_api_request(1)
            self.assertEqual(req.method, GET)
            self.assertEqual(req.headers['X-Auth-Token'], self.token)

            retry_req = self.get_test_api_request(3)
            self.assertEqual(retry_req.method, GET)
            self.assertEqual(retry_req.url, url)
            self.assertEqual(retry_req.headers['X-Auth-Token'], self.token)
            self.assertEqual(resp.json(), response_json)

    @responses.activate
    def testAutoRetryFailedAgain(self):
        url = 'https://server1.ibmc.com/redfish/v1/fakepath'
        response_json = {'message': 'hello ibmc.'}
        self.start_mocked_http_server([
            responses.Response(method=GET, url=url, status=401,
                               json=self.load_json_file('401.json')),
            self.get_mocked_new_session_response(self.session_location),
            responses.Response(method=GET, url=url, status=401,
                               json=self.load_json_file('401.json')),
        ])
        with self.assertRaises(exceptions.AccessError):
            with ibmc_client.connect(**self.server) as client:
                resp = client.connector.request(GET, url)
                req = self.get_test_api_request(1)
                self.assertEqual(req.method, GET)
                self.assertEqual(req.headers['X-Auth-Token'], self.token)

                retry_req = self.get_test_api_request(3)
                self.assertEqual(retry_req.method, GET)
                self.assertEqual(retry_req.url, url)
                self.assertEqual(retry_req.headers['X-Auth-Token'], self.token)
                self.assertEqual(resp.json(), response_json)


if __name__ == '__main__':
    unittest.main()
