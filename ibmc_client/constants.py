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

# System' PowerState constants

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
