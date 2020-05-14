# coding: utf-8
import copy
import json
import logging
import unittest
import uuid
from random import shuffle
from mock.mock import patch, Mock, call

import responses
from requests import Response

import ibmc_client
from ibmc_client import exceptions, constants, raid_utils
from ibmc_client.api.system import storage
from ibmc_client.api.system.storage import LogicalDisk, \
    sort_and_group_pending_logical_disk_list
from ibmc_client.constants import GET, PATCH, HEADER_IF_MATCH, \
    HEADER_AUTH_TOKEN, POST, DRIVE_FM_STATE_ONLINE
from ibmc_client.exceptions import ControllerHintRequired, \
    NoControllerMatchesHint
from ibmc_client.resources.chassis.drive import Drive
from ibmc_client.resources.system.storage import Storage, Volume
from tests.unittests import BaseUnittest

LOG = logging.getLogger(__name__)
CTRL1_ID = "RAID Card1 Controller"
G_BYTES = 1024 * 1024 * 1024
ALL_RAID_LEVELS = ["RAID0", "RAID1", "RAID5", "RAID6",
                   "RAID10", "RAID50", "RAID60"]


def gb(g_int):
    return g_int * G_BYTES


def build_drive(drive_id, capacity_gb=100, media_type='hdd'):
    return {"id": "Disk%d" % drive_id, "drive_id": drive_id,
            "media_type": media_type, "capacity_bytes": gb(capacity_gb),
            'firmware_state': constants.DRIVE_FM_STATE_UNCONFIG_GOOD}


def build_volume(volume_id, raid_level, span, capacity_gb=100, drives=[]):
    return {"id": "LogicalDrive%d" % volume_id, 'raid_level': raid_level,
            "capacity_bytes": gb(capacity_gb), 'span': span,
            'drives': ["Disk%d" % drive for drive in drives]}


CTRL1_WITH_NON_DRIVES = {
    "id": CTRL1_ID,
    "supported_raid_levels": ALL_RAID_LEVELS,
    "drives": [],
    "volumes": []
}

CTRL1_WITH_16_DEFAULT_DRIVES = {
    "id": CTRL1_ID,
    "supported_raid_levels": ALL_RAID_LEVELS,
    "drives": [build_drive(idx) for idx in range(0, 16)],
    "volumes": [build_volume(0, raid_utils.RAID5, 1, 200, [13, 14, 15])]
}


def mock_ctrl(prototype_list):
    def construct_hint_matches_func(hint):
        def str_equal(string, **kwargs):
            return string == hint

        return str_equal

    prototype_list = copy.deepcopy(prototype_list)

    def mock(prototype):
        drive_data_list = prototype.pop('drives')
        volume_data_list = prototype.pop('volumes')
        ctrl = Mock(spec=Storage, **prototype)
        ctrl.matches.side_effect = construct_hint_matches_func(ctrl.id)

        volumes = []
        used_drive_id_list = []
        for volume_data in volume_data_list:
            drive_id_list = volume_data.get('drives')
            resp = Mock(spec=Response, headers={})
            resp.json.return_value = {
                "@odata.id": volume_data.get('id'),
                "Id": volume_data.get('id'),
                "Name": volume_data.get('id'),
                "CapacityBytes": volume_data.get('capacity_bytes'),
                "Oem": {"Huawei": {
                    "VolumeRaidLevel": volume_data.get('raid_level'),
                    "SpanNumber": volume_data.get('span'),
                }},
                "Links": {
                    "Drives": [{"@odata.id": drive_id}
                               for drive_id in drive_id_list]
                }
            }

            used_drive_id_list.extend(drive_id_list)
            volume = Volume(resp)
            volumes.append(volume)

        ctrl.volumes.return_value = volumes

        drives = []
        for drive_data in drive_data_list:
            resp = Mock(spec=Response, headers={})
            drive_id = drive_data.get('id')
            resp.json.return_value = {
                "@odata.id": drive_id,
                "Id": drive_id,
                "Name": drive_id,
                "SerialNumber": drive_id,
                "CapacityBytes": drive_data.get('capacity_bytes'),
                "MediaType": drive_data.get('media_type').upper(),
                "Protocol": "SATA",
                "Oem": {"Huawei": {
                    "DriveID": drive_data.get('drive_id'),
                    "FirmwareStatus": (DRIVE_FM_STATE_ONLINE
                                       if drive_id in used_drive_id_list
                                       else drive_data.get('firmware_state')),
                }}
            }

            drive = Drive(resp)
            drives.append(drive)

        ctrl.drives.return_value = drives
        return ctrl

    if type(prototype_list) is dict:
        return mock(prototype_list)

    if type(prototype_list) is list:
        return [mock(prototype) for prototype in prototype_list]


def build_default_ctrl(ctrl_id=CTRL1_ID):
    prototype = copy.deepcopy(CTRL1_WITH_16_DEFAULT_DRIVES)
    prototype["id"] = ctrl_id
    return mock_ctrl(prototype)


def mock_logical_disk(ctrl_id, drive_count=0,
                      capacity_bytes=-1):
    ctrl = Mock(controller=Mock(id=ctrl_id))
    ctrl.drives = [] if drive_count == 0 else [Mock()] * drive_count
    ctrl.capacity_bytes = capacity_bytes
    return ctrl


