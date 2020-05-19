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


def remove_empty_from_dict(original):
    """get a new dict which removes keys with empty value

    :param dict original: original dict, should not be None
    :return: a new dict which removes keys with empty values
    """
    return dict((k, v) for k, v in original.items()
                if v is not None and v != '' and v != [] and v != {})


def str2bool(v):
    """str bool value to python Boolean

    :param v:
    :return:
    """
    return v.lower() in ("yes", "true", "t", "1")


def human_readable_byte(size_in_byte, suffix='B'):
    # type: (int, str) -> str
    """convert int size in byte to human readable size with unit.

    :param size_in_byte: indicates size in bytes
    :param suffix: suffix append to size unit
    :return: human readable size
    """
    for unit in ['', 'K', 'M', 'G', 'T', 'P', 'E', 'Z']:
        if abs(size_in_byte) < 1024.0:
            return "%3.1f%s%s" % (size_in_byte, unit, suffix)
        size_in_byte /= 1024.0
    return "%.1f%s%s" % (size_in_byte, 'Y', suffix)
