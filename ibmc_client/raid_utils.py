# Copyright 2020 HUAWEI, Inc. All Rights Reserved.
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

# Version 0.0.3

import collections
import logging
import math

from ibmc_client import exceptions
from ibmc_client.resources.chassis import drive as DRIVE
from ibmc_client.resources.system import storage

LOG = logging.getLogger(__name__)

# RAID Levels
JBOD = 'JBOD'
"""No RAID, JBOD mode"""

RAID0 = 'RAID0'
"""RAID Level 0, at least 1 drives is required."""

RAID1 = 'RAID1'
"""RAID Level 1, at least 2 drives is required."""

RAID5 = 'RAID5'
"""RAID Level 5, at least 3 drives is required. (N-1)"""

RAID6 = 'RAID6'
"""RAID Level 6, at least 3 drives is required. (N-2)"""

RAID10 = 'RAID10'
"""RAID Level 10, alias to RAID 0+1, at least 4 drives is required."""

RAID50 = 'RAID50'
"""RAID Level 50"""

RAID60 = 'RAID60'
"""RAID Level 60"""

# RAID types
RAID_TYPE_SPANNED = 'Spanned'
"""RAID type spanned"""

RAID_TYPE_NON_REDUNDANT = 'NonRedundant'
"""RAID type NonRedundant"""

RAID_TYPE_MIRRORED = 'Mirrored'
"""RAID type Mirrored"""

RAID_TYPE_STRIPED_WITH_PARITY = 'StripedWithParity'
"""RAID type Mirrored"""

RAID_TYPE_RAW_DEVICE = 'RawDevice'
"""RAID type RawDevice"""


class PhysicalDisk(object):
    """A model represents a real physical-disk(known as drive in iBMC)
    hardware
    """
    drive = None
    drive_id = None
    protocol = None
    media_type = None
    capacity_bytes = None
    firmware_state = None
    used_by_volumes = None

    exclusive = None
    """indicates whether a physical disk is exclusive"""

    # pending_capacity_bytes = None
    # """indicates the pending bytes of uncommitted volumes"""

    def __init__(self, drive):
        # type: (DRIVE.Drive) -> None
        self.drive = drive
        self.drive_id = drive.drive_id
        self.protocol = drive.protocol
        self.media_type = drive.media_type
        self.capacity_bytes = drive.capacity_bytes
        self.firmware_state = drive.firmware_state
        self.used_by_volumes = drive.volume_odata_id_collection

        self.exclusive = False

    @property
    def is_excludable(self):
        """whether this disk is excludable.
        - not exclusive by any other unshareable pending volume
        - firmware state is unconfig good
        - not used by other shareable pending volume

        :return: true if yes else false
        """
        return not self.exclusive and self.drive.is_unconfig_good()

    def mark_as_exclusive(self):
        self.exclusive = True

    def __repr__(self):
        return str(self)

    def __str__(self):
        return "Disk%d(%s)" % (self.drive_id, self.media_type)


