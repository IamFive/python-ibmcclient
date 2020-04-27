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

from ibmc_client.api import BaseApiClient
from ibmc_client.constants import GET, PATCH, POST
from ibmc_client.resources.system.storage import Volume
from ibmc_client.resources.task import Task
from ibmc_client.utils import remove_empty_from_dict


# class CreateVolumePayload(object):
#     StorageId = None
#     VolumeName = None
#     VolumeRaidLevel = None
#     Drives = None
#     CapacityBytes = None
#     SpanNumber = None
#     Bootable = False
#
#     def __init__(self, storage_id=None, volume_name=None, raid_level=None,
#                  drives=None, capacity_bytes=None, span=None, bootable=None):
#         self.StorageId = storage_id
#         self.VolumeName = volume_name
#         self.VolumeRaidLevel = raid_level
#         self.CapacityBytes = capacity_bytes
#         self.Drives = drives
#         self.SpanNumber = span
#         self.Bootable = bootable
#
#     def to_dict(self):
#         oem = remove_empty_from_dict({
#             "VolumeName": self.VolumeName,
#             "VolumeRaidLevel": self.VolumeRaidLevel,
#             "Drives": self.Drives,
#             "SpanNumber": self.SpanNumber if self.SpanNumber > 1 else None
#         })
#
#         payload = {
#             "CapacityBytes": self.CapacityBytes,
#             "Oem": {
#                 "Huawei": oem
#             }
#         }
#         return remove_empty_from_dict(payload)


class IbmcVolumeClient(BaseApiClient):
    """iBMC volume API Client"""

    def __init__(self, connector, ibmc_client=None):
        """Initial a iBMC volume Resource Client

        :param connector: iBMC http connector
        :param ibmc_client: a reference to global
            :class:`~ibmc_client.IBMCClient` object
        """
        super(IbmcVolumeClient, self).__init__(connector, ibmc_client)

    def get(self, storage_id, volume_id):
        """get volume by id

        :param storage_id: indicates the id of storage
        :param volume_id: indicates the id of volume
        :return: A Volume (:class:`~ibmc_client.resources.chassis.volume
                 .Volume`) object
        """
        url = '%s/Storages/%s/Volumes/%s' % (self.connector.system_base_url,
                                             storage_id, volume_id)
        resp = self.connector.request(GET, url)
        return Volume(resp, ibmc_client=self.ibmc_client)

    def list(self, storage_id):
        """get all volumes belongs to the storage

        :param storage_id: indicates the id of storage
        :return: A list of Volume (:class:`~ibmc_client.resources.chassis
                .volume.Volume`) object
        """
        url = '%s/Storages/%s/Volumes' % (self.connector.system_base_url,
                                          storage_id)
        collection = self.connector.request(GET, url).json()
        members = collection.get('Members', [])
        return [self.load_odata(member, Volume) for member in members]

    def init(self, storage_id, volume_id, init_type):
        """init volume

        :param storage_id: indicates the id of storage
        :param volume_id: indicates the id of volume
        :param init_type: Indicates the initialization action of volume.
            Available Value Set:  QuickInit, FullInit, CancelInit.
            - QuickInit: perform quick initialization. No task will be created
            - FullInit: perform complete initialization. A task will be created
            - CancelInit: cancel the initialization. No task will be created
        :return:
        :raises: a sub-class of IBMCClientError when http request failed
        """
        url = '%s/Storages/%s/Volumes/%s/Actions/Volume.Initialize' % (
            self.connector.system_base_url, storage_id, volume_id)

        payload = {
            "Type": init_type
        }
        self.connector.request(POST, url, json=payload)

    def create(self, storage_id=None, volume_name=None, raid_level=None,
               drives=None, capacity_bytes=None, span=None, bootable=None):
        """Create a new volume

        :param storage_id: indicates the storage id
        :param volume_name: indicates the name of to create volume
        :param raid_level: indicates the raid-level of to create volume
        :param drives: indicates the used drives of to create volume
        :param capacity_bytes: indicates the capacity bytes of to create volume
        :param span: indicates the span number of to create volume
        :param bootable: indicates whether the volume is a bootable volume
        :return: created volume id
        """

        url = '%s/Storages/%s/Volumes' % (self.connector.system_base_url,
                                          storage_id)

        oem = remove_empty_from_dict({
            "VolumeName": volume_name,
            "VolumeRaidLevel": raid_level,
            "Drives": drives,
            "SpanNumber": span if (span and span > 1) else None
        })

        payload = remove_empty_from_dict({
            "CapacityBytes": capacity_bytes,
            "Oem": {
                "Huawei": oem
            }
        })

        resp = self.connector.request(POST, url, json=payload)
        task = self.ibmc_client.task.wait_task(
            Task(resp, ibmc_client=self.ibmc_client))
        task.raise_if_failed()

        created_volume_odata_id = task.message_args[0]
        # set as boot volume if necessary
        if bootable:
            self.set_bootable(created_volume_odata_id, bootable)

        return created_volume_odata_id.split('/')[-1]

    def get_volume_odata_id(self, storage_id, volume_id):
        """set volume odata id

        :param storage_id: indicates the storage id
        :param volume_id: indicates the volume id
        :return:
        """
        url = '%s/Storages/%s/Volumes/%s' % (
            self.connector.system_base_url, storage_id, volume_id)
        return url

    def set_bootable(self, volume_odata_id, bootable):
        """set volume as boot disk

        :param volume_odata_id: indicates the volume odata id
        :param bootable:
        :return:
        """
        payload = {
            "Oem": {
                "Huawei": {
                    "BootEnable": bootable
                }
            }
        }

        url = self.connector.get_url(volume_odata_id)
        self.connector.request(PATCH, url, json=payload)

    def delete(self, storage_id, volume_id):
        """delete volume

        :param storage_id: indicates the storage id to delete
        :param volume_id: indicates the volume id to delete
        :return: volume deletion task with stable status
        """
        url = '%s/Storages/%s/Volumes/%s' % (self.connector.system_base_url,
                                             storage_id, volume_id)
        return self.delete_by_odata_id(url)

    def delete_by_odata_id(self, odata_id):
        """delete volume by volume-odata-id

        :param odata_id: indicates the odata resource id of volume
        :return: volume deletion task with stable status
        """
        resp = self.delete_odata(odata_id)
        task = self.ibmc_client.task.wait_task(
            Task(resp, ibmc_client=self.ibmc_client))
        return task
