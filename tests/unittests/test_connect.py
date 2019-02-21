# coding: utf-8
from __future__ import absolute_import

import json
import unittest

import responses

import ibmc_client
from ibmc_client import exceptions
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
        self.mock_responses([])
        with ibmc_client.connect(**self.server) as client:
            assert len(responses.calls) == 3

            request0 = responses.calls[0].request
            self.assertEqual(request0.url, '%s/redfish/v1' % self.address)
            self.assertEqual(client.connector.system_base_url,
                             '%s/redfish/v1/Systems/1' % self.address)
            self.assertEqual(client.connector.manager_base_url,
                             '%s/redfish/v1/Managers/1' % self.address)
            session_service_path = ('%s/redfish/v1/SessionService' %
                                    self.address)
            self.assertEqual(client.connector.session_service_base_url,
                             session_service_path)

            request1 = responses.calls[1].request
            self.assertEqual(request1.url, session_service_path + '/Sessions')
            self.assertEqual(request1.method, 'POST')
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
        self.assertEqual(request3.method, 'DELETE')

    @responses.activate
    def testConnectFailed(self):
        self.mock_responses([])
        with self.assertRaises(exceptions.ConnectionError):
            with ibmc_client.connect(**self.server) as client:
                client.system.get()


if __name__ == '__main__':
    unittest.main()