class PhysicalDiskGroup(object):
    """A model represents a real physical-disk group. upon a physical-disk
    group, logical disks is created.
    """
    drives = None
    """sorted drive(:class:`~ibmc_client.resources.chassis.drive.Drive`)
    object list that this disk group uses
    """
    raid_setting = None  # type: Raid
    span_number = None
    overhead = None
    capacity_bytes = None
    used_capacity_bytes_list = None
    pending_capacity_bytes_list = None

    def __init__(self, drives, raid_setting, span_number):
        # type: (list[DRIVE.Drive], Raid, int) -> None
        self.drives = sorted(drives, key=lambda drive: drive.capacity_bytes)
        self.raid_setting = raid_setting
        self.span_number = span_number
        self.overhead = raid_setting.get_overhead_per_span() * span_number
        self.capacity_bytes = (self.drives[0].capacity_bytes
                               * (len(self.drives) - self.overhead))
        self.pending_capacity_bytes_list = []
        self.used_capacity_bytes_list = []

    @staticmethod
    def from_volume(volume, all_drives):
        # type: (storage.Volume, list[DRIVE.Drive]) -> PhysicalDiskGroup

        raid_setting = RAID_SETTINGS.get(volume.raid_level)
        drives = sorted(
            [drive for drive in all_drives
             if drive.odata_id in volume.drive_odata_id_collection],
            key=lambda drive: drive.capacity_bytes)
        span_number = volume.span_number
        disk_group = PhysicalDiskGroup(drives, raid_setting, span_number)
        disk_group.add_used_capacity_bytes(volume.capacity_bytes)
        return disk_group

    @property
    def used_capacity_bytes(self):
        return sum(self.used_capacity_bytes_list)

    @property
    def pending_capacity_bytes(self):
        return sum(self.pending_capacity_bytes_list)

    @property
    def left_capacity_bytes(self):
        return (self.capacity_bytes - self.used_capacity_bytes
                - self.pending_capacity_bytes)

    def has_capacity_for(self, target_capacity):
        """check whether this disk group has enough left capacity for target
        capacity.

        :param target_capacity: -1 for 'max'; int for bytes;
        :return: true if yes else false
        """
        if target_capacity == -1:
            return self.left_capacity_bytes > 0
        return self.left_capacity_bytes >= target_capacity

    def add_pending_capacity_bytes(self, target_capacity):
        if self.has_capacity_for(target_capacity):
            if target_capacity == -1:
                self.pending_capacity_bytes_list.append(
                    self.left_capacity_bytes)
            else:
                self.pending_capacity_bytes_list.append(target_capacity)

    def owns_volume(self, volume):
        # type: (storage.Volume) -> bool
        """check whether current disk group owns a volume

        base on whether any disk of the volume belongs to disk group too.
        :param volume:
        :return: true if owns else false
        """
        return any([drive.odata_id == volume.drive_odata_id_collection[0]
                    for drive in self.drives])

    def validate_if_suitable_for(self, target_capacity, raid):
        # type: (int, Raid) -> None
        """validate whether current physical disk group is suitable for
        target capacity with raid setting.

        :param target_capacity: indicates the required capacity
        :param raid: indicates the target raid setting
        :raises exceptions.NotSuitablePhysicalDiskGroup when a disk group does
            not have enough capacity or it has a different raid-level than
            required.
        """
        # validate whether disk group has enough shareable capacity
        matches = self.has_capacity_for(target_capacity)
        if not matches:
            raise exceptions.NotSuitablePhysicalDiskGroup(
                message='Those physical disks does not have enough capacity.')
        # validate whether disk group has same raid level
        if self.raid_setting.name != raid.name:
            message = ('Those shareable physical disks has raid-level %s, '
                       'could not be used for required raid-level %s.' %
                       (self.raid_setting.key, raid.key))
            raise exceptions.NotSuitablePhysicalDiskGroup(message=message)

    def add_used_capacity_bytes(self, used_capacity_bytes):
        self.used_capacity_bytes_list.append(used_capacity_bytes)

    @property
    def drive_id_list(self):
        return [drive.id for drive in self.drives]

    def is_better_than(self, target_capacity, other):
        # type: (int, PhysicalDiskGroup) -> bool
        """compare to other PhysicalDiskGroup to check whether is a better
        choice.

        :param target_capacity:
        :param other: indicates the other physical disk group to compare
        :return: true if current physical disk group is a better choice else
            false
        """
        if target_capacity > 0:
            return self.waste_less_than(other)

        if target_capacity == -1:
            return self.left_great_than(other)

    def waste_less_than(self, other):
        """waste as less disk capacity as better

        :param other:
        :return:
        """
        if other is None:
            return True

        if self.left_capacity_bytes < other.left_capacity_bytes:
            return True
        if self.left_capacity_bytes > other.left_capacity_bytes:
            return False

        return False

    def left_great_than(self, other):
        """as much left capacity bytes as better

        :param other:
        :return:
        """
        if other is None:
            return True

        if self.left_capacity_bytes > other.left_capacity_bytes:
            return True
        if self.left_capacity_bytes < other.left_capacity_bytes:
            return False

        return False  # pragma: no cover

    def log(self, find):
        fmt_kwargs = {'disk_group': str(self),
                      'left': self.left_capacity_bytes}
        if find:
            LOG.info('Find a better choice:: disk-group->%(disk_group)s, '
                     'left-capacity-bytes: %(left)d', fmt_kwargs)
        else:
            LOG.info('Not a better choice:: disk-group->%(disk_group)s, '
                     'left-capacity-bytes: %(left)d', fmt_kwargs)

    def __repr__(self):  # pragma: no cover
        return str(self)

    def __str__(self):
        return "PhysicalDiskGroup(%s-%s)" % (self.raid_setting.name,
                                             ','.join(self.drive_id_list))


