# Copyright 2019 HUAWEI, Inc. All Rights Reserved.
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
import logging
import time
from collections import defaultdict
from functools import cmp_to_key
from itertools import groupby

import six

from ibmc_client import raid_utils, exceptions, constants
from ibmc_client.api import BaseApiClient
from ibmc_client.resources.system.storage import Storage

LOG = logging.getLogger(__name__)


class LogicalDisk(object):
    MAX_CAPACITY = -1

    controller = None
    """controller model"""
    volume_name = None
    raid_level = None
    drives = None
    capacity_bytes = None
    span_number = None
    bootable = False

    share_physical_disks = False
    number_of_physical_disks = 0
    use_shareable_disk_group = False

    def __init__(self, logical_disk):
        self._logical_disk = logical_disk

        self.controller = None
        # initialize volume name
        self.volume_name = logical_disk.get('volume_name', None)
        self.drives = []
        self.capacity_bytes = None
        self.span_number = None
        # initialize bootable
        self.bootable = logical_disk.get('is_root_volume', False)

        self._size_gb = logical_disk.get('size_gb')
        self._controller_hint = logical_disk.get('controller')
        self._media_type = logical_disk.get('disk_type')
        self._protocol = logical_disk.get('interface_type')
        self._physical_disks = logical_disk.get('physical_disks')

        # initialize raid level
        _raid_level = logical_disk.get('raid_level')
        self.raid_setting = raid_utils.RAID_SETTINGS.get(_raid_level)
        if not self.raid_setting:
            raise exceptions.NotSupportedRaidLevel(_raid_level)

        # initialize capacity bytes
        if type(self._size_gb) == int:
            self.capacity_bytes = self._size_gb * 1024 * 1024 * 1024
        else:
            self.capacity_bytes = self.MAX_CAPACITY

        # initialize physical disk settings
        self.share_physical_disks = logical_disk.get(
            'share_physical_disks', False)

        # if user has specified physical disk number, use it.
        # (?) Else use min disks number as required by current raid level.
        self.number_of_physical_disks = logical_disk.get(
            'number_of_physical_disks', None)
        if self.number_of_physical_disks:
            min_disk_count = self.raid_setting.get_min_disks()
            if self.number_of_physical_disks < min_disk_count:
                reason = ('number_of_physical_disks is small than min-disk-'
                          'count(%d) required by raid level %s' %
                          (min_disk_count, self.raid_setting.key))
                raise exceptions.InvalidLogicalDiskConfig(
                    config=self._logical_disk, reason=reason)

        self.use_shareable_disk_group = False

    @property
    def is_jbod_mode(self):
        return self.raid_setting.name == raid_utils.JBOD

    @property
    def auto_scale(self):
        """whether use as much free space(size 'max') as possible

        :return: true if yes or false
        """
        return self.capacity_bytes == self.MAX_CAPACITY

    @property
    def use_specified_disks(self):
        """whether user has specified the disks to be used

        :return:
        """
        return self._physical_disks and len(self._physical_disks) > 0

    def init_ctrl(self, controllers):
        # type: (list[Storage]) -> None
        """initialize storage controller for this logical disk

        :param controllers: a list controller object of iBMC
        """
        if len(controllers) == 0:
            raise exceptions.NoRaidControllerFound()

        if not self._controller_hint:
            if len(controllers) != 1:
                raise exceptions.ControllerHintRequired()
            else:
                self.controller = controllers[0]
        else:
            # find storage matches hint or the every controller if no hint
            self.controller = next((ctrl for ctrl in controllers
                                    if ctrl.matches(self._controller_hint)),
                                   None)
            if not self.controller:
                raise exceptions.NoControllerMatchesHint(
                    hint=self._controller_hint)

        if not self.controller.support_oob:
            ctrl_name = (self._controller_hint if self._controller_hint else
                         self.controller.controller_name)
            raise exceptions.ControllerNotSupportOOB(controller=ctrl_name)

        if (self.raid_setting.name not in self.controller.supported_raid_levels
                and self.raid_setting.name != raid_utils.JBOD):
            raise exceptions.NotSupportedRaidLevel(
                self.raid_setting.key, controller=self._controller_hint)

    def init_disks(
            self,
            physical_disks,  # type: list[raid_utils.PhysicalDisk]
            physical_disk_groups  # type: list[raid_utils.PhysicalDiskGroup]
    ):
        """

        :param physical_disks: a list of exists physical disk object
        :param physical_disk_groups: a list of exists physical disk group
            object
        :return:
        """
        # disks that are excludable and matches required
        #   "media type" and "protocol"
        excludable_disks = [
            d for d in physical_disks
            if d.drive.matches(d.drive.id, media_type=self._media_type,
                               protocol=self._protocol) and d.is_excludable]

        # non-share and use specified disks (2 cases, both size int and max)
        if not self.share_physical_disks and self.use_specified_disks:
            specified_disks = []
            for hint in self._physical_disks:
                disk = self.get_specified_disk(physical_disks, hint)
                if not disk.is_excludable:
                    reason = ('Disk `%s` may has been used by other logical '
                              'disk.' % hint)
                    raise exceptions.InvalidLogicalDiskConfig(
                        config=self._logical_disk, reason=reason)
                specified_disks.append(disk)

            try:
                solution = self.raid_setting.get_best_matched_disks(
                    self.capacity_bytes, specified_disks, len(specified_disks))
                if solution:
                    self.span_number = solution.span
                    for disk in solution.disks:
                        disk.mark_as_exclusive()
                        self.drives.append(disk.drive_id)
                else:
                    raise exceptions.SpecifiedDisksHasNotEnoughSpace(
                        size=self._size_gb, raid=self.raid_setting.key)
            except exceptions.IBMCClientError as e:
                raise exceptions.InvalidLogicalDiskConfig(
                    config=self._logical_disk, reason=str(e))

        # non-share and auto choose disks (2 cases, both size int and max)
        elif not self.share_physical_disks and not self.use_specified_disks:
            try:
                solution = self.raid_setting.get_best_matched_disks(
                    self.capacity_bytes, excludable_disks,
                    self.number_of_physical_disks)
                if solution:
                    self.span_number = solution.span
                    for disk in solution.disks:
                        disk.mark_as_exclusive()
                        self.drives.append(disk.drive_id)
                else:
                    raise exceptions.LackOfDiskSpace()
            except exceptions.IBMCClientError as e:
                raise exceptions.InvalidLogicalDiskConfig(
                    config=self._logical_disk, reason=str(e))

        # share and use specified disks (2 cases, both size int and max)
        elif self.share_physical_disks and self.use_specified_disks:
            # we should find it from exits disk group first
            specified_disks = [self.get_specified_disk(physical_disks, hint)
                               for hint in self._physical_disks]
            disk_group = self.find_disk_group_owns_disks(
                physical_disk_groups, specified_disks)
            if disk_group:
                disk_group.add_pending_capacity_bytes(self.capacity_bytes)
                self.drives = [disk_group.drives[0].drive_id]
                self.use_shareable_disk_group = True
                return

            # if no disk group matches, we need to use free disks
            for i in range(0, len(specified_disks)):
                disk = specified_disks[i]
                if not disk.is_excludable:
                    reason = ('Disk `%s` may has been used by other logical '
                              'disk.' % self._physical_disks[i])
                    raise exceptions.InvalidLogicalDiskConfig(
                        config=self._logical_disk, reason=reason)

            try:
                solution = self.raid_setting.get_best_matched_disks(
                    self.capacity_bytes, specified_disks, len(specified_disks))
                if solution:
                    self.use_shareable_solution(solution, physical_disk_groups)
                else:
                    raise exceptions.LackOfDiskSpace()
            except exceptions.IBMCClientError as e:
                raise exceptions.InvalidLogicalDiskConfig(
                    config=self._logical_disk, reason=str(e))

        elif self.share_physical_disks and not self.use_specified_disks:
            # if any exists disk group matches, we would not compare it with
            # disk solutions. Use it directly.
            disk_group = self.raid_setting.get_best_matched_disk_group(
                self.capacity_bytes, physical_disk_groups)
            if disk_group:
                disk_group.add_pending_capacity_bytes(self.capacity_bytes)
                self.drives = [disk_group.drives[0].drive_id]
                self.use_shareable_disk_group = True
                return

            try:
                solution = self.raid_setting.get_best_matched_disks(
                    self.capacity_bytes, excludable_disks,
                    self.number_of_physical_disks)
                if solution:
                    self.use_shareable_solution(solution, physical_disk_groups)
                else:
                    raise exceptions.LackOfDiskSpace()
            except exceptions.IBMCClientError as e:
                raise exceptions.InvalidLogicalDiskConfig(
                    config=self._logical_disk, reason=str(e))

    def use_shareable_solution(
            self,
            solution,  # type: raid_utils.RaidSolution
            physical_disk_groups  # type: list[raid_utils.PhysicalDiskGroup]
    ):
        # type: (...) -> None
        """use a physical disks shareable solution
        - update drives & span number
        - mark used drives as exclusive
        - update physical disk group

        :param solution:
        :param physical_disk_groups:
        :return:
        """
        self.span_number = solution.span
        drives = [disk.drive for disk in solution.disks]
        self.drives = [drive.drive_id for drive in drives]
        disk_group = raid_utils.PhysicalDiskGroup(
            drives, self.raid_setting, self.span_number)
        disk_group.add_used_capacity_bytes(self.capacity_bytes)
        physical_disk_groups.append(disk_group)
        for disk in solution.disks:
            disk.mark_as_exclusive()

    def find_disk_group_owns_disks(
            self,
            physical_disk_groups,  # type: list[raid_utils.PhysicalDiskGroup]
            specified_physical_disks  # type: list[raid_utils.PhysicalDisk]
    ):
        # type: (...) -> raid_utils.PhysicalDiskGroup
        """Find a disk group which owns all those physical disks.

        :param physical_disk_groups available physical disk groups
        :param specified_physical_disks specified physical disks
        :raises exceptions.InvalidLogicalDiskConfig when a disk group owns
            those physical disks exists, but it does not have enough capacity
            or it has a different raid-level.
        :return physical disk group if it's suitable to create the logical disk
        """
        disk_id_str = ','.join([disk.drive.id
                                for disk in specified_physical_disks])
        LOG.info("Try to find disk-group owns disks %(disks)s",
                 {'disks': disk_id_str})
        disk_group = None
        share_disk_group = False
        for dg in physical_disk_groups:
            # FIXME(qianbiao.ng) whether all disks should be present or a
            #  subset disks is ok too? Currently, a subset is allowed.
            share_disk_group = all(disk.drive.id in dg.drive_id_list
                                   for disk in specified_physical_disks)
            if share_disk_group:
                disk_group = dg
                break

        if share_disk_group:
            try:
                disk_group.validate_if_suitable_for(self.capacity_bytes,
                                                    self.raid_setting)
                LOG.info("Find a matched disk-group:: %(disk_group)s. Use it.",
                         {'disk_group': str(disk_group)})
            except exceptions.NotSuitablePhysicalDiskGroup as e:
                LOG.info("Find a disk-group:: %(disk_group)s owns specified "
                         "disks. But it can not be used because:: %(reason)s",
                         {'disk_group': str(disk_group), 'reason': str(e)})
                raise exceptions.InvalidLogicalDiskConfig(
                    config=self._logical_disk, reason=e.message)
        else:
            LOG.info("Could not find any disk-group owns disks%(disks)s",
                     {'disks': disk_id_str})

        return disk_group

    def get_specified_disk(
            self,
            physical_disks,  # type: list[raid_utils.PhysicalDisk]
            disk_hint  # type: str
    ):
        # type: (...) -> raid_utils.PhysicalDisk
        """get the physical disk specified by disk hint, media type and
        protocol.

        :param physical_disks: all physical disk object list
        :param disk_hint: indicates the disk hint specified by caller
        :raises: exceptions.NoDriveMatchesHint when non physical disk matches
        :return: the specified physical disk
        """
        disk = next((disk for disk in physical_disks
                     if disk.drive.matches(disk_hint,
                                           media_type=self._media_type,
                                           protocol=self._protocol)),
                    None)
        if not disk:
            raise exceptions.NoDriveMatchesHint(hint=disk_hint,
                                                media_type=self._media_type,
                                                protocol=self._protocol)

        disk.hint = disk_hint
        return disk

    def guess_span_number(self):  # pragma: no cover
        """(deprecated) guess span number
        """
        if self.raid_setting.name in [raid_utils.RAID0, raid_utils.RAID1,
                                      raid_utils.RAID5, raid_utils.RAID6]:
            self.span_number = 1
        elif self.raid_setting.name in [raid_utils.RAID50, raid_utils.RAID60]:
            for n in [2, 3, 5, 7]:
                if len(self.drives) % n == 0:
                    self.span_number = n
        elif self.raid_setting.name == raid_utils.RAID10:
            self.span_number = len(self.drives) >> 1

    def to_create_volume_payload(self):
        capacity_bytes = (None if self.capacity_bytes == self.MAX_CAPACITY else
                          self.capacity_bytes)
        if not self.use_shareable_disk_group:
            payload = dict(
                storage_id=self.controller.id, volume_name=self.volume_name,
                raid_level=self.raid_setting.name, drives=self.drives,
                capacity_bytes=capacity_bytes, span=self.span_number,
                bootable=self.bootable)
        else:
            payload = dict(
                storage_id=self.controller.id, volume_name=self.volume_name,
                raid_level=None, drives=self.drives,
                capacity_bytes=capacity_bytes, span=None,
                bootable=self.bootable)
        return payload

    def __str__(self):
        return str(self._logical_disk)


