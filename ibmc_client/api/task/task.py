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

from ibmc_client.api import BaseApiClient
from ibmc_client import constants
from ibmc_client.resources.task import Task

LOG = logging.getLogger(__name__)


class IbmcTaskClient(BaseApiClient):
    """iBMC TaskService API Client"""

    RECHECK_TASK_DELAY_IN_SECONDS = 3

    def __init__(self, connector, ibmc_client=None):
        """Initial a iBMC TaskService Resource Client

        :param connector: iBMC http connector
        :param ibmc_client: a reference to global
            :class:`~ibmc_client.IBMCClient` object
        """
        super(IbmcTaskClient, self).__init__(connector, ibmc_client)

    def get(self, task_id):
        url = '%s/Tasks/%s' % (self.connector.task_service_base_url, task_id)
        return self.load_odata(url, Task)

    def wait_task_by_id(self, task_id):
        """wait a task util it becomes stable.

        :param task_id: indicates id of task
        :return: stable task
        """
        task = self.get(task_id)
        return self.wait_task(task)

    def wait_task(self, task):
        """wait a task util it becomes stable.

        :param task: task it self
        :return: stable task
        """
        LOG.info("Wait task util processed, task: %s.", task)
        while True:
            if task.state in constants.TASK_STATUS_PROCESSING:
                LOG.info("%s is still processing, will reload %d seconds "
                         "later.", task, self.RECHECK_TASK_DELAY_IN_SECONDS)
                sleep(self.RECHECK_TASK_DELAY_IN_SECONDS)
                task = self.get(task.id)
            elif task.state in constants.TASK_STATUS_PROCESSED:
                LOG.info("%s has been processed.", task)
                return task