class RaidSolution(object):
    """RAID solution summary

    """
    span = None
    disks = []  # type: list[PhysicalDisk]
    disks_count = None
    disks_total_bytes = None
    disks_waste_bytes = None
    disks_min_bytes = None
    raid_total_bytes = None

    def __init__(self, span, disks, overhead):
        # type: (int, list[PhysicalDisk], int) -> None
        self.span = span
        self.disks = sorted(disks, key=lambda d: d.capacity_bytes)
        self.disks_total_bytes = sum((_.capacity_bytes for _ in disks))
        self.disks_min_bytes = (disks[0].capacity_bytes
                                if len(disks) else 0)
        self.disks_count = len(disks)
        effect_disk_count = self.disks_count - overhead
        self.raid_total_bytes = self.disks_min_bytes * effect_disk_count
        self.disks_waste_bytes = (self.disks_total_bytes
                                  - self.disks_min_bytes * self.disks_count)

    def is_better_than(self, target_capacity, other):
        """compare to other solution

        :param target_capacity:
        :param other: indicates the other solution to compare
        :return: true if current solution is better choice else false
        """
        if target_capacity > 0:
            return self.waste_less_than(other)

        if target_capacity == -1:
            return self.raid_capacity_great_than(other)

    def waste_less_than(self, other):
        """waste as less disk capacity as better

        if waste space is same then use as small disk capacity as better.

        :param other:
        :return:
        """
        if other is None:
            return True

        if self.disks_waste_bytes < other.disks_waste_bytes:
            return True
        if self.disks_waste_bytes > other.disks_waste_bytes:
            return False

        if self.disks_total_bytes < other.disks_total_bytes:
            return True
        if self.disks_total_bytes > other.disks_total_bytes:
            return False

        if self.disks_count < other.disks_count:  # pragma: no cover
            return True
        if self.disks_count > other.disks_count:  # pragma: no cover
            return False

        return False

    def raid_capacity_great_than(self, other):
        """as much RAID volume capacity as better

        if capacity is same, then waste as less as better.

        :param other:
        :return:
        """
        if other is None:
            return True

        if self.raid_total_bytes > other.raid_total_bytes:
            return True
        if self.raid_total_bytes < other.raid_total_bytes:
            return False

        return self.waste_less_than(other)

    def log(self, find):
        fmt_kwargs = {'span': self.span, 'waste': self.disks_waste_bytes,
                      'used': self.disks_total_bytes, 'disks': self.disks,
                      'effect': self.raid_total_bytes}
        if find:
            LOG.info('Find a better choice:: span->%(span)d, '
                     'total-waste-bytes->%(waste)d, '
                     'used-disks-total-bytes->%(used)d, '
                     'raid-volume-bytes->%(effect)d, '
                     'disks->%(disks)s', fmt_kwargs)
        else:
            LOG.info('Not a better choice:: span->%(span)d, '
                     'total-waste-bytes->%(waste)d, '
                     'used-disks-total-bytes->%(used)d, '
                     'raid-volume-bytes->%(effect)d, '
                     'disks->%(disks)s', fmt_kwargs)


