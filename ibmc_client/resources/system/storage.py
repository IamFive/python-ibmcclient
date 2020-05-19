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
from time import sleep

from ibmc_client import utils, exceptions, constants
from ibmc_client.resources import BaseResource, Status, PROP_RESOURCE_ID
from ibmc_client.resources.chassis.drive import Drive

LOG = logging.getLogger(__name__)


class Storage(BaseResource):
    """iBMC System storage controller Resource Model"""

    ACTION_RESTORE = 'Storage.RestoreStorageControllerDefaultSettings'

    _drives = None
    _volumes = None
    _controller = None

    def extra_init_action(self):
        self._drives = None
        self._controller = self._json['StorageControllers'][0]
        self._oem = (self._controller['Oem']['Huawei']
                     if self._controller.get('Oem') else None)

    @property
    def id(self):
        """get Storage id

        :return: Storage id
        """
        return self._json.get('Id', None)

    @property
    def name(self):
        """get Storage name

        :return: Storage name
        """
        return self._json.get('Name', None)

    @property
    def controller_name(self):
        """get storage controller name

        :return: storage controller name
        """
        return self._controller.get('Name', None)

    @property
    def model(self):
        """get storage controller model

        :return: storage controller model
        """
        return self._controller.get('Model', None)

    @property
    def supported_raid_levels(self):
        """get storage controller Supported RAID Levels

        :return: storage controller Supported RAID Levels
        """
        return self._oem.get('SupportedRAIDLevels', [])

    @property
    def support_oob(self):
        """get whether storage controller support OOB

        TODO(turnbig) compatibility between iBMC versions
        :return: true if support else false
        """
        return self._oem.get('OOBSupport', False)

    @property
    def is_jbod_mode(self):
        """get whether storage controller is in jbod mode

        :return: true if jbod mode else false
        """
        return self._oem.get('JBODState', False)

    @property
    def status(self):
        """get storage controller status

        :return: storage controller status
        """
        return Status(self._controller.get('Status', {}))

    def drives(self, force_reload=False):
        # type: (bool) -> list[Drive]
        """get physical drives of this controller

        :return: physical drives
        """
        # cache physical drives
        if not force_reload and self._drives:
            return self._drives

        drive_collection = self._json.get('Drives', [])
        self._drives = [self._ibmc_client.load_odata(_, Drive)
                        for _ in drive_collection]
        return self._drives

    def volumes(self, force_reload=False):
        # type: (bool) -> list[Volume]
        """get logical volumes of this controller

        :return: logical volumes
        """
        # cache physical drives
        if not force_reload and self._volumes:
            return self._volumes

        volume_collection_odata_id = self._json.get('Volumes')
        self._volumes = self._ibmc_client.load_odata_collection(
            volume_collection_odata_id, Volume)
        return self._volumes

    def get_sharable_volumes(self):
        pass

    def summary(self):
        return {
            "Id": self.id,
            "Name": self.name,
            "ControllerName": self.controller_name,
            "Model": self.model,
            "SupportedRAIDLevels": self.supported_raid_levels,
            "OOBSupport": self.support_oob,
            "JBOD": self.is_jbod_mode,
            "PhysicalDisks": [
                {"Id": drive.id, "Name": drive.name, "DriveId": drive.drive_id,
                 "SerialNumber": drive.serial_number,
                 "FirmwareStatus": drive.firmware_state,
                 "CapacityBytes": utils.human_readable_byte(
                     drive.capacity_bytes)}
                for drive in self.drives()
            ],
            "LogicalDisks": [
                {"Id": volume.id, "Name": volume.name,
                 "VolumeName": volume.volume_oem_name,
                 "RaidLevel": volume.raid_level,
                 "SpanNumber": volume.span_number,
                 "Bootable": volume.bootable,
                 "CapacityBytes": utils.human_readable_byte(
                     volume.capacity_bytes),
                 "PhysicalDisks": [
                     odata_id.split('/')[-1]
                     for odata_id in volume.drive_odata_id_collection
                 ]}
                for volume in self.volumes()
            ]
        }

    def matches(self, hint):
        """Check whether current storage matches the hint

        Notes:: if the hint is None or empty, it matches any controller.

        :param hint: a string could be storage id, storage name, storage
            controller name
        :return: true if matches else false
        """
        return hint and hint in (self.id, self.name, self.controller_name)

    def set(self, copy_back=None, smarter_copy_back=None,
            jbod=None):
        """apply settings to storage

        :param copy_back: :bool: Indicates Whether copy back is enabled.
        :param smarter_copy_back: Indicates Whether SMART error copy back is
                enable. Before enabling this function, enable CopyBack first.
        :param jbod: Indicates Whether JBOD is enable.
        :return: A storage controller(:class:`~ibmc_client.resources.system
                .storage.Storage`) object
        """
        settings = utils.remove_empty_from_dict({
            "CopyBackState": copy_back,
            "SmarterCopyBackState": smarter_copy_back,
            "JBODState": jbod
        })

        if not settings:
            raise exceptions.NothingToApplyError()

        payload = {
            "StorageControllers": [
                {
                    "Oem": {
                        "Huawei": settings
                    }
                }
            ]
        }

        resp = self._connector.request(constants.PATCH, self.odata_id,
                                       json=payload, etag=self.etag)
        self.refresh(resp)

    def restore(self):
        """restore RAID storage

        """
        restore_url = self.get_action_uri(self.ACTION_RESTORE)
        self._connector.request(constants.POST, restore_url, json={})

    def delete_volume_collection(self):
        """delete volume collection of a storage

        :return:
        """
        LOG.info("Start delete volumes for storage:: %s.", self.id)
        volume_collection_url = self._json.get('Volumes', {}).get(
            PROP_RESOURCE_ID)
        volume_collection = self._ibmc_client.load_collection_resource(
            volume_collection_url)
        for volume_odata_id in volume_collection.resources:
            LOG.info("Start delete volume:: %s.", volume_odata_id)
            task = self._ibmc_client.system.volume.delete_by_odata_id(
                volume_odata_id)
            task.raise_if_failed()
            LOG.info("Delete volume:: %s done.", volume_odata_id)
        if volume_collection.count == 0:
            LOG.info("No volume present in this storage:: %s", self.id)
        else:
            # sleep some seconds to make sure the deletion has completely
            # take effect.
            sleep(constants.RAID_TASK_EFFECT_SECONDS)
            LOG.info("Delete volumes for storage:: %s done.", self.id)


