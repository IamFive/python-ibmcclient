# coding: utf-8
import json
import unittest
from unittest.mock import patch

import responses

import ibmc_client
from ibmc_client import constants
from ibmc_client.resources.chassis.drive import Drive
from tests.unittests import BaseUnittest


class TestChassisDrive(BaseUnittest):
    """ iBMC chassis drive client unit test stubs """

    def testDriveHintMatches(self):
        resp = self.new_mocked_response('get-drive-0.json')
        drive = Drive(resp)

        should_pass_protocol = 'SATA'
        should_pass_media_type = 'HDD'
        should_pass_hints = ('HDDPlaneDisk0', 'Disk0', '0', '38DGK77LF77D')
        for hint in should_pass_hints:
            self.assertTrue(drive.matches(hint), 'correct drive hints')
            self.assertTrue(drive.matches(hint, protocol=should_pass_protocol))
            self.assertTrue(drive.matches(hint,
                                          media_type=should_pass_media_type))
            self.assertTrue(drive.matches(hint, protocol=should_pass_protocol,
                                          media_type=should_pass_media_type))

    def testDriveHintNotMatches(self):
        resp = self.new_mocked_response('get-drive-0.json')
        drive = Drive(resp)

        should_pass_hints = ('HDDPlaneDisk0', 'Disk0', '0', '38DGK77LF77D')
        should_not_pass_hints = ('HDDPlaneDisk', 'Disk', '10', '38DGK77LF77D2')

        should_pass_protocol = 'SATA'
        should_not_pass_protocol = 'SAS'
        should_pass_media_type = 'HDD'
        should_not_pass_media_type = 'SSD'
        for hint in should_not_pass_hints:
            self.assertFalse(drive.matches(hint), 'wrong drive hints')
            self.assertFalse(drive.matches(hint,
                                           protocol=should_pass_protocol))
            self.assertFalse(drive.matches(hint,
                                           media_type=should_pass_media_type))
            self.assertFalse(drive.matches(hint,
                                           protocol=should_pass_protocol,
                                           media_type=should_pass_media_type))

            self.assertFalse(
                drive.matches(hint, protocol=should_not_pass_protocol))
            self.assertFalse(
                drive.matches(hint, media_type=should_not_pass_media_type))
            self.assertFalse(
                drive.matches(hint, protocol=should_not_pass_protocol,
                              media_type=should_not_pass_media_type))

        for hint in should_pass_hints:
            self.assertFalse(
                drive.matches(hint, protocol=should_not_pass_protocol))
            self.assertFalse(
                drive.matches(hint, media_type=should_not_pass_media_type))
            self.assertFalse(
                drive.matches(hint, protocol=should_not_pass_protocol,
                              media_type=should_not_pass_media_type))

    @responses.activate
    def testGetDrive(self):
        self.start_mocked_http_server([
            responses.Response(
                method=constants.GET,
                url=('https://server1.ibmc.com/redfish/v1/Chassis/1/Drives'
                     '/HDDPlaneDisk0'),
                json=self.load_json_file('get-drive-0.json')
            )
        ])
        with ibmc_client.connect(**self.server) as client:
            drive = client.chassis.drive.get('HDDPlaneDisk0')
            self._assertDrive0(drive)

    @responses.activate
    def testListDrive(self):
        storage_id = 'RAIDStorage0'
        resp_list = [
            responses.Response(
                method=constants.GET,
                url=('https://server1.ibmc.com/redfish/v1/Systems/1'
                     '/Storages/%s' % storage_id),
                json=self.load_json_file('get-raid-storage-0.json')
            )
        ]

        drive_idx_list = list(range(0, 8)) + [40, 41]
        for idx in drive_idx_list:
            resp_list.append(responses.Response(
                method=constants.GET,
                url=('https://server1.ibmc.com/redfish/v1/Chassis/1/Drives/'
                     'HDDPlaneDisk%d' % idx),
                json=self.load_json_file('get-drive-%d.json' % idx)
            ))

        self.start_mocked_http_server(resp_list)
        with ibmc_client.connect(**self.server) as client:
            drives = client.chassis.drive.list(storage_id)
            self.assertEqual(len(drives), 10)

            drive0 = drives[0]
            self._assertDrive0(drive0)

            drive40 = drives[-2]
            self._assertDrive40(drive40)

    @responses.activate
    def testSetDriveFirmwareState(self):
        resp = self.new_mocked_response('get-drive-0.json')
        self.start_mocked_http_server([
            responses.Response(
                method=constants.PATCH,
                url=('https://server1.ibmc.com/redfish/v1/Chassis/1/Drives'
                     '/HDDPlaneDisk0'),
                json=resp.json()
            )
        ])
        with ibmc_client.connect(**self.server) as client:
            drive = Drive(resp, ibmc_client=client)
            drive.set(firmware_state=constants.DRIVE_FM_STATE_JBOD)
            patch_req = self.get_test_api_request(1)
            payload = {
                'Oem': {
                    'Huawei': {
                        'FirmwareStatus': constants.DRIVE_FM_STATE_JBOD,
                    }
                }
            }
            self.assertEqual(json.loads(self.get_request_body(patch_req)),
                             payload)

    @responses.activate
    def testSetDriveHotSpareType(self):
        resp = self.new_mocked_response('get-drive-0.json')
        self.start_mocked_http_server([
            responses.Response(
                method=constants.PATCH,
                url=('https://server1.ibmc.com/redfish/v1/Chassis/1/Drives'
                     '/HDDPlaneDisk0'),
                json=resp.json()
            )
        ])
        with ibmc_client.connect(**self.server) as client:
            drive = Drive(resp, ibmc_client=client)
            drive.set(hotspare_type=constants.HOT_SPARE_GLOBAL)
            patch_req = self.get_test_api_request(1)
            self.assertEqual(json.loads(self.get_request_body(patch_req)),
                             {"HotspareType": constants.HOT_SPARE_GLOBAL})

    @responses.activate
    def testSetDrive(self):
        resp = self.new_mocked_response('get-drive-0.json')
        self.start_mocked_http_server([
            responses.Response(
                method=constants.PATCH,
                url=('https://server1.ibmc.com/redfish/v1/Chassis/1/Drives'
                     '/HDDPlaneDisk0'),
                json=resp.json()
            )
        ])
        with ibmc_client.connect(**self.server) as client:
            drive = Drive(resp, ibmc_client=client)
            drive.set(firmware_state=constants.DRIVE_FM_STATE_UNCONFIG_GOOD,
                      hotspare_type=constants.HOT_SPARE_NONE)
            patch_req = self.get_test_api_request(1)
            payload = {
                "HotspareType": constants.HOT_SPARE_NONE,
                'Oem': {
                    'Huawei': {
                        'FirmwareStatus':
                            constants.DRIVE_FM_STATE_UNCONFIG_GOOD
                    }
                }
            }
            self.assertEqual(json.loads(self.get_request_body(patch_req)),
                             payload)

    @responses.activate
    def testRestoreJbodDrive(self):
        resp = self.new_mocked_response('get-drive-fm-jbod-response.json')
        self.start_mocked_http_server([
            responses.Response(
                method=constants.PATCH,
                url=('https://server1.ibmc.com/redfish/v1/Chassis/1/Drives'
                     '/HDDPlaneDisk0'),
                json=resp.json()
            )
        ])
        with ibmc_client.connect(**self.server) as client:
            drive = Drive(resp, ibmc_client=client)
            with patch.object(drive, 'set') as patched_set:
                drive.restore()
                patched_set.assert_called_with(
                    firmware_state=constants.DRIVE_FM_STATE_UNCONFIG_GOOD)

    @responses.activate
    def testRestoreHotSparedDrive(self):
        resp = self.new_mocked_response('get-drive-fm-spare-response.json')
        self.start_mocked_http_server([
            responses.Response(
                method=constants.PATCH,
                url=('https://server1.ibmc.com/redfish/v1/Chassis/1/Drives'
                     '/HDDPlaneDisk0'),
                json=resp.json()
            )
        ])
        with ibmc_client.connect(**self.server) as client:
            drive = Drive(resp, ibmc_client=client)
            with patch.object(drive, 'set') as patched_set:
                drive.restore()
                patched_set.assert_called_with(
                    hotspare_type=constants.HOT_SPARE_NONE)

    @responses.activate
    def testRestoreNothing(self):
        resp = self.new_mocked_response('get-drive-fm-good-response.json')
        self.start_mocked_http_server([
            responses.Response(
                method=constants.PATCH,
                url=('https://server1.ibmc.com/redfish/v1/Chassis/1/Drives'
                     '/HDDPlaneDisk0'),
                json=resp.json()
            )
        ])
        with ibmc_client.connect(**self.server) as client:
            drive = Drive(resp, ibmc_client=client)
            with patch.object(drive, 'set') as patched_set:
                drive.restore()
                self.assertFalse(patched_set.called)

    def _assertDrive0(self, drive0):
        self.assertEqual(drive0.drive_id, 0,
                         'drive oem id does not match')
        self.assertEqual(drive0.id, 'HDDPlaneDisk0',
                         'drive id does not match')
        self.assertEqual(drive0.name, 'Disk0',
                         'drive name does not match')
        self.assertIsNone(drive0.model, 'drive model does not match')
        self.assertEqual(drive0.protocol, 'SATA',
                         'drive protocol does not match')
        self.assertEqual(drive0.media_type, 'HDD',
                         'drive media type does not match')
        self.assertEqual(drive0.manufacturer, 'ATA',
                         'drive manufacturer does not match')
        self.assertEqual(drive0.serial_number, '38DGK77LF77D',
                         'drive serial number does not match')
        self.assertEqual(drive0.status.state, 'Enabled',
                         'drive state does not match')
        self.assertEqual(drive0.status.health, 'OK',
                         'drive health does not match')
        self.assertEqual(drive0.capacity_bytes, 3999999721472,
                         'drive capacity bytes does not match')
        self.assertEqual(drive0.firmware_state,
                         constants.DRIVE_FM_STATE_ONLINE,
                         'drive firmware state does not match')
        self.assertEqual(drive0.hotspare_type,
                         constants.HOT_SPARE_NONE,
                         'drive firmware state does not match')

    def _assertDrive40(self, drive40):
        self.assertEqual(drive40.drive_id, 40,
                         'drive oem id does not match')
        self.assertEqual(drive40.id, 'HDDPlaneDisk40',
                         'drive id does not match')
        self.assertEqual(drive40.name, 'Disk40',
                         'drive name does not match')
        self.assertEqual(drive40.model, 'HUC101860CSS200',
                         'drive model does not match')
        self.assertEqual(drive40.protocol, 'SAS',
                         'drive protocol does not match')
        self.assertEqual(drive40.media_type, 'HDD',
                         'drive media type does not match')
        self.assertEqual(drive40.manufacturer, 'HGST',
                         'drive manufacturer does not match')
        self.assertEqual(drive40.serial_number, '0BHDEM3H',
                         'drive serial number does not match')
        self.assertEqual(drive40.status.state, 'Enabled',
                         'drive state does not match')
        self.assertEqual(drive40.status.health, 'OK',
                         'drive health does not match')
        self.assertEqual(drive40.capacity_bytes, 598999040000,
                         'drive capacity bytes does not match')
        self.assertEqual(drive40.firmware_state,
                         constants.DRIVE_FM_STATE_UNCONFIG_GOOD,
                         'drive firmware state does not match')
        self.assertEqual(drive40.hotspare_type,
                         constants.HOT_SPARE_NONE,
                         'drive firmware state does not match')


if __name__ == '__main__':
    unittest.main()