def sort_and_group_pending_logical_disk_list(logical_disks):
    # type: (list[LogicalDisk]) -> dict(str, list[LogicalDisk])
    """

    :rtype: dict(str, list[LogicalDisk])
    :param logical_disks:
    :return:
    """

    def compare_pending_logical_disks(logical_disk1, logical_disk2):
        # type: (LogicalDisk, LogicalDisk) -> int
        """

        :param logical_disk1:
        :param logical_disk2:
        :return:
        """
        # order by controller first
        if logical_disk1.controller.id != logical_disk2.controller.id:
            gt = logical_disk1.controller.id > logical_disk2.controller.id
            return 1 if gt else -1

        # volumes with specified drives can be processed without cleaning
        if len(logical_disk1.drives) != len(logical_disk2.drives):
            return len(logical_disk1.drives) - len(logical_disk2.drives)

        # volume with 'MAX' size and empty drives should be processed at last
        if logical_disk1.capacity_bytes != logical_disk2.capacity_bytes:
            return logical_disk1.capacity_bytes - logical_disk2.capacity_bytes

        return 0  # pragma: no cover

    if six.PY2:  # pragma: no cover
        _logical_disk_list = sorted(
            logical_disks, cmp=compare_pending_logical_disks, reverse=True)
    elif six.PY3:
        _logical_disk_list = sorted(
            logical_disks, key=cmp_to_key(compare_pending_logical_disks),
            reverse=True)

    grouped_logical_disks = dict(
        (key, list(it))
        for key, it in groupby(_logical_disk_list, lambda it: it.controller.id)
    )

    return grouped_logical_disks