class Raid(object):
    key = None
    name = None
    min_disks = None
    max_disks = None
    overhead = None
    raid_type = None
    level = None

    # when raid-type is spanned
    raid_level = None
    span = None

    def __init__(self, key, name, raid_type, level, min_disks=None,
                 max_disks=None, overhead=None, raid_level=None, span=None):
        self.key = key
        self.name = name
        self.min_disks = min_disks
        self.max_disks = max_disks
        self.overhead = overhead
        self.raid_type = raid_type
        self.level = level

        # when raid-type is spanned
        self.raid_level = raid_level
        self.span = span

    def get_min_disks(self):
        """get min required disks for all possible situations

        :return: min required disks
        """
        if not self.is_spanned:
            return self.min_disks
        else:
            sub_raid_setting = RAID_SETTINGS.get(self.raid_level)
            return sub_raid_setting.min_disks * 2

    def get_overhead_per_span(self):
        """get overhead for every span

        :return:
        """
        if not self.is_spanned:
            return self.overhead
        else:
            sub_raid_setting = RAID_SETTINGS.get(self.raid_level)
            return sub_raid_setting.overhead

    @property
    def is_spanned(self):
        return self.raid_type == RAID_TYPE_SPANNED

    def get_best_matched_disk_group(self, target_capacity,
                                    physical_disk_groups):
        # type: (int, list[PhysicalDiskGroup]) -> PhysicalDiskGroup
        """get best matched physical disk group using waste least capacity
        strategy.

        :param target_capacity: indicates target required capacity
        :param physical_disk_groups: indicates available physical disk group
            list
        :return:
        """

        LOG.info('Try to get best matched disk-group for '
                 'volume(%(raid_level)s) with target capacity %(capacity)d '
                 'using waste least strategy',
                 {'raid_level': self.name, 'capacity': target_capacity})

        best_choice = None
        for disk_group in physical_disk_groups:
            try:
                disk_group.validate_if_suitable_for(target_capacity, self)
            except exceptions.NotSuitablePhysicalDiskGroup as e:
                LOG.info("%(disk_group)s is not a choice:: %(reason)s",
                         {'disk_group': str(disk_group), 'reason': str(e)})
                pass
            else:
                better = disk_group.is_better_than(target_capacity,
                                                   best_choice)
                disk_group.log(better)
                if better:
                    best_choice = disk_group

        return best_choice

    def get_best_matched_disks(self, target_capacity, available_disks,
                               disk_count_to_use):
        # type: (int, list[PhysicalDisk], int) -> RaidSolution
        """get best matched disks for target capacity size with current raid.

        :param target_capacity: target capacity
        :param available_disks: a list available physical disk
        :param disk_count_to_use: disk count to use if not None
            else auto choose
        :return:
        """

        if self.name == JBOD:  # pragma: no cover
            return None

        LOG.info('Calculate waste least disks for volume(%(raid_level)s) with'
                 ' target capacity %(capacity)d, available disks: %(disks)s.',
                 {'raid_level': self.name, 'capacity': target_capacity,
                  'disks': available_disks})

        raid = RAID_SETTINGS.get(self.raid_level) if self.is_spanned else self
        available_span_list = [1] if not self.is_spanned else list(range(2, 9))

        grouped_by_media_type = collections.defaultdict(list)
        for disk in available_disks:
            grouped_by_media_type[disk.media_type].append(disk)
        LOG.info('Group available disks by media type: %(disks)s',
                 {'disks': str(grouped_by_media_type)})

        is_specified_disk_count_legal = disk_count_to_use is None
        best_solution = None
        for (media_type, disks_by_media_type) in grouped_by_media_type.items():
            LOG.info('Try to calculate for media type `%(media_type)s` now.',
                     {'media_type': media_type})
            for span in available_span_list:
                if disk_count_to_use:
                    if disk_count_to_use % span != 0:
                        LOG.info(
                            'Specified disk count number `%(disk_count)d` does'
                            ' not match span number %(span)d, continue.',
                            {'span': span, 'disk_count': disk_count_to_use})
                        continue

                    disk_count_to_use_per_span = disk_count_to_use / span
                    if (disk_count_to_use_per_span < raid.min_disks or
                            disk_count_to_use_per_span > raid.max_disks):
                        LOG.info(
                            'Specified disk count number `%(disk_count)d` '
                            'does not match raid-level %(raid)s with '
                            'span %(span)d, continue.',
                            {'span': span, 'disk_count': disk_count_to_use,
                             'raid': self.key})
                        continue

                    is_specified_disk_count_legal = True

                min_disks = (disk_count_to_use if disk_count_to_use else
                             raid.min_disks * span)
                max_disks = (disk_count_to_use if disk_count_to_use else
                             raid.max_disks * span)
                overhead = raid.overhead * span

                if min_disks > len(disks_by_media_type):
                    LOG.info('Disk count(%(disk_count)d) is less than '
                             'min-disks(%(min_disks)d), break current branch.',
                             {'disk_count': len(disks_by_media_type),
                              'min_disks': min_disks})
                    break

                max_disk_count = min(max_disks, len(disks_by_media_type))
                for required_disk_count in range(
                        min_disks, max_disk_count + 1, span):

                    LOG.info('Calculate for span:: %(span)d, disk-count:: %('
                             'disk_count)d.',
                             {'span': span, 'disk_count': required_disk_count})

                    if required_disk_count % span != 0:  # pragma: no cover
                        LOG.info(
                            'Disk count %(disk_count)d does not match span '
                            'number %(span)d, continue.',
                            {'span': span, 'disk_count': required_disk_count})
                        continue

                    required_capacity = math.ceil(
                        target_capacity / (required_disk_count - overhead))
                    matched_disks = [_ for _ in disks_by_media_type
                                     if _.capacity_bytes >= required_capacity]
                    if len(matched_disks) < required_disk_count:
                        LOG.info('Not enough disks has required capacity '
                                 '%(required_capacity)d, required %('
                                 'disk_count)d actual %(actual)d.',
                                 {'required_capacity': required_capacity,
                                  'disk_count': required_disk_count,
                                  'actual': len(matched_disks)})
                        continue

                    # sort matched disks
                    sorted_matched_disks = sorted(
                        matched_disks, key=lambda d: d.capacity_bytes)
                    cases = len(matched_disks) - required_disk_count + 1
                    for start in range(0, cases):
                        end = start + required_disk_count
                        possible_disks = sorted_matched_disks[start:end]
                        solution = RaidSolution(span, possible_disks, overhead)
                        better = solution.is_better_than(target_capacity,
                                                         best_solution)
                        solution.log(better)
                        if better:
                            best_solution = solution

                    """
                    In waste less scene::
                      if all disk capacity is gt than min-required capacity.
                      it means all disks will always in possible disks later.
                      then the greater disk-count-per-span is, waste the more.
                    """
                    if (len(matched_disks) == len(disks_by_media_type)
                            and target_capacity > 0):
                        break

        if not is_specified_disk_count_legal:
            raise exceptions.InvalidPhysicalDiskNumber(
                number_of_physical_disks=disk_count_to_use, raid=self.key)

        return best_solution


