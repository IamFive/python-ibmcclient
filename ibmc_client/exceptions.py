# Copyright 2019 HUAWEI, Inc. All Rights Reserved.
# Copyright 2017 Red Hat, Inc. All Rights Reserved.
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

import logging

from six.moves import http_client

LOG = logging.getLogger(__name__)


class IBMCClientError(Exception):
    """Basic exception for errors"""

    message = None

    def __init__(self, **kwargs):
        if self.message and kwargs:
            self.message = self.message % kwargs

        super(IBMCClientError, self).__init__(self.message)


class IBMCClientOperationError(IBMCClientError):

    def __init__(self, error, **kwargs):
        self.message = error
        super(IBMCClientOperationError, self).__init__(**kwargs)


class IBMCConnectionError(IBMCClientError):
    message = 'Unable to connect to %(url)s. Error: %(error)s'


class MissingAttributeError(IBMCClientError):
    message = ('The attribute %(attribute)s is missing from the '
               'resource %(resource)s')


class MalformedAttributeError(IBMCClientError):
    message = ('The attribute %(attribute)s is malformed in the '
               'resource %(resource)s: %(error)s')


class MissingActionError(IBMCClientError):
    message = ('The action %(action)s is missing from the '
               'resource %(resource)s')


class InvalidParameterValueError(IBMCClientError):
    message = ('The parameter "%(parameter)s" value "%(value)s" is invalid. '
               'Valid values are: %(valid_values)s')


class NothingToApplyError(IBMCClientError):
    message = 'Nothing to apply, at least one property should be specified.'


class ArchiveParsingError(IBMCClientError):
    message = 'Failed parsing archive "%(path)s": %(error)s'


class IBMCHttpRequestError(IBMCClientError):
    """Basic exception for HTTP errors"""

    status_code = None
    """HTTP status code."""

    body = None
    """Error JSON body, if present."""

    code = 'Base.1.0.GeneralError'
    """Error code defined in the Redfish specification, if present."""

    detail = None
    """Error message defined in the Redfish specification, if present."""

    message = 'HTTP %(method)s %(url)s returned code %(code)s. %(error)s'

    def __init__(self, method, url, response):
        self.status_code = response.status_code
        try:
            body = response.json()
        except ValueError:
            LOG.warning('Error response from %(method)s %(url)s '
                        'with status code %(code)s has no JSON body',
                        {'method': method, 'url': url, 'code':
                            self.status_code})
            error = 'unknown error'
        else:
            self.body = body.get('error', {})
            # TODO (qianbiao.ng): handle partial failure situation
            self.extended_info_list = self.body.get('@Message.ExtendedInfo',
                                                    [])
            if len(self.extended_info_list) > 0:
                info = self.extended_info_list[0]
                error = ('[%(Severity)s] %(Message)s '
                         'Resolution: %(Resolution)s') % info
            else:
                error = ('http status code: %d, http response: %s' %
                         (self.status_code, self.body))

        kwargs = {'method': method, 'url': url, 'code': self.status_code,
                  'error': error}
        LOG.info(('HTTP response for %(method)s %(url)s -> '
                  'status code: %(code)s, error: %(error)s'), kwargs)
        super(IBMCHttpRequestError, self).__init__(**kwargs)


class BadRequestError(IBMCHttpRequestError):
    pass


class ResourceNotFoundError(IBMCHttpRequestError):
    # Overwrite the complex generic message with a simpler one.
    message = 'Resource %(url)s not found'


class ServerSideError(IBMCHttpRequestError):
    pass


class AccessError(IBMCHttpRequestError):
    pass


class MissingXAuthToken(IBMCHttpRequestError):
    message = ('No X-Auth-Token returned from remote host when '
               'attempting to establish a session. Error: %(error)s')


class NoControllerMatchesHint(IBMCClientError):
    message = ('No RAID storage controller matches hint %(hint)s. Please '
               'using storage-id, storage-name or storage-controller-name as '
               'controller hint.')


class NoDriveMatchesHint(IBMCClientError):
    message = ('No available physical disk matches hint: %(hint)s, '
               'media-type: %(media_type)s, protocol: %(protocol)s. Please '
               'using HUAWEI drive-id, drive id, drive name or drive '
               'serial-number as physical disk hint.')

    def __init__(self, **kwargs):
        if kwargs['media_type'] is None:
            kwargs['media_type'] = 'any'
        if kwargs['protocol'] is None:
            kwargs['protocol'] = 'any'
        super(NoDriveMatchesHint, self).__init__(**kwargs)


class NotSupportedRaidLevel(IBMCClientError):
    message = 'RAID level %(raid_level)s is supported.'

    def __init__(self, raid_level, controller=None):
        kwargs = {'raid_level': raid_level}
        if controller:
            kwargs.update(controller='controller')
            self.message = ('RAID level %(raid_level)s is supported by '
                            'controller %(controller)s.')
        super(NotSupportedRaidLevel, self).__init__(**kwargs)


class NoRaidControllerFound(IBMCClientError):
    message = 'No RAID storage controller found.'


class ControllerHintRequired(IBMCClientError):
    message = ('Option `controller` is required because more than one RAID '
               'storage controller exists. Please review target-raid-config.')


class TaskFailed(IBMCClientError):
    message = '%(message)s'


class InvalidPhysicalDiskNumber(IBMCClientError):
    message = ('Invalid number_of_physical_disks option value %('
               'number_of_physical_disks)d, it could not work with '
               'raid-level %(raid)s.')


class LackOfDiskSpace(IBMCClientError):
    message = ('There are not enough available disk space to create'
               ' this logical disk.')


class SpecifiedDisksHasNotEnoughSpace(IBMCClientError):
    message = ('The specified physical disks do not have enough space '
               'to create a %(size)dG logical-disk(raid-level %(raid)s).')


class InvalidLogicalDiskConfig(IBMCClientError):
    message = ('Logical-disk config `%(config)s` is invalid, reason: %('
               'reason)s')


class NotSuitablePhysicalDiskGroup(IBMCClientError):
    message = '%(message)s'


class ControllerNotSupportOOB(IBMCClientError):
    message = ('RAID controller `%(controller)s` does not support OOB '
               'management. Currently, ibmc RAID interface can only manage '
               'RAID controller which support OOB management.')


class FeatureNotSupported(IBMCClientError):
    message = ('Feature is not supported by this iBMC server: %(feature)s, '
               'please check the version of this iBMC server.')


def raise_for_response(method, url, response):
    """Raise a correct error class, if needed."""
    if response.status_code < http_client.BAD_REQUEST:
        return
    elif response.status_code == http_client.NOT_FOUND:
        raise ResourceNotFoundError(method, url, response)
    elif response.status_code == http_client.BAD_REQUEST:
        raise BadRequestError(method, url, response)
    elif response.status_code in (http_client.UNAUTHORIZED,
                                  http_client.FORBIDDEN):
        raise AccessError(method, url, response)
    elif response.status_code >= http_client.INTERNAL_SERVER_ERROR:
        raise ServerSideError(method, url, response)
    else:
        raise IBMCHttpRequestError(method, url, response)
