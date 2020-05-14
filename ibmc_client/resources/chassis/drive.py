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

from ibmc_client import utils, constants
from ibmc_client.resources import BaseResource, Status, PROP_RESOURCE_ID

LOG = logging.getLogger(__name__)


class Drive(BaseResource):
    """iBMC chassis Drive Resource Model"""

    @property
    def drive_id(self):
        """get Oem drive id

        :return: drive id
        """
        return self._oem.get('DriveID', None)

    @property
    def id(self):
        """get drive id

        :return: drive id
        """
        return self._json.get('Id', None)

    @property
    def name(self):
        """get drive name

        :return: drive name
        """
        return self._json.get('Name', None)

    @property
    def model(self):
        """get drive model

        :return: drive model
        """
        return self._json.get('Model', None)

    @property
    def protocol(self):
        """get drive protocol

        typical protocol: SATA, SAS, SCSI.
        :return: drive protocol
        """
        return self._json.get('Protocol', None)

    @property
    def media_type(self):
        """get drive Media Type

        typical media types: HDD, SSD
        :return: drive Media Type
        """
        return self._json.get('MediaType', None)

    @property
    def manufacturer(self):
        """get drive Manufacturer

        :return: drive Manufacturer
        """
        return self._json.get('Manufacturer', None)

    @property
    def serial_number(self):
        """get drive serial number

        :return: drive serial number
        """
        return self._json.get('SerialNumber', None)

    @property
    def status(self):
        """get drive status

        :return: drive status
        """
        return Status(self._json.get('Status', {}))

    @property
    def firmware_state(self):
        """get drive firmware state

        :return: drive firmware state
        """
        return self._oem.get('FirmwareStatus', None)

    @property
    def hotspare_type(self):
        """get drive hot spare type

        :return: drive hot spare type
        """
        return self._json.get('HotspareType', None)

    @property
    def capacity_bytes(self):
        """get drive capacity bytes

        :return: drive capacity bytes
        """
        return self._json.get('CapacityBytes', None)

    @property
    def volume_odata_id_collection(self):
        """get volume odata id collection which this drive belongs to

        :return: volume odata id collection
        """
        odata_collection = self._json.get('Links', {}).get('Volumes', [])
        return [odata.get(PROP_RESOURCE_ID) for odata in odata_collection]

    def has_fm_state(self, state):
        return self.firmware_state == state

    def is_unconfig_good(self):
        return self.has_fm_state(constants.DRIVE_FM_STATE_UNCONFIG_GOOD)

    def matches(self, hint, media_type=None, protocol=None):
        hint_matches = hint and hint in (
            self.id, self.name, self.serial_number, str(self.drive_id))

        media_matched = not media_type or (
            media_type.lower() == self.media_type.lower())
        protocol_matches = not protocol or (
            protocol.lower() == self.protocol.lower())
        return hint_matches and media_matched and protocol_matches

    def set(self, firmware_state=None, hotspare_type=None):
        """update drive

        :param firmware_state: indicates firmware state to update
        :param hotspare_type: indicates hotspare type to update
        :return:
        """

        oem = ({"Huawei": {"FirmwareStatus": firmware_state}}
               if firmware_state else None)

        payload = utils.remove_empty_from_dict({
            "HotspareType": hotspare_type,
            "Oem": oem
        })

        if payload:
            resp = self._connector.request(constants.PATCH, self.odata_id,
                                           json=payload, etag=self.etag)
            self.refresh(resp)

    def restore(self):
        """restore drive

        - set hot-spare type to None if current state is HotSpareDrive
        - set disk state to UnconfiguredGood if current state is JBOD

        :return:
        """
        LOG.info('Start to restore drive %s.', self.id)
        settings = {}
        if self.firmware_state == constants.DRIVE_FM_STATE_HOTSPARE:
            settings['hotspare_type'] = constants.HOT_SPARE_NONE

        if self.firmware_state == constants.DRIVE_FM_STATE_JBOD:
            settings['firmware_state'] = constants.DRIVE_FM_STATE_UNCONFIG_GOOD

        if settings:
            self.set(**settings)
            logging.info('drive %s has been restored, restore settings:: %s.',
                         self.id, str(settings))
        else:
            LOG.info('drive %s has nothing to restore.', self.id)