def build_disk_groups(ctrl):
    disk_groups = []
    for volume in ctrl.volumes():
        disk_group = next((dg for dg in disk_groups
                           if dg.owns_volume(volume)), None)
        if disk_group:
            disk_group.add_used_capacity_bytes(volume.capacity_bytes)
        else:
            disk_group = raid_utils.PhysicalDiskGroup.from_volume(
                volume, ctrl.drives())
            disk_groups.append(disk_group)
    return disk_groups


class IBMCStorageClient(BaseApiClient):
    """iBMC storage API Client"""

    def __init__(self, connector, ibmc_client=None):
        """Initial a iBMC System storage Resource Client

        :param connector: iBMC http connector
        :param ibmc_client: a reference to global
            :class:`~ibmc_client.IBMCClient` object
        """
        super(IBMCStorageClient, self).__init__(connector, ibmc_client)

    def list(self):
        # type: () -> list[Storage]
        """Get all storage controllers of this iBMC

        :return: a list of storage controller
                (:class:`~ibmc_client.resources.system.storage.Storage`) object
        """
        url = '%s/Storages' % self.connector.system_base_url
        return self.load_odata_collection(url, Storage)

    def get(self, storage_id):
        # type: (str) -> Storage
        """get storage controller by raid storage id

        :param storage_id: indicates the id of storage
        :return: A storage controller(:class:`~ibmc_client.resources.system
                .storage.Storage`) object
        """
        url = '%s/Storages/%s' % (self.connector.system_base_url, storage_id)
        return self.load_odata(url, Storage)

    def delete_all_raid_configuration(self):
        """Delete all RAID configuration.

        :return:
        """
        LOG.info("Start delete all RAID configuration.")

        # waiting until storage ready
        self.waiting_storage_ready()

        storage_collection = self.list()
        for storage in storage_collection:
            if not storage.support_oob:
                raise exceptions.ControllerNotSupportOOB(
                    controller=storage.controller_name)
            LOG.info("Start delete RAID configuration for %s.", storage.id)

            # we do not need to restore storage
            # restore RAID controller
            # storage.restore()
            # storage.set(copy_back=True, smarter_copy_back=True, jbod=False)

            # delete volume collection of RAID controller
            storage.delete_volume_collection()

            # restore all drives
            for drive in storage.drives():
                drive.restore()

            LOG.info("Delete RAID configuration for %s done.", storage.id)

        if not storage_collection:
            LOG.info("No Storage present in this server.")

        LOG.info("Delete all RAID configuration done.")

    def apply_raid_configuration(self, logical_disks):
        """Apply RAID configuration.

        :param logical_disks: a list of JSON dictionaries which represents
            the logical disks to be created. The JSON dictionary should match
            the (ibmc_client.raid_config_schema.json) scheme. check
            https://docs.openstack.org/ironic/latest/admin/raid.html for
            details. A typical logical_disks may looks like::

            [
                {
                  "size_gb": 50,
                  "raid_level": "1+0",
                  "controller": "RAID.Integrated.1-1",
                  "volume_name": "root_volume",
                  "is_root_volume": true,
                  "physical_disks": [
                    "Disk.Bay.0:Encl.Int.0-1:RAID.Integrated.1-1",
                    "Disk.Bay.1:Encl.Int.0-1:RAID.Integrated.1-1"
                  ]
                },
                {
                  "size_gb": 100,
                  "raid_level": "5",
                  "controller": "RAID.Integrated.1-1",
                  "volume_name": "data_volume",
                  "physical_disks": [
                    "Disk.Bay.2:Encl.Int.0-1:RAID.Integrated.1-1",
                    "Disk.Bay.3:Encl.Int.0-1:RAID.Integrated.1-1",
                    "Disk.Bay.4:Encl.Int.0-1:RAID.Integrated.1-1"
                  ]
                },
                .....
              ]

        :return:
        """
        LOG.info('Start apply RAID configuration:: %(logical_disks)s',
                 {'logical_disks': logical_disks})

        # waiting until storage ready
        self.waiting_storage_ready()

        # load all controllers
        controllers = self.list()

        # prepare pending volume list
        pending_volume_list = []
        for logical_disk in logical_disks:
            logical_disk = LogicalDisk(logical_disk)
            logical_disk.init_ctrl(controllers)
            pending_volume_list.append(logical_disk)

        groups = defaultdict(list)  # type: dict(str, list[LogicalDisk])
        for pending_volume in pending_volume_list:
            groups[pending_volume.controller.id].append(pending_volume)
        # validate volumes
        self.validate_pending_volumes(groups)

        # assign drives for not specified volumes
        for (ctrl_id, pending_volumes) in groups.items():
            ctrl = next(ctrl for ctrl in controllers if ctrl.id == ctrl_id)
            jbod_mode = any(v.is_jbod_mode for v in pending_volumes)

            # handle JBOD mode
            if jbod_mode:
                ctrl.set(jbod=True)
                continue

            share_disk_enabled = any(v.share_physical_disks
                                     for v in pending_volumes)
            disk_groups = build_disk_groups(ctrl) if share_disk_enabled else []
            physical_disks = [raid_utils.PhysicalDisk(drive)
                              for drive in ctrl.drives()]

            # handle other RAID levels
            ordered_pending_volumes = []
            """
            step1:: handle volumes (2 cases)
                [x] share physical disks
                [o] specified physical disks
                [o] size "max|int"

            Notes::
                - make sure all specified disks has not been used
                - make sure all specified disks will not be used later
            """
            ordered_pending_volumes.extend([v for v in pending_volumes
                                            if not v.share_physical_disks
                                            and v.use_specified_disks])

            """
            step2:: handle volumes (1 cases)
                [x] share physical disks
                [x] specified physical disks
                [o] size "int"
            Notes::
                - use disks which waste as less as better
                - make sure all specified disks has not been used
                - make sure all specified disks will not be used later
            """
            ordered_pending_volumes.extend([v for v in pending_volumes
                                            if not v.share_physical_disks
                                            and not v.use_specified_disks
                                            and not v.auto_scale])

            """
            step3:: handle volumes (1 cases)
                [o] share physical disks
                [o] specified physical disks
                [o] size "int"
            """
            ordered_pending_volumes.extend([v for v in pending_volumes
                                            if v.share_physical_disks
                                            and v.use_specified_disks
                                            and not v.auto_scale])

            """
            step4:: handle volumes (1 cases)
                [o] share physical disks
                [o] specified physical disks
                [o] size "max"
            """
            ordered_pending_volumes.extend([v for v in pending_volumes
                                            if v.share_physical_disks
                                            and v.use_specified_disks
                                            and v.auto_scale])

            """
            step5:: handle volumes (1 cases)
                [o] share physical disks
                [x] specified physical disks
                [o] size "int"
            """
            ordered_pending_volumes.extend([v for v in pending_volumes
                                            if v.share_physical_disks
                                            and not v.use_specified_disks
                                            and not v.auto_scale])

            """
            step6:: handle volumes (1 cases)
                [o] share physical disks
                [x] specified physical disks
                [o] size "max"
            Notes::
                (?) Is this case really exists?
            """
            ordered_pending_volumes.extend([v for v in pending_volumes
                                            if v.share_physical_disks
                                            and not v.use_specified_disks
                                            and v.auto_scale])

            """
            step7:: handle volumes (1 cases)
                [x] share physical disks
                [x] specified physical disks
                [o] size "max"
            """
            ordered_pending_volumes.extend([
                v for v in pending_volumes if (not v.share_physical_disks
                                               and not v.use_specified_disks
                                               and v.auto_scale)])

            for pending_volume in ordered_pending_volumes:
                pending_volume.init_disks(physical_disks, disk_groups)

            for pending_volume in ordered_pending_volumes:
                self.ibmc_client.system.volume.create(
                    **pending_volume.to_create_volume_payload())
                time.sleep(constants.RAID_TASK_EFFECT_SECONDS)

    def waiting_storage_ready(self):
        # waiting util storage ready
        LOG.info('Waiting until storage ready.')
        while True:
            system = self.ibmc_client.system.get()
            try:
                if system.is_storage_ready:
                    LOG.info('Storage is ready.')
                    break
                LOG.info('Storage is not ready. waiting...')
            except exceptions.FeatureNotSupported:
                LOG.info('Query `IsStorageReady` feature is not supported, '
                         'will treat it as ready now.')
                break
            time.sleep(30)

    @staticmethod
    def validate_pending_volumes(groups):
        for (ctrl_id, volumes) in groups.items():
            # - (?) share disks & disks not specified but size 'max'
            # - size 'max' & disks not specified at most could appear once
            # unlimit_auto_scale_volumes = [v for v in volumes if v.auto_scale
            #                               and not v.use_specified_disks]
            # if len(unlimit_auto_scale_volumes) > 1:
            #     reason = ('At most one logical disk config can be size-gb('
            #               '"max") but no physical-disks specified.')
            #     raise InvalidLogicalDiskConfig(
            #         config=unlimit_auto_scale_volumes[0], reason=reason)

            jbod_volumes = [v for v in volumes if v.is_jbod_mode]
            if 0 < len(jbod_volumes) != len(volumes):
                reason = 'JBOD mode could not work with other RAID level.'
                raise exceptions.InvalidLogicalDiskConfig(
                    config=jbod_volumes[0], reason=reason)
