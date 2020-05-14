# Copyright 2020 HUAWEI, Inc. All Rights Reserved.
# Modified upon https://github.com/openstack/sushy
#
# Licensed under the Apache License, Version 2.0 (the "License"); you may
# not use this file except in compliance with the License. You may obtain
# a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
# License for the specific language governing permissions and limitations
# under the License.
import functools
import operator

from ibmc_client import raid_utils
from tests.unittests import test_storage

apply_raid_config_cases = [
    {
        "name": "case-1",
        "logical_disks": [
            {
                "volume_name": "os_volume",
                "controller": test_storage.CTRL1_ID,
                "disk_type": "hdd",
                "raid_level": "RAID1",
                "size_gb": 100
            },
            {
                "volume_name": "os_volume",
                "controller": test_storage.CTRL1_ID,
                "is_root_volume": True,
                "raid_level": "RAID1",
                "size_gb": "MAX"
            },
        ],
        "controllers": [test_storage.CTRL1_WITH_16_DEFAULT_DRIVES],
        "pending_volumes": [
            {'storage_id': 'RAID Card1 Controller',
             'volume_name': 'os_volume', 'raid_level': 'RAID1',
             'drives': [0, 1], 'capacity_bytes': test_storage.gb(100),
             'span': 1, 'bootable': False},
            {'storage_id': 'RAID Card1 Controller',
             'volume_name': 'os_volume', 'raid_level': 'RAID1',
             'drives': [2, 3], 'capacity_bytes': None,
             'span': 1, 'bootable': True}
        ]
    },
    {
        "name": "case-2",
        "logical_disks": [
            {
                "volume_name": "os_volume",
                "raid_level": "RAID1",
                "size_gb": 100
            },
            {
                "volume_name": "os_volume",
                "is_root_volume": True,
                "raid_level": "RAID1",
                "size_gb": "MAX"
            },
        ],
        "controllers": [test_storage.CTRL1_WITH_16_DEFAULT_DRIVES],
        "pending_volumes": [
            {'storage_id': 'RAID Card1 Controller',
             'volume_name': 'os_volume', 'raid_level': 'RAID1',
             'drives': [0, 1], 'capacity_bytes': test_storage.gb(100),
             'span': 1, 'bootable': False},
            {'storage_id': 'RAID Card1 Controller',
             'volume_name': 'os_volume', 'raid_level': 'RAID1',
             'drives': [2, 3], 'capacity_bytes': None,
             'span': 1, 'bootable': True}
        ]
    },
    {
        "name": "case-3",
        "logical_disks": [
            {
                "volume_name": "os_volume",
                "raid_level": "RAID1",
                "size_gb": 100
            },
            {
                "volume_name": "os_volume",
                "is_root_volume": True,
                "raid_level": "RAID1",
                "size_gb": "MAX"
            },
        ],
        "controllers": [{
            "id": test_storage.CTRL1_ID,
            "supported_raid_levels": test_storage.ALL_RAID_LEVELS,
            "drives": functools.reduce(
                operator.iconcat,
                [[test_storage.build_drive(idx, capacity_gb=100)
                  for idx in range(0, 6)],
                 [test_storage.build_drive(idx, capacity_gb=200)
                  for idx in range(6, 16)]], []),
            "volumes": []
        }],
        "pending_volumes": [
            {'storage_id': 'RAID Card1 Controller',
             'volume_name': 'os_volume', 'raid_level': 'RAID1',
             'drives': [0, 1], 'capacity_bytes': test_storage.gb(100),
             'span': 1, 'bootable': False},
            {'storage_id': 'RAID Card1 Controller',
             'volume_name': 'os_volume', 'raid_level': 'RAID1',
             'drives': [6, 7], 'capacity_bytes': None,
             'span': 1, 'bootable': True}
        ]
    },
    {
        "name": "case-4",
        "logical_disks": [
            {
                "volume_name": "os_volume",
                "raid_level": "RAID1",
                "size_gb": 100
            },
            {
                "volume_name": "os_volume",
                "is_root_volume": True,
                "raid_level": "RAID1",
                "size_gb": "MAX"
            },
        ],
        "controllers": [{
            "id": test_storage.CTRL1_ID,
            "supported_raid_levels": test_storage.ALL_RAID_LEVELS,
            "drives": functools.reduce(
                operator.iconcat,
                [[test_storage.build_drive(idx, capacity_gb=200)
                  for idx in range(6, 16)],
                 [test_storage.build_drive(idx, capacity_gb=100)
                  for idx in range(0, 6)]], []),
            "volumes": []
        }],
        "pending_volumes": [
            {'storage_id': 'RAID Card1 Controller',
             'volume_name': 'os_volume', 'raid_level': 'RAID1',
             'drives': [0, 1], 'capacity_bytes': test_storage.gb(100),
             'span': 1, 'bootable': False},
            {'storage_id': 'RAID Card1 Controller',
             'volume_name': 'os_volume', 'raid_level': 'RAID1',
             'drives': [6, 7], 'capacity_bytes': None,
             'span': 1, 'bootable': True}
        ]
    },
    {
        "name": "case-5",
        "logical_disks": [
            {
                "volume_name": "os_volume",
                "raid_level": "RAID1",
                "size_gb": 100
            },
            {
                "volume_name": "os_volume",
                "is_root_volume": True,
                "raid_level": "RAID1",
                "size_gb": "MAX"
            },
        ],
        "controllers": [{
            "id": test_storage.CTRL1_ID,
            "supported_raid_levels": test_storage.ALL_RAID_LEVELS,
            "drives": functools.reduce(
                operator.iconcat,
                [[test_storage.build_drive(idx, capacity_gb=100)
                  for idx in range(0, 1)],
                 [test_storage.build_drive(idx, capacity_gb=200)
                  for idx in range(1, 16)]], []),
            "volumes": []
        }],
        "pending_volumes": [
            {'storage_id': 'RAID Card1 Controller',
             'volume_name': 'os_volume', 'raid_level': 'RAID1',
             'drives': [1, 2], 'capacity_bytes': test_storage.gb(100),
             'span': 1, 'bootable': False},
            {'storage_id': 'RAID Card1 Controller',
             'volume_name': 'os_volume', 'raid_level': 'RAID1',
             'drives': [3, 4], 'capacity_bytes': None,
             'span': 1, 'bootable': True}
        ]
    },
    {
        "name": "case-6",
        "logical_disks": [
            {
                "volume_name": "os_volume",
                "raid_level": "RAID1",
                "size_gb": 100
            },
            {
                "volume_name": "os_volume",
                "is_root_volume": True,
                "raid_level": "RAID1",
                "size_gb": "MAX"
            },
        ],
        "controllers": [{
            "id": test_storage.CTRL1_ID,
            "supported_raid_levels": test_storage.ALL_RAID_LEVELS,
            "drives": functools.reduce(
                operator.iconcat,
                [[test_storage.build_drive(0, capacity_gb=100)],
                 [test_storage.build_drive(1, capacity_gb=150)],
                 [test_storage.build_drive(idx, capacity_gb=200)
                  for idx in range(2, 16)]], []),
            "volumes": []
        }],
        "pending_volumes": [
            {'storage_id': 'RAID Card1 Controller',
             'volume_name': 'os_volume', 'raid_level': 'RAID1',
             'drives': [2, 3], 'capacity_bytes': test_storage.gb(100),
             'span': 1, 'bootable': False},
            {'storage_id': 'RAID Card1 Controller',
             'volume_name': 'os_volume', 'raid_level': 'RAID1',
             'drives': [4, 5], 'capacity_bytes': None,
             'span': 1, 'bootable': True}
        ]
    },
    ############################################################
    # Waste less strategy
    ############################################################
    {
        "name": "waste less disk total capacity",
        "logical_disks": [
            {
                "volume_name": "os_volume",
                "raid_level": "RAID5",
                "size_gb": 600
            },
            {
                "volume_name": "os_volume",
                "is_root_volume": True,
                "raid_level": "RAID5",
                "size_gb": "MAX"
            },
        ],
        "controllers": [{
            "id": test_storage.CTRL1_ID,
            "supported_raid_levels": test_storage.ALL_RAID_LEVELS,
            "drives": functools.reduce(
                operator.iconcat,
                [[test_storage.build_drive(idx, capacity_gb=100)
                  for idx in range(0, 7)],
                 [test_storage.build_drive(idx, capacity_gb=200)
                  for idx in range(8, 16)]], []),
            "volumes": []
        }],
        "pending_volumes": [
            {'storage_id': 'RAID Card1 Controller',
             'volume_name': 'os_volume', 'raid_level': 'RAID5',
             'drives': list(range(0, 7)),
             'capacity_bytes': test_storage.gb(600),
             'span': 1, 'bootable': False},
            {'storage_id': 'RAID Card1 Controller',
             'volume_name': 'os_volume', 'raid_level': 'RAID5',
             'drives': list(range(8, 16)), 'capacity_bytes': None,
             'span': 1, 'bootable': True}
        ]
    },
    {
        "name": "waste less capacity with different media type",
        "logical_disks": [
            {
                "volume_name": "os_volume",
                "raid_level": "RAID5",
                "size_gb": 600
            },
            {
                "volume_name": "os_volume",
                "is_root_volume": True,
                "raid_level": "RAID5",
                "size_gb": "MAX"
            },
        ],
        "controllers": [{
            "id": test_storage.CTRL1_ID,
            "supported_raid_levels": test_storage.ALL_RAID_LEVELS,
            "drives": functools.reduce(
                operator.iconcat,
                [
                    [test_storage.build_drive(
                        idx, capacity_gb=100, media_type='sdd')
                        for idx in range(0, 6)],
                    [test_storage.build_drive(idx, capacity_gb=100)
                     for idx in range(10, 17)],
                    [test_storage.build_drive(idx, capacity_gb=200)
                     for idx in range(18, 26)]
                ], []),
            "volumes": []
        }],
        "pending_volumes": [
            {'storage_id': 'RAID Card1 Controller',
             'volume_name': 'os_volume', 'raid_level': 'RAID5',
             'drives': list(range(10, 17)),
             'capacity_bytes': test_storage.gb(600),
             'span': 1, 'bootable': False},
            {'storage_id': 'RAID Card1 Controller',
             'volume_name': 'os_volume', 'raid_level': 'RAID5',
             'drives': list(range(18, 26)), 'capacity_bytes': None,
             'span': 1, 'bootable': True}
        ]
    },

    ############################################################
    #  Non-Share and specified disks
    ############################################################
    {
        "description": "non share and use specified disks",
        "name": "case-9",
        "logical_disks": [
            {
                "volume_name": "os_volume",
                "raid_level": "RAID5",
                "size_gb": 600
            },
            {
                "volume_name": "os_volume",
                "is_root_volume": True,
                "raid_level": "RAID5",
                "physical_disks": [
                    "Disk18",
                    "Disk19",
                    "Disk20"
                ],
                "size_gb": "MAX"
            },
        ],
        "controllers": [{
            "id": test_storage.CTRL1_ID,
            "supported_raid_levels": test_storage.ALL_RAID_LEVELS,
            "drives": functools.reduce(
                operator.iconcat,
                [
                    [test_storage.build_drive(
                        idx, capacity_gb=100, media_type='sdd')
                        for idx in range(0, 2)],
                    [test_storage.build_drive(idx, capacity_gb=100)
                     for idx in range(10, 17)],
                    [test_storage.build_drive(idx, capacity_gb=200)
                     for idx in range(18, 26)]
                ], []),
            "volumes": []
        }],
        "pending_volumes": [
            {'storage_id': 'RAID Card1 Controller',
             'volume_name': 'os_volume', 'raid_level': 'RAID5',
             'drives': list(range(18, 21)), 'capacity_bytes': None,
             'span': 1, 'bootable': True},
            {'storage_id': 'RAID Card1 Controller',
             'volume_name': 'os_volume', 'raid_level': 'RAID5',
             'drives': list(range(10, 17)),
             'capacity_bytes': test_storage.gb(600),
             'span': 1, 'bootable': False},
        ]
    },
    ############################################################
    # Share Disks and Specified Disks
    ############################################################
    {
        "name": "Share Disks and Specified Disks With Exists Volume matches",
        "logical_disks": [
            {
                "volume_name": "os_volume",
                "raid_level": "RAID5",
                "share_physical_disks": True,
                "size_gb": 400,
                "physical_disks": ["Disk8", "Disk9", "Disk10", "Disk11"]
            }
        ],
        "controllers": [{
            "id": test_storage.CTRL1_ID,
            "supported_raid_levels": test_storage.ALL_RAID_LEVELS,
            "drives": [test_storage.build_drive(idx, capacity_gb=200)
                       for idx in range(1, 16)],
            "volumes": [
                test_storage.build_volume(0, raid_utils.RAID5, 1, 200,
                                          [8, 9, 10, 11])
            ]
        }],
        "pending_volumes": [
            {'storage_id': 'RAID Card1 Controller',
             'volume_name': 'os_volume', 'raid_level': None,
             'drives': [8], 'capacity_bytes': test_storage.gb(400),
             'span': None, 'bootable': False},
        ]
    },
    {
        "name": "Share Disks and Specified Disks With Exists Volume matches",
        "logical_disks": [
            {
                "volume_name": "os_volume",
                "raid_level": "RAID5",
                "share_physical_disks": True,
                "size_gb": "MAX",
                "physical_disks": ["Disk8", "Disk9", "Disk10", "Disk11"]
            },
            {
                "volume_name": "os_volume",
                "raid_level": "RAID5",
                "share_physical_disks": True,
                "size_gb": 200,
                "physical_disks": ["Disk8", "Disk9", "Disk10", "Disk11"]
            }
        ],
        "controllers": [{
            "id": test_storage.CTRL1_ID,
            "supported_raid_levels": test_storage.ALL_RAID_LEVELS,
            "drives": [test_storage.build_drive(idx, capacity_gb=200)
                       for idx in range(1, 16)],
            "volumes": [
                test_storage.build_volume(0, raid_utils.RAID5, 1, 100,
                                          [8, 9, 10, 11])
            ]
        }],
        "pending_volumes": [
            {'storage_id': 'RAID Card1 Controller',
             'volume_name': 'os_volume', 'raid_level': None,
             'drives': [8], 'capacity_bytes': test_storage.gb(200),
             'span': None, 'bootable': False},
            {'storage_id': 'RAID Card1 Controller',
             'volume_name': 'os_volume', 'raid_level': None,
             'drives': [8], 'capacity_bytes': None,
             'span': None, 'bootable': False},
        ]
    },
    {
        "name": "Share Disks + Specified Disks But No exists volume matches",
        "logical_disks": [
            {
                "volume_name": "os_volume",
                "raid_level": "RAID5",
                "share_physical_disks": True,
                "size_gb": 400,
                "physical_disks": ["Disk8", "Disk9", "Disk10", "Disk11"]
            }
        ],
        "controllers": [{
            "id": test_storage.CTRL1_ID,
            "supported_raid_levels": test_storage.ALL_RAID_LEVELS,
            "drives": [test_storage.build_drive(idx, capacity_gb=200)
                       for idx in range(1, 16)],
            "volumes": [
                test_storage.build_volume(0, raid_utils.RAID5, 1, 200,
                                          range(0, 4))
            ]
        }],
        "pending_volumes": [
            {'storage_id': 'RAID Card1 Controller',
             'volume_name': 'os_volume', 'raid_level': raid_utils.RAID5,
             'drives': [8, 9, 10, 11], 'capacity_bytes': test_storage.gb(400),
             'span': 1, 'bootable': False},
        ]
    },
    {
        "name": "Share Disks + Specified Disks But Non exists volume matches",
        "logical_disks": [
            {
                "volume_name": "os_volume",
                "raid_level": "RAID5",
                "share_physical_disks": True,
                "size_gb": "MAX",
                "physical_disks": ["Disk8", "Disk9", "Disk10", "Disk11"]
            }
        ],
        "controllers": [{
            "id": test_storage.CTRL1_ID,
            "supported_raid_levels": test_storage.ALL_RAID_LEVELS,
            "drives": [test_storage.build_drive(idx, capacity_gb=200)
                       for idx in range(1, 16)],
            "volumes": [
                test_storage.build_volume(0, raid_utils.RAID5, 1, 200,
                                          range(0, 4))
            ]
        }],
        "pending_volumes": [
            {'storage_id': 'RAID Card1 Controller',
             'volume_name': 'os_volume', 'raid_level': raid_utils.RAID5,
             'drives': [8, 9, 10, 11], 'capacity_bytes': None,
             'span': 1, 'bootable': False},
        ]
    },
    {
        "name": "[M] Share Disks and Specified Disks But No Volume Matches",
        "logical_disks": [
            {
                "volume_name": "os_volume",
                "raid_level": "RAID5",
                "share_physical_disks": True,
                "size_gb": 400,
                "physical_disks": ["Disk8", "Disk9", "Disk10", "Disk11"]
            },
            {
                "volume_name": "os_volume",
                "raid_level": "RAID5",
                "share_physical_disks": True,
                "size_gb": 200,
                "physical_disks": ["Disk8", "Disk9", "Disk10", "Disk11"]
            }
        ],
        "controllers": [{
            "id": test_storage.CTRL1_ID,
            "supported_raid_levels": test_storage.ALL_RAID_LEVELS,
            "drives": [test_storage.build_drive(idx, capacity_gb=200)
                       for idx in range(1, 16)],
            "volumes": [
                test_storage.build_volume(0, raid_utils.RAID5, 1, 200,
                                          range(0, 4))
            ]
        }],
        "pending_volumes": [
            {'storage_id': 'RAID Card1 Controller',
             'volume_name': 'os_volume', 'raid_level': raid_utils.RAID5,
             'drives': [8, 9, 10, 11], 'capacity_bytes': test_storage.gb(400),
             'span': 1, 'bootable': False},
            {'storage_id': 'RAID Card1 Controller',
             'volume_name': 'os_volume', 'raid_level': None,
             'drives': [8], 'capacity_bytes': test_storage.gb(200),
             'span': None, 'bootable': False},
        ]
    },
    {
        "name": "[M] Share Disks and Specified Disks But No Volume Matches",
        "logical_disks": [
            {
                "volume_name": "os_volume",
                "raid_level": "RAID5",
                "share_physical_disks": True,
                "size_gb": "MAX",
                "physical_disks": ["Disk8", "Disk9", "Disk10", "Disk11"]
            },
            {
                "volume_name": "os_volume",
                "raid_level": "RAID5",
                "share_physical_disks": True,
                "size_gb": 200,
                "physical_disks": ["Disk8", "Disk9", "Disk10", "Disk11"]
            }
        ],
        "controllers": [{
            "id": test_storage.CTRL1_ID,
            "supported_raid_levels": test_storage.ALL_RAID_LEVELS,
            "drives": [test_storage.build_drive(idx, capacity_gb=200)
                       for idx in range(1, 16)],
            "volumes": [
                test_storage.build_volume(0, raid_utils.RAID5, 1, 200,
                                          range(0, 4))
            ]
        }],
        "pending_volumes": [
            {'storage_id': 'RAID Card1 Controller',
             'volume_name': 'os_volume', 'raid_level': raid_utils.RAID5,
             'drives': [8, 9, 10, 11], 'capacity_bytes': test_storage.gb(200),
             'span': 1, 'bootable': False},
            {'storage_id': 'RAID Card1 Controller',
             'volume_name': 'os_volume', 'raid_level': None,
             'drives': [8], 'capacity_bytes': None,
             'span': None, 'bootable': False},
        ]
    },
    ############################################################
    # Share Disks and Auto Choose Disks
    ############################################################
    {
        "name": "Share Disks and Auto Choose Disks",
        "logical_disks": [
            {
                "volume_name": "os_volume",
                "raid_level": "RAID5",
                "share_physical_disks": True,
                "size_gb": 400,
            }
        ],
        "controllers": [{
            "id": test_storage.CTRL1_ID,
            "supported_raid_levels": test_storage.ALL_RAID_LEVELS,
            "drives": [test_storage.build_drive(idx, capacity_gb=200)
                       for idx in range(0, 24)],
            "volumes": [
                test_storage.build_volume(0, raid_utils.RAID5, 1, 200,
                                          range(4, 7)),
                test_storage.build_volume(0, raid_utils.RAID5, 1, 200,
                                          range(7, 13)),
                test_storage.build_volume(0, raid_utils.RAID5, 1, 200,
                                          range(0, 4)),
                test_storage.build_volume(0, raid_utils.RAID5, 1, 200,
                                          range(13, 18)),
                test_storage.build_volume(0, raid_utils.RAID5, 1, 200,
                                          range(18, 22))
            ]
        }],
        "pending_volumes": [
            {'storage_id': 'RAID Card1 Controller',
             'volume_name': 'os_volume', 'raid_level': None,
             'drives': [0], 'capacity_bytes': test_storage.gb(400),
             'span': None, 'bootable': False},
        ]
    },
    {
        "name": "Share Disks and Auto Choose Disks For 'MAX' size",
        "logical_disks": [
            {
                "volume_name": "os_volume",
                "raid_level": "RAID5",
                "share_physical_disks": True,
                "size_gb": "MAX",
            }
        ],
        "controllers": [{
            "id": test_storage.CTRL1_ID,
            "supported_raid_levels": test_storage.ALL_RAID_LEVELS,
            "drives": [test_storage.build_drive(idx, capacity_gb=200)
                       for idx in range(0, 24)],
            "volumes": [
                test_storage.build_volume(0, raid_utils.RAID5, 1, 200,
                                          range(4, 7)),
                test_storage.build_volume(0, raid_utils.RAID5, 1, 200,
                                          range(7, 13)),
                test_storage.build_volume(0, raid_utils.RAID5, 1, 200,
                                          range(0, 4)),
                test_storage.build_volume(0, raid_utils.RAID5, 1, 200,
                                          range(13, 18)),
                test_storage.build_volume(0, raid_utils.RAID5, 1, 200,
                                          range(18, 22))
            ]
        }],
        "pending_volumes": [
            {'storage_id': 'RAID Card1 Controller',
             'volume_name': 'os_volume', 'raid_level': None,
             'drives': [7], 'capacity_bytes': None,
             'span': None, 'bootable': False},
        ]
    },
    {
        "name": "Share Disks and Auto Choose Disks with un-matched raid level",
        "logical_disks": [
            {
                "volume_name": "os_volume",
                "raid_level": "RAID5",
                "share_physical_disks": True,
                "size_gb": "MAX",
            }
        ],
        "controllers": [{
            "id": test_storage.CTRL1_ID,
            "supported_raid_levels": test_storage.ALL_RAID_LEVELS,
            "drives": [test_storage.build_drive(idx, capacity_gb=200)
                       for idx in range(0, 24)],
            "volumes": [
                test_storage.build_volume(0, raid_utils.RAID5, 1, 200,
                                          range(4, 7)),
                test_storage.build_volume(0, raid_utils.RAID6, 1, 200,
                                          range(7, 13)),
                test_storage.build_volume(0, raid_utils.RAID5, 1, 200,
                                          range(0, 4)),
                test_storage.build_volume(0, raid_utils.RAID5, 1, 200,
                                          range(13, 18)),
                test_storage.build_volume(0, raid_utils.RAID5, 1, 200,
                                          range(18, 22))
            ]
        }],
        "pending_volumes": [
            {'storage_id': 'RAID Card1 Controller',
             'volume_name': 'os_volume', 'raid_level': None,
             'drives': [13], 'capacity_bytes': None,
             'span': None, 'bootable': False},
        ]
    },
    {
        "name": "[Multiple] Share Disks and Auto Choose Disks",
        "logical_disks": [
            {
                "volume_name": "os_volume",
                "raid_level": "RAID5",
                "share_physical_disks": True,
                "size_gb": 400,
            },
            {
                "volume_name": "os_volume",
                "raid_level": "RAID5",
                "share_physical_disks": True,
                "size_gb": 100,
            },
            {
                "volume_name": "os_volume",
                "raid_level": "RAID5",
                "share_physical_disks": True,
                "size_gb": 100,
            },
            {
                "volume_name": "os_volume",
                "raid_level": "RAID5",
                "share_physical_disks": True,
                "size_gb": 500,
            },
            {
                "volume_name": "os_volume",
                "raid_level": "RAID5",
                "share_physical_disks": True,
                "size_gb": 300,
            }
        ],
        "controllers": [{
            "id": test_storage.CTRL1_ID,
            "supported_raid_levels": test_storage.ALL_RAID_LEVELS,
            "drives": [test_storage.build_drive(idx, capacity_gb=200)
                       for idx in range(0, 24)],
            "volumes": [
                test_storage.build_volume(0, raid_utils.RAID5, 1, 200,
                                          range(4, 7)),
                test_storage.build_volume(0, raid_utils.RAID6, 1, 200,
                                          range(7, 13)),
                test_storage.build_volume(0, raid_utils.RAID5, 1, 200,
                                          range(0, 4)),
                test_storage.build_volume(0, raid_utils.RAID5, 1, 200,
                                          range(13, 18)),
                test_storage.build_volume(0, raid_utils.RAID5, 1, 200,
                                          range(18, 22))
            ]
        }],
        "pending_volumes": [
            {'storage_id': 'RAID Card1 Controller',
             'volume_name': 'os_volume', 'raid_level': None,
             'drives': [0], 'capacity_bytes': test_storage.gb(400),
             'span': None, 'bootable': False},
            {'storage_id': 'RAID Card1 Controller',
             'volume_name': 'os_volume', 'raid_level': None,
             'drives': [4], 'capacity_bytes': test_storage.gb(100),
             'span': None, 'bootable': False},
            {'storage_id': 'RAID Card1 Controller',
             'volume_name': 'os_volume', 'raid_level': None,
             'drives': [4], 'capacity_bytes': test_storage.gb(100),
             'span': None, 'bootable': False},
            {'storage_id': 'RAID Card1 Controller',
             'volume_name': 'os_volume', 'raid_level': None,
             'drives': [13], 'capacity_bytes': test_storage.gb(500),
             'span': None, 'bootable': False},
            {'storage_id': 'RAID Card1 Controller',
             'volume_name': 'os_volume', 'raid_level': None,
             'drives': [18], 'capacity_bytes': test_storage.gb(300),
             'span': None, 'bootable': False},
        ]
    },
    {
        "name": "Share Disks and Auto Choose Disks When no disk group matches",
        "logical_disks": [
            {
                "volume_name": "os_volume",
                "raid_level": "RAID5",
                "share_physical_disks": True,
                "size_gb": 500,
            }
        ],
        "controllers": [{
            "id": test_storage.CTRL1_ID,
            "supported_raid_levels": test_storage.ALL_RAID_LEVELS,
            "drives": [test_storage.build_drive(idx, capacity_gb=200)
                       for idx in range(0, 24)],
            "volumes": [
                test_storage.build_volume(0, raid_utils.RAID5, 1, 200,
                                          range(0, 4)),
                test_storage.build_volume(0, raid_utils.RAID5, 1, 400,
                                          range(13, 18)),
            ]
        }],
        "pending_volumes": [
            {'storage_id': 'RAID Card1 Controller',
             'volume_name': 'os_volume', 'raid_level': raid_utils.RAID5,
             'drives': [4, 5, 6, 7], 'capacity_bytes': test_storage.gb(500),
             'span': 1, 'bootable': False},
        ]
    },
    {
        "name": "Share Disks and Auto Choose Disks When no disk group matches",
        "logical_disks": [
            {
                "volume_name": "os_volume",
                "raid_level": "RAID5",
                "share_physical_disks": True,
                "size_gb": 'max',
            }
        ],
        "controllers": [{
            "id": test_storage.CTRL1_ID,
            "supported_raid_levels": test_storage.ALL_RAID_LEVELS,
            "drives": [test_storage.build_drive(idx, capacity_gb=200)
                       for idx in range(0, 24)],
            "volumes": [
                test_storage.build_volume(0, raid_utils.RAID5, 1, 300,
                                          range(0, 4)),
                test_storage.build_volume(0, raid_utils.RAID5, 1, 400,
                                          range(13, 18)),
            ]
        }],
        "pending_volumes": [
            {'storage_id': 'RAID Card1 Controller',
             'volume_name': 'os_volume', 'raid_level': None,
             'drives': [13], 'capacity_bytes': None,
             'span': None, 'bootable': False},
        ]
    },
    {
        "name": "Share Disks and Auto Choose Disks When no disk group matches",
        "logical_disks": [
            {
                "volume_name": "os_volume",
                "raid_level": "RAID50",
                "share_physical_disks": True,
                "size_gb": 'max',
            }
        ],
        "controllers": [{
            "id": test_storage.CTRL1_ID,
            "supported_raid_levels": test_storage.ALL_RAID_LEVELS,
            "drives": [test_storage.build_drive(idx, capacity_gb=200)
                       for idx in range(0, 24)],
            "volumes": [
                test_storage.build_volume(0, raid_utils.RAID5, 1, 300,
                                          range(0, 4)),
                test_storage.build_volume(0, raid_utils.RAID5, 1, 400,
                                          range(4, 10)),
            ]
        }],
        "pending_volumes": [
            {'storage_id': 'RAID Card1 Controller',
             'volume_name': 'os_volume', 'raid_level': raid_utils.RAID50,
             'drives': list(range(10, 24)), 'capacity_bytes': None,
             'span': 2, 'bootable': False},
        ]
    },
    ############################################################
    # Guess span number
    ############################################################
    {
        "name": "Test Guess span number For 3 using RAID50",
        "logical_disks": [
            {
                "volume_name": "os_volume",
                "raid_level": "RAID50",
                "share_physical_disks": True,
                "size_gb": 'max',
                "number_of_physical_disks": 9
            }
        ],
        "controllers": [{
            "id": test_storage.CTRL1_ID,
            "supported_raid_levels": test_storage.ALL_RAID_LEVELS,
            "drives": [test_storage.build_drive(idx, capacity_gb=200)
                       for idx in range(0, 9)],
            "volumes": []
        }],
        "pending_volumes": [
            {'storage_id': 'RAID Card1 Controller',
             'volume_name': 'os_volume', 'raid_level': raid_utils.RAID50,
             'drives': list(range(0, 9)), 'capacity_bytes': None,
             'span': 3, 'bootable': False},
        ]
    },
    {
        "name": "Test Guess span number For 4 using RAID10",
        "logical_disks": [
            {
                "volume_name": "os_volume",
                "raid_level": "RAID10",
                "share_physical_disks": True,
                "size_gb": 'max'
            }
        ],
        "controllers": [{
            "id": test_storage.CTRL1_ID,
            "supported_raid_levels": test_storage.ALL_RAID_LEVELS,
            "drives": [test_storage.build_drive(idx, capacity_gb=200)
                       for idx in range(0, 9)],
            "volumes": []
        }],
        "pending_volumes": [
            {'storage_id': 'RAID Card1 Controller',
             'volume_name': 'os_volume', 'raid_level': raid_utils.RAID10,
             'drives': list(range(0, 8)), 'capacity_bytes': None,
             'span': 4, 'bootable': False},
        ]
    },
    {
        "name": "Test Guess span number For 5 using RAID10",
        "logical_disks": [
            {
                "volume_name": "os_volume",
                "raid_level": "RAID10",
                "share_physical_disks": True,
                "size_gb": 'max'
            }
        ],
        "controllers": [{
            "id": test_storage.CTRL1_ID,
            "supported_raid_levels": test_storage.ALL_RAID_LEVELS,
            "drives": [test_storage.build_drive(idx, capacity_gb=200)
                       for idx in range(0, 11)],
            "volumes": []
        }],
        "pending_volumes": [
            {'storage_id': 'RAID Card1 Controller',
             'volume_name': 'os_volume', 'raid_level': raid_utils.RAID10,
             'drives': list(range(0, 10)), 'capacity_bytes': None,
             'span': 5, 'bootable': False},
        ]
    },
    {
        "name": "Test Guess span number For 5 using RAID10",
        "logical_disks": [
            {
                "volume_name": "os_volume",
                "raid_level": "RAID50",
                "share_physical_disks": True,
                "size_gb": 'MAX',
                "number_of_physical_disks": 25
            }
        ],
        "controllers": [{
            "id": test_storage.CTRL1_ID,
            "supported_raid_levels": test_storage.ALL_RAID_LEVELS,
            "drives": [test_storage.build_drive(idx, capacity_gb=200)
                       for idx in range(0, 25)],
            "volumes": []
        }],
        "pending_volumes": [
            {'storage_id': 'RAID Card1 Controller',
             'volume_name': 'os_volume', 'raid_level': raid_utils.RAID50,
             'drives': list(range(0, 25)), 'capacity_bytes': None,
             'span': 5, 'bootable': False},
        ]
    },
    {
        "name": "Test share disks",
        "logical_disks": [
            {
                "raid_level": "RAID5",
                "size_gb": 500,
                "share_physical_disks": True
            },
            {
                "raid_level": "RAID5",
                "size_gb": 500,
                "share_physical_disks": True
            },
            {
                "raid_level": "RAID5",
                "size_gb": 500,
                "share_physical_disks": True
            },
        ],
        "controllers": [{
            "id": test_storage.CTRL1_ID,
            "supported_raid_levels": test_storage.ALL_RAID_LEVELS,
            "drives": [test_storage.build_drive(idx, capacity_gb=1000)
                       for idx in range(0, 25)],
            "volumes": []
        }],
        "pending_volumes": [
            {'storage_id': 'RAID Card1 Controller',
             'volume_name': None, 'raid_level': raid_utils.RAID5,
             'drives': list(range(0, 3)),
             'capacity_bytes': test_storage.gb(500),
             'span': 1, 'bootable': False},
            {'storage_id': 'RAID Card1 Controller',
             'volume_name': None, 'raid_level': None,
             'drives': [0],
             'capacity_bytes': test_storage.gb(500),
             'span': None, 'bootable': False},
            {'storage_id': 'RAID Card1 Controller',
             'volume_name': None, 'raid_level': None,
             'drives': [0],
             'capacity_bytes': test_storage.gb(500),
             'span': None, 'bootable': False},
        ]
    }
]
