# -*- coding: utf-8 -*-
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

# Version 0.0.2

# RAID rsync task wait effect time seconds
RAID_TASK_EFFECT_SECONDS = 20

# HTTP request method shortcut

HEAD = 'HEAD'
"""http method HEAD"""

GET = 'GET'
"""http method get"""

POST = 'POST'
"""http method POST"""

PATCH = 'PATCH'
"""http method PATCH"""

PUT = 'PUT'
"""http method PUT"""

DELETE = 'DELETE'

# Redfish HTTP Headers

HEADER_ETAG = 'ETag'
"""Redfish API HTTP header 'ETag'"""

HEADER_AUTH_TOKEN = 'X-Auth-Token'
"""Redfish API HTTP header 'X-Auth-Token'"""

HEADER_IF_MATCH = 'If-Match'
"""Redfish API HTTP header 'If-Match'"""

HEADER_CONTENT_TYPE = 'Content-Type'
"""Redfish API HTTP header 'Content-Type'"""

# System PowerState constants

SYSTEM_POWER_STATE_ON = 'On'
"""The system is powered on"""

SYSTEM_POWER_STATE_OFF = 'Off'
"""The system is powered off, although some components may continue to
   have AUX power such as management controller"""

# Boot source target constants

BOOT_SOURCE_TARGET_NONE = 'None'
"""Boot from the normal boot device"""

BOOT_SOURCE_TARGET_PXE = 'Pxe'
"""Boot from the Pre-Boot EXecution (PXE) environment"""

BOOT_SOURCE_TARGET_FLOPPY = 'Floppy'
"""Boot from the floppy disk drive"""

BOOT_SOURCE_TARGET_CD = 'Cd'
"""Boot from the CD/DVD disc"""

BOOT_SOURCE_TARGET_HDD = 'Hdd'
"""Boot from a hard drive"""

BOOT_SOURCE_TARGET_BIOS_SETUP = 'BiosSetup'
"""Boot to the BIOS Setup Utility"""

# Boot source mode constants

BOOT_SOURCE_MODE_BIOS = 'Legacy'
BOOT_SOURCE_MODE_UEFI = 'UEFI'

# Boot source enabled constants

BOOT_SOURCE_ENABLED_ONCE = 'Once'
BOOT_SOURCE_ENABLED_CONTINUOUS = 'Continuous'
BOOT_SOURCE_ENABLED_DISABLED = 'Disabled'

# Reset action constants
RESET_NMI = 'Nmi'
RESET_ON = 'On'
RESET_FORCE_OFF = 'ForceOff'
RESET_GRACEFUL_SHUTDOWN = 'GracefulShutdown'
RESET_FORCE_RESTART = 'ForceRestart'
RESET_FORCE_POWER_CYCLE = 'ForcePowerCycle'

# Task status
TASK_STATUS_NEW = 'New'
TASK_STATUS_STARTING = 'Starting'
TASK_STATUS_RUNNING = 'Running'
TASK_STATUS_SUSPENDED = 'Suspended'
TASK_STATUS_INTERRUPTED = 'Interrupted'
TASK_STATUS_PENDING = 'Pending'
TASK_STATUS_STOPPING = 'Stopping'
TASK_STATUS_COMPLETED = 'Completed'
TASK_STATUS_KILLED = 'Killed'
TASK_STATUS_EXCEPTION = 'Exception'
TASK_STATUS_SERVICE = 'Service'

TASK_STATUS_PROCESSING = (TASK_STATUS_NEW, TASK_STATUS_STARTING,
                          TASK_STATUS_RUNNING, TASK_STATUS_SUSPENDED,
                          TASK_STATUS_PENDING, TASK_STATUS_STOPPING)

TASK_STATUS_PROCESSED = (TASK_STATUS_INTERRUPTED, TASK_STATUS_EXCEPTION,
                         TASK_STATUS_KILLED, TASK_STATUS_COMPLETED)

TASK_STATUS_FAILED = (TASK_STATUS_INTERRUPTED, TASK_STATUS_KILLED,
                      TASK_STATUS_EXCEPTION)

# Initial volume types
VOLUME_INIT_QUICK = 'QuickInit'
"""perform quick initialization. No task will be created."""

VOLUME_INIT_FULL = 'FullInit'
"""perform complete initialization. A task will be created."""

VOLUME_INIT_CANCEL = 'CancelInit'
"""cancel the initialization. No task will be created."""

# Online 为某个虚拟磁盘的成员盘，可正常使用，处于在线状态。
# Unconfigured Good 磁盘状态正常，但不是虚拟磁盘的成员盘或热备盘。
# Hot Spare 被设置为热备盘。
# Failed 当“Online”状态或“Hot Spare”状态的磁盘出现不可恢复的错误时，会体现为此状态。
# Rebuild 硬盘正在进行数据重建，以保证虚拟磁盘的数据冗余性和完整性。
# Unconfigured Bad “Unconfigured Good”状态磁盘或未初始化的磁盘，出现
# 无法恢复的错误时，会体现为此状态。
# Missing “Online”状态的磁盘被拔出后，体现为此状态。
# Offline 为某个虚拟磁盘的成员盘，不可正常使用，处于离线状态。
# Shield State 物理磁盘在做诊断操作时的临时状态。
# Copyback 新盘正在替换故障成员盘。
# Optimal 虚拟磁盘状态良好，所有成员盘均在线。
# Degraded 虚拟磁盘状态异常，存在成员盘故障或离线的情况。
# Failed 虚拟磁盘故障。
# Partial Degraded 当RAID组中的物理硬盘故障或离线的数量未超过该RAID组级
# 别支持的最大故障硬盘的数量时，RAID组会体现为部分降级状态。

# drive firmware state

DRIVE_FM_STATE_JBOD = 'JBOD'
"""drive firmware state:: JBOD"""

DRIVE_FM_STATE_ONLINE = 'Online'
"""drive firmware state:: Online"""

DRIVE_FM_STATE_HOTSPARE = 'HotSpareDrive'
"""drive firmware state:: Hot Spare"""

DRIVE_FM_STATE_UNCONFIG_GOOD = 'UnconfiguredGood'
"""drive firmware state:: Unconfigured Good"""

# drive hot spare type

HOT_SPARE_NONE = 'None'
"""drive hot spare type None"""

HOT_SPARE_GLOBAL = 'Global'
"""drive hot spare type Global"""

HOT_SPARE_DEDICATED = 'Dedicated'
"""drive hot spare type Dedicated"""