RAID_SETTINGS = {
    'JBOD': Raid(**{
        'key': 'JBOD',
        'name': JBOD,
        'min_disks': 1,
        'max_disks': 1024,
        'raid_type': RAID_TYPE_RAW_DEVICE,
        'overhead': 0,
        'level': -1
    }),
    '0': Raid(**{
        'key': '0',
        'name': RAID0,
        'min_disks': 1,
        'max_disks': 1024,
        'raid_type': RAID_TYPE_NON_REDUNDANT,
        'overhead': 0,
        'level': 0
    }),
    '1': Raid(**{
        'key': '1',
        'name': RAID1,
        'min_disks': 2,
        'max_disks': 2,
        'raid_type': RAID_TYPE_MIRRORED,
        'overhead': 1,
        'level': 1
    }),
    '5': Raid(**{
        'key': '5',
        'name': RAID5,
        'min_disks': 3,
        'max_disks': 1024,
        'raid_type': RAID_TYPE_STRIPED_WITH_PARITY,
        'overhead': 1,
        'level': 5
    }),
    '6': Raid(**{
        'key': '6',
        'name': RAID6,
        'min_disks': 3,
        'max_disks': 1024,
        'raid_type': RAID_TYPE_STRIPED_WITH_PARITY,
        'overhead': 2,
        'level': 6
    }),
    '1+0': Raid(**{
        'key': '1+0',
        'name': RAID10,
        'raid_type': RAID_TYPE_SPANNED,
        'raid_level': '1',
        'span': lambda disk_count: disk_count >> 1,
        'level': 10
    }),
    '5+0': Raid(**{
        'key': '5+0',
        'name': RAID50,
        'raid_type': RAID_TYPE_SPANNED,
        'raid_level': '5',
        'span': 2,
        'level': 50
    }),
    '6+0': Raid(**{
        'key': '6+0',
        'name': RAID60,
        'raid_type': RAID_TYPE_SPANNED,
        'raid_level': '6',
        'span': 2,
        'level': 60
    })
}

# add local raid name mapping
for k in list(RAID_SETTINGS):
    RAID_SETTINGS[RAID_SETTINGS[k].name] = RAID_SETTINGS[k]
"""RAID settings"""
