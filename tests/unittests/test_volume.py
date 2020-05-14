# coding: utf-8
import json
import unittest
from mock.mock import patch

import responses

import ibmc_client
from ibmc_client.constants import GET, DELETE, VOLUME_INIT_QUICK, POST, PATCH
from tests.unittests import BaseUnittest


class TestVolumeClient(BaseUnittest):
    """ iBMC volume client unit test stubs """

    def assertVolume0(self, volume0):
        self.assertEqual(volume0.id, 'LogicalDrive0',
                         'volume id does not match')
        self.assertEqual(volume0.name, 'LogicalDrive0',
                         'volume name does not match')
        self.assertEqual(volume0.status.state, 'Enabled',
                         'volume state does not match')
        self.assertEqual(volume0.status.health, 'OK',
                         'volume health does not match')
        self.assertEqual(volume0.volume_oem_name, 'os_volume',
                         'volume OEM name does not match')
        self.assertEqual(volume0.raid_level, 'RAID0',
                         'volume raid level does not match')
        self.assertEqual(volume0.span_number, 1,
                         'volume span number does not match')
        self.assertEqual(volume0.drive_number_per_span, 1,
                         'volume drive number per span does not match')
        self.assertEqual(volume0.capacity_bytes, 536870912000,
                         'volume capacity bytes does not match')
        self.assertEqual(volume0.bootable, True,
                         'volume bootable does not match')
        self.assertEqual(volume0.bgi_enabled, True,
                         'volume bgi-enabled does not match')

    def assertVolume1(self, volume1):
        self.assertEqual(volume1.id, 'LogicalDrive1',
                         'volume id does not match')
        self.assertEqual(volume1.name, 'LogicalDrive1',
                         'volume name does not match')
        self.assertEqual(volume1.status.state, 'Enabled',
                         'volume state does not match')
        self.assertEqual(volume1.status.health, 'OK',
                         'volume health does not match')
        self.assertEqual(volume1.volume_oem_name, 'os_volume_2',
                         'volume OEM name does not match')
        self.assertEqual(volume1.raid_level, 'RAID0',
                         'volume raid level does not match')
        self.assertEqual(volume1.span_number, 1,
                         'volume span number does not match')
        self.assertEqual(volume1.drive_number_per_span, 1,
                         'volume drive number per span does not match')
        self.assertEqual(volume1.capacity_bytes, 536870912000,
                         'volume capacity bytes does not match')
        self.assertEqual(volume1.bootable, False,
                         'volume bootable does not match')
        self.assertEqual(volume1.bgi_enabled, True,
                         'volume bgi-enabled does not match')

    @responses.activate
    def testGetVolume(self):
        self.start_mocked_http_server([
            responses.Response(
                method=GET,
                url=('https://server1.ibmc.com/redfish/v1/Systems/1/Storages/'
                     'RAIDStorage0/Volumes/LogicalDrive0'),
                json=self.load_json_file('get-volume-0.json')
            )
        ])
        with ibmc_client.connect(**self.server) as client:
            volume0 = client.system.volume.get('RAIDStorage0', 'LogicalDrive0')
            self.assertVolume0(volume0)

    @responses.activate
    def testListVolume(self):
        storage_id = 'RAIDStorage0'
        resp_list = [
            responses.Response(
                method=GET,
                url=('https://server1.ibmc.com/redfish/v1/Systems/1/Storages'
                     '/%s/Volumes' % storage_id),
                json=self.load_json_file('get-volume-collection.json')
            )
        ]

        volume_ids = [0, 1]
        for volume_id in volume_ids:
            resp_list.append(responses.Response(
                method=GET,
                url=('https://server1.ibmc.com/redfish/v1/Systems/1/Storages'
                     '/%s/Volumes/LogicalDrive%d' % (storage_id, volume_id)),
                json=self.load_json_file('get-volume-%d.json' % volume_id)
            ))

        self.start_mocked_http_server(resp_list)
        with ibmc_client.connect(**self.server) as client:
            volumes = client.system.volume.list('RAIDStorage0')
            self.assertEqual(len(volumes), 2)

            volume0 = volumes[0]
            self.assertVolume0(volume0)
            volume1 = volumes[1]
            self.assertVolume1(volume1)

    @patch('ibmc_client.api.task.task.sleep')
    @responses.activate
    def testDeleteVolume(self, patched_sleep):
        storage_id = 'storage-id'
        volume_id = 'volume-id'

        resp_list = [
            responses.Response(
                method=DELETE,
                url=('https://server1.ibmc.com/redfish/v1/Systems/1/Storages'
                     '/%s/Volumes/%s' % (storage_id, volume_id)),
                json=self.load_json_file('delete-volume-task-response.json')
            )
        ]

        for times in range(0, 9):
            resp_list.append(responses.Response(
                method=GET,
                url='https://server1.ibmc.com/redfish/v1/TaskService/Tasks/1',
                json=self.load_json_file('delete-volume-task-response.json')
            ))

        resp_list.append(responses.Response(
            method=GET,
            url='https://server1.ibmc.com/redfish/v1/TaskService/Tasks/1',
            json=self.load_json_file(
                'delete-volume-task-finished-response.json')
        ))

        self.start_mocked_http_server(resp_list)
        with ibmc_client.connect(**self.server) as client:
            client.system.volume.delete(storage_id, volume_id)
            self.assertEqual(patched_sleep.call_count, 10)

    @responses.activate
    def testInitVolume(self):
        storage_id = 'storage-id'
        volume_id = 'volume-id'

        resp_list = [
            responses.Response(
                method=POST,
                url=('https://server1.ibmc.com/redfish/v1/Systems/1/Storages'
                     '/%s/Volumes/%s/Actions/Volume.Initialize' %
                     (storage_id, volume_id)),
                json=self.load_json_file('quick-init-volume-response.json')
            )
        ]

        self.start_mocked_http_server(resp_list)
        with ibmc_client.connect(**self.server) as client:
            client.system.volume.init(storage_id, volume_id, VOLUME_INIT_QUICK)

    @responses.activate
    def testSetVolumeBootable(self):
        storage_id = 'storage-id'
        volume_id = 'volume-id'

        resp_list = [
            responses.Response(
                method=GET,
                url=('https://server1.ibmc.com/redfish/v1/Systems/1/Storages'
                     '/%s/Volumes/%s' % (storage_id, volume_id)),
                json=self.load_json_file('get-volume-0.json'),
                headers={"ETag": self.etag}
            ),
            responses.Response(
                method=PATCH,
                url=('https://server1.ibmc.com/redfish/v1/Systems/1/Storages'
                     '/%s/Volumes/%s' % (storage_id, volume_id)),
                json=self.load_json_file('set-volume-bootable-response.json')
            )
        ]

        payload = {
            "Oem": {
                "Huawei": {
                    "BootEnable": True
                }
            }
        }

        self.start_mocked_http_server(resp_list)
        with ibmc_client.connect(**self.server) as client:
            odata = client.system.volume.get_volume_odata_id(storage_id,
                                                             volume_id)
            client.system.volume.set_bootable(odata, True)

            patch_req = self.get_test_api_request(2)
            self.assertEqual(patch_req.method, PATCH)
            self.assertEqual(patch_req.headers['Content-Type'],
                             'application/json')
            self.assertEqual(patch_req.headers['X-Auth-Token'], self.token)
            self.assertEqual(patch_req.headers['If-Match'], self.etag)
            self.assertEqual(json.loads(self.get_request_body(patch_req)),
                             payload)

    @patch('ibmc_client.api.task.task.sleep')
    @responses.activate
    def testCreateVolume(self, patched_sleep):
        storage_id = 'RAIDStorage0'
        resp_list = [
            responses.Response(
                method=POST,
                url=('https://server1.ibmc.com/redfish/v1/Systems/1/Storages'
                     '/%s/Volumes' % storage_id),
                json=self.load_json_file(
                    'create-volume-task-init-response.json'),
                headers={"ETag": self.etag}
            ),
            responses.Response(
                method=GET,
                url='https://server1.ibmc.com/redfish/v1/TaskService/Tasks/2',
                json=self.load_json_file(
                    'create-volume-task-complete-response.json'),
            )
        ]

        self.start_mocked_http_server(resp_list)
        with ibmc_client.connect(**self.server) as client:
            with patch.object(client.system.volume,
                              'set_bootable') as set_bootable:
                capacity_bytes = 3999999721472
                volume_name = 'os_volume'
                raid_level = 'RAID0'
                drives = [0, 1]
                span_number = 1
                payload = {
                    'storage_id': storage_id,
                    'volume_name': volume_name,
                    'raid_level': raid_level,
                    'drives': drives,
                    'capacity_bytes': capacity_bytes,
                    'span': span_number,
                    'bootable': True
                }
                volume_id = client.system.volume.create(**payload)
                self.assertEqual(volume_id, 'LogicalDrive0')
                self.assertEqual(patched_sleep.call_count, 1)
                volume_odata_id = client.system.volume.get_volume_odata_id(
                    storage_id, volume_id)
                set_bootable.assert_called_with(volume_odata_id, True)

                patch_req = self.get_test_api_request(1)
            self.assertEqual(patch_req.method, POST)
            self.assertEqual(patch_req.headers['Content-Type'],
                             'application/json')

            payload = {
                "CapacityBytes": capacity_bytes,
                "Oem": {
                    "Huawei": {
                        "VolumeName": volume_name,
                        "VolumeRaidLevel": raid_level,
                        "Drives": drives
                    }
                }
            }
            self.assertEqual(json.loads(self.get_request_body(patch_req)),
                             payload)

    @patch('ibmc_client.api.task.task.sleep')
    @responses.activate
    def testCreateVolumeOnExistsDiskGroup(self, patched_sleep):
        storage_id = 'RAIDStorage0'
        resp_list = [
            responses.Response(
                method=POST,
                url=('https://server1.ibmc.com/redfish/v1/Systems/1/Storages'
                     '/%s/Volumes' % storage_id),
                json=self.load_json_file(
                    'create-volume-task-init-response.json'),
                headers={"ETag": self.etag}
            ),
            responses.Response(
                method=GET,
                url='https://server1.ibmc.com/redfish/v1/TaskService/Tasks/2',
                json=self.load_json_file(
                    'create-volume-task-complete-response.json'),
            )
        ]

        self.start_mocked_http_server(resp_list)
        with ibmc_client.connect(**self.server) as client:
            with patch.object(client.system.volume,
                              'set_bootable') as set_bootable:
                capacity_bytes = 3999999721472
                volume_name = 'os_volume'
                raid_level = None
                drives = [0]
                span_number = None
                payload = {
                    'storage_id': storage_id,
                    'volume_name': volume_name,
                    'raid_level': raid_level,
                    'drives': drives,
                    'capacity_bytes': capacity_bytes,
                    'span': span_number,
                    'bootable': True
                }
                volume_id = client.system.volume.create(**payload)
                self.assertEqual(volume_id, 'LogicalDrive0')
                self.assertEqual(patched_sleep.call_count, 1)
                volume_odata_id = client.system.volume.get_volume_odata_id(
                    storage_id, volume_id)
                set_bootable.assert_called_with(volume_odata_id, True)

                patch_req = self.get_test_api_request(1)
            self.assertEqual(patch_req.method, POST)
            self.assertEqual(patch_req.headers['Content-Type'],
                             'application/json')

            self.assertEqual(json.loads(self.get_request_body(patch_req)),
                             {"CapacityBytes": capacity_bytes,
                              "Oem": {
                                  "Huawei": {
                                      "VolumeName": volume_name,
                                      "Drives": drives
                                  }
                              }})


if __name__ == '__main__':
    unittest.main()