class TestStorageClient(BaseUnittest):
    """ iBMC storage client unit test stubs """

    def testStorageHintMatches(self):
        resp = self.new_mocked_response('get-raid-storage-0.json')
        storage = Storage(resp)

        should_pass_hints = ('RAIDStorage0', 'RAID Card1 Controller')
        for hint in should_pass_hints:
            self.assertTrue(storage.matches(hint), 'correct storage hints')

        should_not_pass_hints = ('RAIDStorage', 'RAID Card Controller', None)
        for hint in should_not_pass_hints:
            self.assertFalse(storage.matches(hint), 'wrong storage hints')

    @responses.activate
    def testGetStorage(self):
        storage_id = 'RAIDStorage0'
        self.start_mocked_http_server([
            responses.Response(
                method=GET,
                url=('https://server1.ibmc.com/redfish/v1/Systems/1'
                     '/Storages/%s' % storage_id),
                json=self.load_json_file('get-raid-storage-0.json')
            )
        ])
        with ibmc_client.connect(**self.server) as client:
            storage = client.system.storage.get('RAIDStorage0')
            self._assertStorage(storage)

    def _assertStorage(self, storage):
        self.assertEqual(storage.id, 'RAIDStorage0',
                         'storage id does not match')
        self.assertEqual(storage.name, 'RAIDStorage0',
                         'storage name does not match')
        self.assertEqual(storage.controller_name, 'RAID Card1 Controller',
                         'storage controller name does not match')
        self.assertEqual(storage.model, 'SAS3508',
                         'storage raid level does not match')
        self.assertEqual(storage.supported_raid_levels,
                         ["RAID0", "RAID1", "RAID5", "RAID6", "RAID10",
                          "RAID50", "RAID60"],
                         'storage supported raid level does not match')
        # self.assertEqual(storage.support_oob, True,
        #                  'storage support OOB does not match')
        self.assertEqual(storage.is_jbod_mode, False,
                         'storage drive number per span does not match')
        self.assertEqual(storage.status.state, 'Enabled',
                         'storage state does not match')
        self.assertEqual(storage.status.health, 'OK',
                         'storage health does not match')

    @responses.activate
    def testLoadStorageVolumes(self):
        storage_id = 'RAIDStorage0'
        resp_list = [
            responses.Response(
                method=GET,
                url=('https://server1.ibmc.com/redfish/v1/Systems/1'
                     '/Storages/%s' % storage_id),
                json=self.load_json_file('get-raid-storage-0.json')
            ),
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
            storage = client.system.storage.get(storage_id)
            volumes = storage.volumes()
            self.assertEqual(len(volumes), 2)
            # volumes will be cached by default
            self.assertEqual(len(volumes), 2)
            self.assertEqual(type(volumes[0]), Volume)
            self.assertEqual(type(volumes[1]), Volume)
            self.assertVolume0(volumes[0])

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

    @responses.activate
    def testForceReloadStorageVolumes(self):
        with patch.object(Storage, '__init__', return_value=None):
            storage = Storage()

            volume_collection_odata_id = Mock()
            storage._json = dict(Volumes=volume_collection_odata_id)
            storage._ibmc_client = Mock()

            rv = [[Mock(), Mock()], [Mock(), Mock()]]
            storage._ibmc_client.load_odata_collection.side_effect = rv
            volumes = storage.volumes()
            self.assertEqual(
                storage._ibmc_client.load_odata_collection.call_count, 1)
            self.assertEqual(volumes, rv[0])
            storage._ibmc_client.load_odata_collection.assert_has_calls(
                [call(volume_collection_odata_id, Volume)]
            )

            storage._ibmc_client.load_odata_collection.reset_mock()
            volumes = storage.volumes()
            self.assertEqual(volumes, rv[0])
            storage._ibmc_client.load_odata_collection.assert_not_called()

            volumes = storage.volumes(force_reload=True)
            self.assertEqual(volumes, rv[1])
            self.assertEqual(
                storage._ibmc_client.load_odata_collection.call_count, 1)
            storage._ibmc_client.load_odata_collection.assert_has_calls(
                [call(volume_collection_odata_id, Volume)]
            )

    @responses.activate
    def testLoadStorageDrives(self):
        storage_id = 'RAIDStorage0'
        resp_list = [
            responses.Response(
                method=GET,
                url=('https://server1.ibmc.com/redfish/v1/Systems/1'
                     '/Storages/%s' % storage_id),
                json=self.load_json_file('get-raid-storage-0.json')
            )
        ]

        drive_idx_list = list(range(0, 8)) + [40, 41]
        for idx in drive_idx_list:
            resp_list.append(responses.Response(
                method=GET,
                url=('https://server1.ibmc.com/redfish/v1/Chassis/1/Drives/'
                     'HDDPlaneDisk%d' % idx),
                json=self.load_json_file('get-drive-%d.json' % idx)
            ))

        self.start_mocked_http_server(resp_list)
        with ibmc_client.connect(**self.server) as client:
            storage = client.system.storage.get(storage_id)
            self.assertEqual(len(storage.drives()), 10)
            # drives will be cached by default
            self.assertEqual(len(storage.drives()), 10)

    @responses.activate
    def testForceReloadStorageDrives(self):
        with patch.object(Storage, '__init__', return_value=None):
            storage = Storage()

            drive_odata_list = [Mock(), Mock()]
            storage._json = dict(Drives=drive_odata_list)
            storage._ibmc_client = Mock()

            return_value = [Mock(), Mock(), Mock(), Mock()]
            storage._ibmc_client.load_odata.side_effect = return_value
            drives = storage.drives()

            self.assertEqual(storage._ibmc_client.load_odata.call_count, 2)
            self.assertEqual(drives, return_value[0:2])
            storage._ibmc_client.load_odata.assert_has_calls(
                [call(odata, Drive) for odata in drive_odata_list]
            )

            storage._ibmc_client.load_odata.reset_mock()
            drives = storage.drives()
            self.assertEqual(drives, return_value[0:2])
            storage._ibmc_client.load_odata.assert_not_called()

            drives = storage.drives(force_reload=True)
            self.assertEqual(drives, return_value[2:])
            self.assertEqual(storage._ibmc_client.load_odata.call_count, 2)
            storage._ibmc_client.load_odata.assert_has_calls(
                [call(odata, Drive) for odata in drive_odata_list]
            )

    @responses.activate
    def testListStorage(self):
        self.start_mocked_http_server([
            responses.Response(
                method=GET,
                url='https://server1.ibmc.com/redfish/v1/Systems/1/Storages',
                json=self.load_json_file('get-raid-storage-collection.json')
            ),
            responses.Response(
                method=GET,
                url=('https://server1.ibmc.com/redfish/v1/Systems/1/Storages'
                     '/RAIDStorage0'),
                json=self.load_json_file('get-raid-storage-0.json')
            )
        ])
        with ibmc_client.connect(**self.server) as client:
            controllers = client.system.storage.list()
            self.assertEqual(len(controllers), 1)
            self._assertStorage(controllers[0])

    @responses.activate
    def testSetStorage(self):
        storage_id = 'RAIDStorage0'
        self.start_mocked_http_server([
            responses.Response(
                method=GET,
                url=('https://server1.ibmc.com/redfish/v1/Systems/1'
                     '/Storages/%s' % storage_id),
                json=self.load_json_file('get-raid-storage-0.json'),
                headers={
                    'ETag': str(uuid.uuid4())
                }
            ),
            responses.Response(
                method=PATCH,
                url=('https://server1.ibmc.com/redfish/v1/Systems/1'
                     '/Storages/%s' % storage_id),
                json=self.load_json_file('get-raid-storage-0.json')
            )
        ])
        with ibmc_client.connect(**self.server) as client:
            controller = client.system.storage.get('RAIDStorage0')
            etag = controller.etag

            controller.set(copy_back=True, smarter_copy_back=True, jbod=True)
            payload = {
                "StorageControllers": [
                    {
                        "Oem": {
                            "Huawei": {
                                "CopyBackState": True,
                                "SmarterCopyBackState": True,
                                "JBODState": True
                            }
                        }
                    }
                ]
            }

            patch_req = self.get_test_api_request(2)
            self.assertEqual(patch_req.headers['Content-Type'],
                             'application/json')
            self.assertEqual(patch_req.headers.get(HEADER_AUTH_TOKEN),
                             self.token)
            self.assertEqual(patch_req.headers.get(HEADER_IF_MATCH), etag)
            self.assertEqual(json.loads(self.get_request_body(patch_req)),
                             payload)

    @responses.activate
    def testRestoreStorage(self):
        storage_id = 'RAIDStorage0'
        self.start_mocked_http_server([
            responses.Response(
                method=GET,
                url=('https://server1.ibmc.com/redfish/v1/Systems/1'
                     '/Storages/%s' % storage_id),
                json=self.load_json_file('get-raid-storage-0.json'),
                headers={
                    'ETag': str(uuid.uuid4())
                }
            ),
            responses.Response(
                method=POST,
                url=('https://server1.ibmc.com/redfish/v1/Systems/1/Storages'
                     '/%s/Actions/Oem/Huawei'
                     '/Storage.RestoreStorageControllerDefaultSettings'
                     % storage_id),
                json=self.load_json_file('restore-storage-response.json')
            )
        ])
        with ibmc_client.connect(**self.server) as client:
            controller = client.system.storage.get('RAIDStorage0')
            controller.restore()

            patch_req = self.get_test_api_request(2)
            self.assertEqual(patch_req.headers['Content-Type'],
                             'application/json')
            self.assertEqual(patch_req.headers.get(HEADER_AUTH_TOKEN),
                             self.token)
            self.assertEqual(json.loads(self.get_request_body(patch_req)),
                             {})

    @responses.activate
    def testSetStorageWithNothing(self):
        with patch.object(Storage, '__init__', return_value=None):
            with self.assertRaises(exceptions.NothingToApplyError):
                controller = Storage()
                controller.set()

    @responses.activate
    @patch('ibmc_client.resources.system.storage.sleep', return_value=None)
    def testDeleteVolumeCollection(self, patched_sleep):
        storage_id = 'RAIDStorage0'
        self.start_mocked_http_server([
            responses.Response(
                method=GET,
                url=('https://server1.ibmc.com/redfish/v1/Systems/1'
                     '/Storages/%s' % storage_id),
                json=self.load_json_file('get-raid-storage-0.json'),
                headers={
                    'ETag': str(uuid.uuid4())
                }
            ),
            responses.Response(
                method=GET,
                url=('https://server1.ibmc.com/redfish/v1/Systems/1/Storages'
                     '/%s/Volumes' % storage_id),
                json=self.load_json_file('get-volume-collection.json'),
                headers={
                    'ETag': str(uuid.uuid4())
                }
            )
        ])
        with ibmc_client.connect(**self.server) as client:
            task = Mock()
            task.raise_if_failed.return_value = None
            with patch.object(client.system.volume, 'delete_by_odata_id',
                              return_value=task) as delete_volume:
                storage = client.system.storage.get('RAIDStorage0')
                storage.delete_volume_collection()
                delete_volume.assert_has_calls([
                    call('/redfish/v1/Systems/1/Storages/RAIDStorage0/Volumes'
                         '/LogicalDrive0'),
                    call('/redfish/v1/Systems/1/Storages/RAIDStorage0/Volumes'
                         '/LogicalDrive1')
                ])

                self.assertEqual(task.raise_if_failed.call_count, 2)

        patched_sleep.assert_called_with(constants.RAID_TASK_EFFECT_SECONDS)

    @responses.activate
    def testDeleteAllRaidConfiguration(self):
        self.start_mocked_http_server([])
        with ibmc_client.connect(**self.server) as client:
            controllers = [build_default_ctrl('Mock1'),
                           build_default_ctrl('Mock2')]
            with patch.object(client.system.storage, 'list',
                              return_value=controllers):
                for ctrl in controllers:
                    for drive in ctrl.drives():
                        drive.restore = Mock()

                client.system.storage.delete_all_raid_configuration()

                for ctrl in controllers:
                    # TODO (qianbiao.ng) do we really need to restore storage?
                    # ctrl.restore.assert_called_once()
                    ctrl.delete_volume_collection.assert_called_once()
                    for drive in ctrl.drives():
                        drive.restore.assert_called_once()

    @responses.activate
    def testDeleteAllRaidConfigurationForNoneCtrl(self):
        self.start_mocked_http_server([])
        with ibmc_client.connect(**self.server) as client:
            controllers = []
            with patch.object(client.system.storage, 'list',
                              return_value=controllers):
                client.system.storage.delete_all_raid_configuration()


class TestInitLogicalDisk(BaseUnittest):
    """ Logical Disk initialize unit test stubs """

    def testInitLogicalDiskWithFullOptions(self):
        options = {
            "volume_name": "os_volume",
            "controller": "RAID Card1 Controller",
            "is_root_volume": True,
            "physical_disks": [
                "Disk1",
                "Disk2",
                "Disk3"
            ],
            "raid_level": "5",
            "size_gb": 'MAX',
            "disk_type": "hdd",
            "interface_type": "sata",
            "number_of_physical_disks": 3
        }

        # test construct
        volume = LogicalDisk(options)
        self.assertEqual(volume.volume_name, "os_volume")
        self.assertEqual(volume._controller_hint,
                         "RAID Card1 Controller")
        self.assertEqual(volume.bootable, True)
        self.assertEqual(volume._physical_disks,
                         ["Disk1", "Disk2", "Disk3"])
        self.assertEqual(volume.raid_setting.name, raid_utils.RAID5)
        self.assertEqual(volume.raid_setting,
                         raid_utils.RAID_SETTINGS.get(raid_utils.RAID5))
        self.assertEqual(volume.capacity_bytes,
                         LogicalDisk.MAX_CAPACITY)
        self.assertEqual(volume._media_type, "hdd")
        self.assertEqual(volume._protocol, "sata")
        self.assertEqual(volume.number_of_physical_disks, 3)

        # test init
        ctrl0 = build_default_ctrl(ctrl_id="RAID Card1 Controller")
        ctrl1 = build_default_ctrl(ctrl_id="RAID Card2 Controller")
        volume.init_ctrl([ctrl0, ctrl1])

        self.assertEqual(volume.controller, ctrl0)

    def testCreateLogicalDiskWithRequiredOptions(self):
        options = {
            "raid_level": "1+0",
            "size_gb": 100,
        }

        volume = LogicalDisk(options)
        self.assertEqual(volume.volume_name, None)
        self.assertEqual(volume._controller_hint, None)
        self.assertEqual(volume.bootable, False)
        self.assertEqual(volume._physical_disks, None)
        self.assertEqual(volume.raid_setting.name, raid_utils.RAID10)
        self.assertEqual(volume.raid_setting,
                         raid_utils.RAID_SETTINGS.get(raid_utils.RAID10))
        self.assertEqual(volume.capacity_bytes,
                         100 * 1024 * 1024 * 1024)
        self.assertEqual(volume._media_type, None)
        self.assertEqual(volume._protocol, None)
        self.assertEqual(volume.number_of_physical_disks, None)

    def testCreateLogicalDiskWithWrongDiskNumber(self):
        options = {
            "raid_level": "1+0",
            "size_gb": 'MAX',
            'controller': 'mock',
            "number_of_physical_disks": 3
        }

        with self.assertRaises(exceptions.InvalidLogicalDiskConfig):
            LogicalDisk(options)

    def testInitCtrl(self):
        options = {
            "volume_name": "os_volume",
            "controller": "RAID Card1 Controller",
            "is_root_volume": "True",
            "physical_disks": [
                "Disk0",
                "Disk1",
                "Disk2",
                "Disk3",
                "Disk4",
                "Disk5"
            ],
            "raid_level": "1+0",
            "size_gb": 'MAX'
        }

        controllers = [build_default_ctrl("RAID Card0 Controller"),
                       build_default_ctrl("RAID Card1 Controller"),
                       build_default_ctrl("RAID Card2 Controller"), ]
        volume = LogicalDisk(options)
        volume.init_ctrl(controllers)
        self.assertEqual(volume.controller, controllers[1])

    def testInitCtrlWithoutHintWhenMultipleCtrl(self):
        options = {
            "raid_level": "1+0",
            "size_gb": 'MAX'
        }
        controllers = [Mock(), Mock(), Mock()]
        with self.assertRaises(ControllerHintRequired):
            volume = LogicalDisk(options)
            volume.init_ctrl(controllers)

    def testInitCtrlWithWrongHintForMultipleCtrl(self):
        options = {
            "raid_level": "1+0",
            "size_gb": 'MAX',
            'controller': 'mock'
        }

        with self.assertRaises(NoControllerMatchesHint):
            controllers = [build_default_ctrl("mock1"),
                           build_default_ctrl("mock2"),
                           build_default_ctrl("mock3")]
            volume = LogicalDisk(options)
            volume.init_ctrl(controllers)

    def testNoCtrlFound(self):
        options = {
            "raid_level": "1+0",
            "size_gb": 'MAX',
            'controller': 'mock'
        }

        with self.assertRaises(exceptions.NoRaidControllerFound):
            controllers = []
            volume = LogicalDisk(options)
            volume.init_ctrl(controllers)

    def testRaidLevelNotSupport(self):
        options = {
            "raid_level": "2",
            "size_gb": 'MAX'
        }

        with self.assertRaises(exceptions.NotSupportedRaidLevel):
            controllers = []
            volume = LogicalDisk(options)
            volume.init_ctrl(controllers)

    def testInitCtrlWithCorrectHintForMultipleCtrl(self):
        options = {
            "raid_level": "1+0",
            "size_gb": 'MAX',
            'controller': 'mock'
        }

        controllers = [build_default_ctrl("mock"),
                       build_default_ctrl("mock1"),
                       build_default_ctrl("mock2")]
        controllers[0].matches.return_value = True
        volume = LogicalDisk(options)
        volume.init_ctrl(controllers)
        self.assertEqual(volume.controller, controllers[0])

    def testInitCtrlWithoutHintForSingleCtrl(self):
        options = {
            "raid_level": "1+0",
            "size_gb": 'MAX'
        }
        controllers = [build_default_ctrl()]
        volume = LogicalDisk(options)
        volume.init_ctrl(controllers)
        self.assertEqual(volume.controller, controllers[0])

    def testInitCtrlWithHintForSingleCtrl(self):
        options = {
            "raid_level": "1+0",
            "size_gb": 'MAX',
            "controller": "RAID Card1 Controller",
        }

        with self.assertRaises(NoControllerMatchesHint):
            controllers = [build_default_ctrl("RAID Card2 Controller")]
            controllers[0].matches.return_value = False
            volume = LogicalDisk(options)
            volume.init_ctrl(controllers)

    def testInitCtrlWithWrongHintForSingleCtrl(self):
        options = {
            "raid_level": "1+0",
            "size_gb": 'MAX',
            "controller": "RAID Card1 Controller",
        }
        controllers = [build_default_ctrl()]
        volume = LogicalDisk(options)
        volume.init_ctrl(controllers)
        self.assertEqual(volume.controller, controllers[0])


class TestSortAndGroupLogicalDisk(BaseUnittest):
    """ sort Logical Disk sort unit test stubs """

    def test(self):
        ctrl1_id = "ctrl 1"
        ctrl2_id = "ctrl 2"
        g_bytes = 1024 * 1024 * 1024

        disk1 = mock_logical_disk(ctrl1_id)
        disk2 = mock_logical_disk(ctrl1_id, drive_count=10)
        disk3 = mock_logical_disk(ctrl1_id, drive_count=5)
        disk4 = mock_logical_disk(
            ctrl1_id, drive_count=10, capacity_bytes=g_bytes)
        disk5 = mock_logical_disk(
            ctrl1_id, drive_count=6, capacity_bytes=g_bytes)
        disk6 = mock_logical_disk(
            ctrl1_id, drive_count=5, capacity_bytes=g_bytes)
        disk7 = mock_logical_disk(
            ctrl1_id, drive_count=5, capacity_bytes=2 * g_bytes)
        disk8 = mock_logical_disk(ctrl1_id, capacity_bytes=1)
        disk9 = mock_logical_disk(ctrl1_id, capacity_bytes=g_bytes)
        disk10 = mock_logical_disk(ctrl1_id, capacity_bytes=2 * g_bytes)

        disk11 = mock_logical_disk(ctrl2_id)
        disk12 = mock_logical_disk(ctrl2_id, drive_count=10)
        disk13 = mock_logical_disk(ctrl2_id, drive_count=5)
        disk14 = mock_logical_disk(
            ctrl2_id, drive_count=10, capacity_bytes=g_bytes)
        disk15 = mock_logical_disk(
            ctrl2_id, drive_count=6, capacity_bytes=g_bytes)
        disk16 = mock_logical_disk(
            ctrl2_id, drive_count=5, capacity_bytes=g_bytes)
        disk17 = mock_logical_disk(
            ctrl2_id, drive_count=5, capacity_bytes=1)
        disk18 = mock_logical_disk(ctrl2_id, capacity_bytes=1)
        disk19 = mock_logical_disk(ctrl2_id, capacity_bytes=g_bytes)
        disk20 = mock_logical_disk(ctrl2_id, capacity_bytes=2 * g_bytes)

        logical_disks = [
            disk1, disk2, disk3, disk4, disk5, disk6, disk7, disk8,
            disk9,
            disk10, disk11, disk12, disk13, disk14, disk15, disk16,
            disk17,
            disk18, disk19, disk20,
        ]
        shuffle(logical_disks)
        grouped = sort_and_group_pending_logical_disk_list(
            logical_disks)

        # self.assertEqual(list(grouped.keys()), [ctrl2_id, ctrl1_id])

        logical_disk_list1 = grouped.get(ctrl1_id)
        logical_disk_list2 = grouped.get(ctrl2_id)
        self.assertEqual(len(logical_disk_list1), 10)
        self.assertEqual(len(logical_disk_list2), 10)

        self.assertEqual(logical_disk_list1,
                         [disk4, disk2, disk5, disk7, disk6, disk3,
                          disk10, disk9, disk8, disk1, ])

        self.assertEqual(logical_disk_list2,
                         [disk14, disk12, disk15, disk16, disk17,
                          disk13,
                          disk20, disk19, disk18, disk11, ])


class TestRaidStorageConfigurationClient(TestStorageClient):
    """ iBMC storage client unit test stubs """

    def testBuildDiskGroup(self):
        ctrl = build_default_ctrl()
        disk_groups = storage.build_disk_groups(ctrl)
        self.assertEqual(len(disk_groups), 1)
        dg = disk_groups[0]

        self.assertEqual(dg.used_capacity_bytes,
                         (sum(volume.capacity_bytes
                              for volume in ctrl.volumes())))
        self.assertEqual(dg.drives, [drive for drive in ctrl.drives()
                                     if drive.id in ["Disk13", "Disk14",
                                                     "Disk15"]])
        self.assertEqual(dg.raid_setting,
                         raid_utils.RAID_SETTINGS.get(raid_utils.RAID5))
        self.assertEqual(dg.span_number, 1)
        self.assertEqual(dg.overhead, 1)
        self.assertEqual(dg.capacity_bytes, gb(200))
        self.assertEqual(dg.used_capacity_bytes, gb(200))
        self.assertEqual(str(dg),
                         "PhysicalDiskGroup(RAID5-Disk13,Disk14,Disk15)")

    def testBuildDiskGroupWithMultipleVolume(self):
        prototype = copy.deepcopy(CTRL1_WITH_16_DEFAULT_DRIVES)
        prototype['volumes'] = [
            build_volume(0, raid_utils.RAID50, 3, 200, range(0, 9)),
            build_volume(1, raid_utils.RAID50, 3, 100, range(0, 9)),
            build_volume(2, raid_utils.RAID10, 2, 100, range(9, 13)),
        ]
        ctrl = mock_ctrl(prototype)
        disk_groups = storage.build_disk_groups(ctrl)
        self.assertEqual(len(disk_groups), 2)

        dg = disk_groups[0]
        self.assertEqual(dg.used_capacity_bytes,
                         (sum(volume.capacity_bytes
                              for volume in ctrl.volumes()[:2])))
        self.assertEqual(dg.drives, [drive for drive in ctrl.drives()
                                     if drive.drive_id in range(0, 9)])
        self.assertEqual(dg.raid_setting,
                         raid_utils.RAID_SETTINGS.get(raid_utils.RAID50))
        self.assertEqual(dg.span_number, 3)
        self.assertEqual(dg.overhead, 3)
        self.assertEqual(dg.capacity_bytes, gb(600))
        self.assertEqual(dg.used_capacity_bytes, gb(300))
        disks = ','.join(["Disk%d" % idx for idx in range(0, 9)])
        self.assertEqual(str(dg), "PhysicalDiskGroup(RAID50-%s)" % disks)

        dg1 = disk_groups[1]
        self.assertEqual(dg1.used_capacity_bytes,
                         (sum(volume.capacity_bytes
                              for volume in ctrl.volumes()[2:])))
        self.assertEqual(dg1.drives, [drive for drive in ctrl.drives()
                                      if drive.drive_id in range(9, 13)])
        self.assertEqual(dg1.raid_setting,
                         raid_utils.RAID_SETTINGS.get(raid_utils.RAID10))
        self.assertEqual(dg1.span_number, 2)
        self.assertEqual(dg1.overhead, 2)
        self.assertEqual(dg1.capacity_bytes, gb(200))
        self.assertEqual(dg1.used_capacity_bytes, gb(100))
        disks = ','.join(["Disk%d" % idx for idx in range(9, 13)])
        self.assertEqual(str(dg1), "PhysicalDiskGroup(RAID10-%s)" % disks)

    @responses.activate
    def testJbodMode(self):
        logical_disks = [
            {
                "controller": "RAID Card1 Controller",
                "raid_level": "JBOD",
                "size_gb": 100
            }
        ]

        self.start_mocked_http_server([
            responses.Response(
                method=GET,
                url='https://server1.ibmc.com/redfish/v1/Systems/1/Storages',
                json=self.load_json_file('get-raid-storage-collection.json')
            ),
            responses.Response(
                method=GET,
                url=('https://server1.ibmc.com/redfish/v1/Systems/1/Storages'
                     '/RAIDStorage0'),
                json=self.load_json_file('get-raid-storage-0.json'),
                headers={
                    'ETag': str(uuid.uuid4())
                }
            ),
            responses.Response(
                method=PATCH,
                url=('https://server1.ibmc.com/redfish/v1/Systems/1/Storages'
                     '/RAIDStorage0'),
                json=self.load_json_file('get-raid-storage-0.json')
            )
        ])
        with ibmc_client.connect(**self.server) as client:
            client.system.storage.apply_raid_configuration(logical_disks)
            payload = {
                "StorageControllers": [
                    {
                        "Oem": {
                            "Huawei": {
                                "JBODState": True
                            }
                        }
                    }
                ]
            }

            patch_req = self.get_test_api_request(3)
            self.assertEqual(json.loads(self.get_request_body(patch_req)),
                             payload)

    @responses.activate
    @patch('ibmc_client.api.system.storage.time')
    def testApplyRaidConfiguration(self, patched_time):
        self.start_mocked_http_server([])
        with ibmc_client.connect(**self.server) as client:
            from tests.unittests import test_apply_raid_config_cases
            for case in test_apply_raid_config_cases.apply_raid_config_cases:
                LOG.info("process apply raid config:: %(name)s", case)
                controllers = mock_ctrl(case.get('controllers'))
                with patch.object(client.system.volume, 'create') as create:
                    with patch.object(client.system.storage, 'list',
                                      return_value=controllers):
                        logical_disks = case.get('logical_disks')
                        client.system.storage.apply_raid_configuration(
                            logical_disks)
                        create.assert_has_calls([
                            call(**pending)
                            for pending in case.get('pending_volumes')
                        ])

                        self.assertEqual(patched_time.sleep.call_count,
                                         create.call_count)
                        patched_time.reset_mock()

    @responses.activate
    def testCombineJbodAndOtherRaidLevel(self):
        self.start_mocked_http_server([])
        with ibmc_client.connect(**self.server) as client:
            controllers = [build_default_ctrl()]
            with self.assertRaises(exceptions.InvalidLogicalDiskConfig) as c:
                with patch.object(client.system.storage, 'list',
                                  return_value=controllers):
                    logical_disks = [{
                        "raid_level": "RAID50",
                        "size_gb": 'max',
                    }, {
                        "raid_level": "JBOD",
                        "size_gb": 'max',
                    }]
                    client.system.storage.apply_raid_configuration(
                        logical_disks)

            self.assertIn('JBOD mode could not work with other RAID '
                          'level.', c.exception.message)

    @responses.activate
    def testNonShareWithWrongSpecifiedDisks(self):
        self.start_mocked_http_server([])
        with ibmc_client.connect(**self.server) as client:
            controllers = [build_default_ctrl()]
            with self.assertRaises(exceptions.NoDriveMatchesHint) as c:
                with patch.object(client.system.storage, 'list',
                                  return_value=controllers):
                    logical_disks = [{
                        "raid_level": "RAID1",
                        "size_gb": 'max',
                        "physical_disks": ["Disk0", "Disk31"]
                    }]
                    client.system.storage.apply_raid_configuration(
                        logical_disks)
            self.assertIn(
                ('No available physical disk matches hint: Disk31, '
                 'media-type: any, protocol: any.'),
                c.exception.message)

    @responses.activate
    def testShareWithWrongSpecifiedDisks(self):
        self.start_mocked_http_server([])
        with ibmc_client.connect(**self.server) as client:
            controllers = [build_default_ctrl()]
            with self.assertRaises(exceptions.NoDriveMatchesHint) as c:
                with patch.object(client.system.storage, 'list',
                                  return_value=controllers):
                    logical_disks = [{
                        "raid_level": "RAID1",
                        "size_gb": 'max',
                        "physical_disks": ["Disk0", "Disk31"],
                        "share_physical_disks": True
                    }]
                    client.system.storage.apply_raid_configuration(
                        logical_disks)
            self.assertIn(
                ('No available physical disk matches hint: Disk31, '
                 'media-type: any, protocol: any.'),
                c.exception.message)

    @responses.activate
    def testCtrlNotSupportRaidLevel(self):
        self.start_mocked_http_server([])
        with ibmc_client.connect(**self.server) as client:
            controller = {
                "id": CTRL1_ID,
                "supported_raid_levels": [raid_utils.RAID5, raid_utils.RAID50],
                "drives": [build_drive(idx) for idx in range(0, 16)],
                "volumes": [
                    build_volume(0, raid_utils.RAID5, 1, 200, [13, 14, 15])]
            }
            controllers = mock_ctrl([controller])
            with self.assertRaises(exceptions.NotSupportedRaidLevel) as c:
                with patch.object(client.system.storage, 'list',
                                  return_value=controllers):
                    logical_disks = [{
                        "controller": CTRL1_ID,
                        "raid_level": "6+0",
                        "size_gb": 'max',
                        "physical_disks": ["Disk0", "Disk31"],
                        "share_physical_disks": True
                    }]
                    client.system.storage.apply_raid_configuration(
                        logical_disks)

            self.assertIn(('RAID level 6+0 is supported by controller '
                           'controller.'), c.exception.message)

    @responses.activate
    def testShareWithSpecifiedDisksButRaidLevelNotMatch(self):
        self.start_mocked_http_server([])
        with ibmc_client.connect(**self.server) as client:
            controller = {
                "id": CTRL1_ID,
                "supported_raid_levels": ALL_RAID_LEVELS,
                "drives": [build_drive(idx) for idx in range(0, 16)],
                "volumes": [
                    build_volume(0, raid_utils.RAID50, 1, 200, range(0, 9))]
            }
            controllers = mock_ctrl([controller])
            with self.assertRaises(exceptions.InvalidLogicalDiskConfig) as c:
                with patch.object(client.system.storage, 'list',
                                  return_value=controllers):
                    logical_disks = [{
                        "controller": CTRL1_ID,
                        "raid_level": "5",
                        "size_gb": 'max',
                        "physical_disks": ["Disk0", "Disk1", "Disk2"],
                        "share_physical_disks": True
                    }]
                    client.system.storage.apply_raid_configuration(
                        logical_disks)

            self.assertIn(('Those shareable physical disks has raid-level 5+0,'
                           ' could not be used for required raid-level 5.'),
                          c.exception.message)

    @responses.activate
    def testShareWithSpecifiedDisksButUsedByOthersForSizeMax(self):
        self.start_mocked_http_server([])
        with ibmc_client.connect(**self.server) as client:
            controller = {
                "id": CTRL1_ID,
                "supported_raid_levels": ALL_RAID_LEVELS,
                "drives": [build_drive(idx) for idx in range(0, 16)],
                "volumes": []
            }
            controllers = mock_ctrl([controller])
            with self.assertRaises(exceptions.InvalidLogicalDiskConfig) as c:
                with patch.object(client.system.storage, 'list',
                                  return_value=controllers):
                    logical_disks = [{
                        "raid_level": "1",
                        "size_gb": 100,
                        "physical_disks": ["Disk2", "Disk3"],
                    }, {
                        "raid_level": "5",
                        "size_gb": 'MAX',
                        "physical_disks": ["Disk0", "Disk1", "Disk2"],
                        "share_physical_disks": True
                    }]
                    client.system.storage.apply_raid_configuration(
                        logical_disks)

            self.assertIn(
                'Disk `Disk2` may has been used by other logical disk.',
                c.exception.message)

    @responses.activate
    def testShareWithSpecifiedDisksButUsedByOthersForSizeInt(self):
        self.start_mocked_http_server([])
        with ibmc_client.connect(**self.server) as client:
            controller = {
                "id": CTRL1_ID,
                "supported_raid_levels": ALL_RAID_LEVELS,
                "drives": [build_drive(idx) for idx in range(0, 16)],
                "volumes": []
            }
            controllers = mock_ctrl([controller])
            with self.assertRaises(exceptions.InvalidLogicalDiskConfig) as c:
                with patch.object(client.system.storage, 'list',
                                  return_value=controllers):
                    logical_disks = [{
                        "raid_level": "1",
                        "size_gb": 100,
                        "physical_disks": ["Disk2", "Disk3"],
                    }, {
                        "raid_level": "5",
                        "size_gb": 200,
                        "physical_disks": ["Disk0", "Disk1", "Disk2"],
                        "share_physical_disks": True
                    }]
                    client.system.storage.apply_raid_configuration(
                        logical_disks)

            self.assertIn(
                'Disk `Disk2` may has been used by other logical disk.',
                c.exception.message)

    @responses.activate
    def testShareWithSpecifiedDisksButSpaceNotEnough(self):
        self.start_mocked_http_server([])
        with ibmc_client.connect(**self.server) as client:
            controller = {
                "id": CTRL1_ID,
                "supported_raid_levels": ALL_RAID_LEVELS,
                "drives": [build_drive(idx) for idx in range(0, 16)],
                "volumes": []
            }
            controllers = mock_ctrl([controller])
            with self.assertRaises(exceptions.InvalidLogicalDiskConfig) as c:
                with patch.object(client.system.storage, 'list',
                                  return_value=controllers):
                    logical_disks = [{
                        "raid_level": "5",
                        "size_gb": 500,
                        "physical_disks": ["Disk0", "Disk1", "Disk2"],
                        "share_physical_disks": True
                    }]
                    client.system.storage.apply_raid_configuration(
                        logical_disks)

            self.assertIn(
                ('There are not enough available disk space to create'
                 ' this logical disk.'),
                c.exception.message)

    @responses.activate
    def testShareAutoChooseDisksButNotEnoughSpace(self):
        self.start_mocked_http_server([])
        with ibmc_client.connect(**self.server) as client:
            controller = {
                "id": CTRL1_ID,
                "supported_raid_levels": ALL_RAID_LEVELS,
                "drives": [build_drive(idx) for idx in range(0, 3)],
                "volumes": []
            }
            controllers = mock_ctrl([controller])
            with self.assertRaises(exceptions.InvalidLogicalDiskConfig) as c:
                with patch.object(client.system.storage, 'list',
                                  return_value=controllers):
                    logical_disks = [{
                        "raid_level": "5",
                        "size_gb": 300,
                        "share_physical_disks": True
                    }]
                    client.system.storage.apply_raid_configuration(
                        logical_disks)

            self.assertIn(('There are not enough available disk space to '
                           'create this logical disk.'),
                          c.exception.message)

    @responses.activate
    def testNonShareWithSpecifiedDisksButUsedByOthers(self):
        self.start_mocked_http_server([])
        with ibmc_client.connect(**self.server) as client:
            controller = {
                "id": CTRL1_ID,
                "supported_raid_levels": ALL_RAID_LEVELS,
                "drives": [build_drive(idx) for idx in range(0, 16)],
                "volumes": [
                    build_volume(0, raid_utils.RAID50, 1, 200, range(0, 9))]
            }
            controllers = mock_ctrl([controller])
            with self.assertRaises(exceptions.InvalidLogicalDiskConfig) as c:
                with patch.object(client.system.storage, 'list',
                                  return_value=controllers):
                    logical_disks = [{
                        "raid_level": "1",
                        "size_gb": 300,
                        "physical_disks": ["Disk2", "Disk3"],
                    }]
                    client.system.storage.apply_raid_configuration(
                        logical_disks)

            self.assertIn(('Disk `Disk2` may has been used by other '
                           'logical disk.'), c.exception.message)

    @responses.activate
    def testNonShareWithSpecifiedDisksButNotEnough(self):
        self.start_mocked_http_server([])
        with ibmc_client.connect(**self.server) as client:
            controller = {
                "id": CTRL1_ID,
                "supported_raid_levels": ALL_RAID_LEVELS,
                "drives": [build_drive(idx) for idx in range(0, 16)],
                "volumes": []
            }
            controllers = mock_ctrl([controller])
            with self.assertRaises(exceptions.InvalidLogicalDiskConfig) as c:
                with patch.object(client.system.storage, 'list',
                                  return_value=controllers):
                    logical_disks = [{
                        "raid_level": "1",
                        "size_gb": 300,
                        "physical_disks": ["Disk2", "Disk3"],
                    }]
                    client.system.storage.apply_raid_configuration(
                        logical_disks)

            self.assertIn(('The specified physical disks do not have enough '
                           'space to create a 300G '
                           'logical-disk(raid-level 1)'),
                          c.exception.message)

    @responses.activate
    def testNonShareAutoChooseDisksButNotEnoughSpace(self):
        self.start_mocked_http_server([])
        with ibmc_client.connect(**self.server) as client:
            controller = {
                "id": CTRL1_ID,
                "supported_raid_levels": ALL_RAID_LEVELS,
                "drives": [build_drive(idx) for idx in range(0, 3)],
                "volumes": []
            }
            controllers = mock_ctrl([controller])
            with self.assertRaises(exceptions.InvalidLogicalDiskConfig) as c:
                with patch.object(client.system.storage, 'list',
                                  return_value=controllers):
                    logical_disks = [{
                        "raid_level": "5",
                        "size_gb": 300,
                    }]
                    client.system.storage.apply_raid_configuration(
                        logical_disks)

            self.assertIn(('There are not enough available disk space to '
                           'create this logical disk.'),
                          c.exception.message)


if __name__ == '__main__':
    unittest.main()