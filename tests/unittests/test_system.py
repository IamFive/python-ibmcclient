# coding: utf-8
import json
import unittest

import responses

import ibmc_client
from ibmc_client import constants, exceptions
from ibmc_client.constants import GET, PATCH, POST
from tests.unittests import BaseUnittest

_BOOT_SEQUENCE_MAP = {
    'HardDiskDrive': 'Hdd',
    'DVDROMDrive': 'Cd',
    'PXE': 'Pxe',
}


class TestSystem(BaseUnittest):
    """ iBMC system client unit test stubs """

    @responses.activate
    def testGetPowerStateForV3Server(self):
        self.start_mocked_http_server([
            responses.Response(
                method=GET,
                url='https://server1.ibmc.com/redfish/v1/Systems/1',
                json=self.load_json_file('system-v3.json')
            )
        ])
        with ibmc_client.connect(**self.server) as client:
            system = client.system.get()
            self.assertEqual(system.power_state, 'On',
                             'power state is not match')

    @responses.activate
    def testGetPowerStateForV5Server(self):
        self.start_mocked_http_server([
            responses.Response(
                method=GET,
                url='https://server1.ibmc.com/redfish/v1/Systems/1',
                json=self.load_json_file('system-v5.json')
            )
        ])
        with ibmc_client.connect(**self.server) as client:
            system = client.system.get()
            self.assertEqual(system.power_state, 'On',
                             'power state is not match')

    @responses.activate
    def testGetBootSequenceForV3(self):
        response_data = self.load_json_file('system-v3.json')
        self.start_mocked_http_server([
            responses.Response(
                method=GET,
                url='https://server1.ibmc.com/redfish/v1/Systems/1',
                json=response_data
            ),
        ])
        with ibmc_client.connect(**self.server) as client:
            system = client.system.get()
            self.assertEqual(system.boot_sequence,
                             response_data['Oem']['Huawei']['BootupSequence'],
                             'Boot Sequence not match')

    @responses.activate
    def testGetBootSequenceForV5(self):
        response_data = self.load_json_file('bios.json')
        self.start_mocked_http_server([
            responses.Response(
                method=GET,
                url='https://server1.ibmc.com/redfish/v1/Systems/1',
                json=self.load_json_file('system-v5.json')
            ),
            responses.Response(
                method=GET,
                url='https://server1.ibmc.com/redfish/v1/Systems/1/Bios',
                json=response_data
            )
        ])
        with ibmc_client.connect(**self.server) as client:
            system = client.system.get()
            attrs = response_data['Attributes']
            _orders = [attrs['BootTypeOrder0'], attrs['BootTypeOrder1'],
                       attrs['BootTypeOrder2'], attrs['BootTypeOrder3']]
            boot_seq = [_BOOT_SEQUENCE_MAP.get(t, t) for t in _orders]
            self.assertEqual(system.boot_sequence, boot_seq,
                             'Boot Sequence not match')

    @responses.activate
    def testGetBootSourceOverride(self):
        self.start_mocked_http_server([
            responses.Response(
                method=GET,
                url='https://server1.ibmc.com/redfish/v1/Systems/1',
                json=self.load_json_file('system-v5.json')
            )
        ])
        with ibmc_client.connect(**self.server) as client:
            system = client.system.get()
            boot_source_override = system.boot_source_override
            self.assertEqual(boot_source_override.enabled,
                             constants.BOOT_SOURCE_ENABLED_DISABLED)
            self.assertEqual(boot_source_override.target,
                             constants.BOOT_SOURCE_TARGET_NONE)
            self.assertEqual(boot_source_override.mode,
                             constants.BOOT_SOURCE_MODE_BIOS)
            self.assertEqual(boot_source_override.supported_boot_devices,
                             ["None", "Pxe", "Floppy", "Cd", "Hdd",
                              "BiosSetup"])

    @responses.activate
    def testResetPower(self):
        response_data = self.load_json_file('bios.json')
        self.start_mocked_http_server([
            responses.Response(
                method=GET,
                url='https://server1.ibmc.com/redfish/v1/Systems/1',
                json=self.load_json_file('system-v5.json')
            ),
            responses.Response(
                method=POST,
                url=('https://server1.ibmc.com'
                     '/redfish/v1/Systems/1/Actions/ComputerSystem.Reset'),
                json=response_data
            )
        ])
        with ibmc_client.connect(**self.server) as client:
            client.system.reset(constants.RESET_FORCE_RESTART)
            req = self.get_test_api_request(2)
            self.assertEqual(req.method, POST)
            self.assertEqual(req.headers['Content-Type'], 'application/json')
            self.assertEqual(req.headers['X-Auth-Token'], self.token)
            self.assertEqual(json.loads(self.get_request_body(req)), {
                'ResetType': constants.RESET_FORCE_RESTART,
            })

    @responses.activate
    def testSetBootSourceOverride(self):
        response_data = self.load_json_file('system-v5.json')
        self.start_mocked_http_server([
            responses.Response(
                method=GET,
                url='https://server1.ibmc.com/redfish/v1/Systems/1',
                json=response_data,
                headers={
                    "ETag": self.etag
                }
            ),
            responses.Response(
                method=PATCH,
                url='https://server1.ibmc.com/redfish/v1/Systems/1',
                json=response_data
            )
        ])
        with ibmc_client.connect(**self.server) as client:
            client.system.set_boot_source(constants.BOOT_SOURCE_TARGET_PXE,
                                          constants.BOOT_SOURCE_MODE_BIOS,
                                          constants.BOOT_SOURCE_ENABLED_ONCE)
            req = self.get_test_api_request(2)
            self.assertEqual(req.method, PATCH)
            self.assertEqual(req.headers['Content-Type'], 'application/json')
            self.assertEqual(req.headers['X-Auth-Token'], self.token)
            self.assertEqual(req.headers['If-Match'], self.etag)

            boot = {
                'BootSourceOverrideTarget': constants.BOOT_SOURCE_TARGET_PXE,
                'BootSourceOverrideEnabled':
                    constants.BOOT_SOURCE_ENABLED_ONCE,
                'BootSourceOverrideMode': constants.BOOT_SOURCE_MODE_BIOS
            }
            self.assertEqual(json.loads(self.get_request_body(req)),
                             {'Boot': boot})

    @responses.activate
    def testIsStorageReadyNotSupported(self):
        self.start_mocked_http_server([
            responses.Response(
                method=GET,
                url='https://server1.ibmc.com/redfish/v1/Systems/1',
                json=self.load_json_file('system-v5.json')
            )
        ])

        with self.assertRaises(exceptions.FeatureNotSupported) as c:
            with ibmc_client.connect(**self.server) as client:
                system = client.system.get()
                system.is_storage_ready

        self.assertIn('Feature is not supported by this iBMC server: get'
                      ' StorageConfigReady attribute from System Resource, '
                      'please check the version of this iBMC server.',
                      c.exception.message)

    @responses.activate
    def testIsStorageReadyReturnTrue(self):
        self.start_mocked_http_server([
            responses.Response(
                method=GET,
                url='https://server1.ibmc.com/redfish/v1/Systems/1',
                json=self.load_json_file('get-system-with-storage-ready.json')
            )
        ])

        with ibmc_client.connect(**self.server) as client:
            system = client.system.get()
            ready = system.is_storage_ready
            self.assertTrue(ready)

    @responses.activate
    def testIsStorageReadyReturnFalse(self):
        self.start_mocked_http_server([
            responses.Response(
                method=GET,
                url='https://server1.ibmc.com/redfish/v1/Systems/1',
                json=self.load_json_file(
                    'get-system-with-storage-not-ready.json')
            )
        ])

        with ibmc_client.connect(**self.server) as client:
            system = client.system.get()
            ready = system.is_storage_ready
            self.assertFalse(ready)


if __name__ == '__main__':
    unittest.main()