class Volume(BaseResource):
    """iBMC system volume Resource Model"""

    @property
    def id(self):
        """get volume id

        :return: volume id
        """
        return self._json.get('Id', None)

    @property
    def name(self):
        """get volume name

        :return: volume name
        """
        return self._json.get('Name', None)

    @property
    def status(self):
        """get volume status

        :return: volume status
        """
        return Status(self._json.get('Status', {}))

    @property
    def capacity_bytes(self):
        """get volume capacity bytes

        :return: volume capacity bytes
        """
        return self._json.get('CapacityBytes', None)

    @property
    def volume_oem_name(self):
        """get volume OEM name

        :return: volume OEM name
        """
        return self._oem.get('VolumeName', None)

    @property
    def raid_level(self):
        """get volume raid level

        :return: volume raid level
        """
        return self._oem.get('VolumeRaidLevel', None)

    @property
    def span_number(self):
        """get volume span number

        :return: volume span number
        """
        return self._oem.get('SpanNumber', None)

    @property
    def drive_number_per_span(self):
        """get volume drive number per span

        :return: volume drive number per span
        """
        return self._oem.get('NumDrivePerSpan', None)

    @property
    def bootable(self):
        """get whether volume bootable or not

        :return: true if bootable else false default None
        """
        return self._oem.get('BootEnable', None)

    @property
    def bgi_enabled(self):
        """get whether volume BGI is enabled

        :return: true if enabled else false default None
        """
        return self._oem.get('BGIEnable', None)

    @property
    def drive_odata_id_collection(self):
        """get drive odata id collection that belongs to this volume

        :return: drive odata id collection (list[str])
        """
        odata_collection = self._json.get('Links', {}).get('Drives', [])
        return [odata.get(PROP_RESOURCE_ID) for odata in odata_collection]
