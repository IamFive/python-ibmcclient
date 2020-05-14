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
from ibmc_client.constants import TASK_STATUS_FAILED
from ibmc_client.exceptions import TaskFailed
from ibmc_client.resources import BaseResource


class Task(BaseResource):
    """iBMC System storage controller Resource Model"""

    def raise_if_failed(self):
        if self.state in TASK_STATUS_FAILED:
            raise TaskFailed(message=self.friendly_failed_message)

    @property
    def id(self):
        """get task id

        :return: task id
        """
        return self._json.get('Id', None)

    @property
    def name(self):
        """get task name

        :return: task name
        """
        return self._json.get('Name', None)

    @property
    def state(self):
        """get task state

        :return: task state
        """
        return self._json.get('TaskState', None)

    @property
    def start_time(self):
        """get task start time

        :return: task start time
        """
        return self._json.get('StartTime', None)

    @property
    def end_time(self):
        """get task end time

        :return: task end time
        """
        return self._json.get('EndTime', None)

    @property
    def percentage(self):
        """get task progress percentage

        :return: task progress percentage
        """
        return self._oem.get('TaskPercentage', None)

    @property
    def messages(self):
        """get task progress result messages

        :return: task progress result messages default {} if empty
        """
        messages = self._json.get('Messages', {})
        # when messages is empty, ibmc will return [].
        # if type(messages) is list:
        #     return {}
        if type(messages) is dict:
            return messages
        return {}

    @property
    def message_id(self):
        """get task progress result message id

        :return: task progress result message id
        """
        return self.messages.get('MessageId', None)

    @property
    def message(self):
        """get task progress result message

        :return: task progress result message
        """
        return self.messages.get('Message', None)

    @property
    def message_args(self):
        """get task progress result message args

        :return: task progress result message args
        """
        return self.messages.get('MessageArgs', None)

    @property
    def resolution(self):
        """get task progress result resolution suggest

        :return: task progress result resolution suggest
        """
        return self.messages.get('Resolution', None)

    @property
    def severity(self):
        """get task progress result severity

        :return: task progress result severity
        """
        return self.messages.get('Severity', None)

    @property
    def friendly_failed_message(self):
        """get task progress failed description

        :return: task progress failed description
        """

        display = ("[%(severity)s] Task(%(name)s)'s final state is %(state)s. "
                   "Reason:: '%(message)s' Resolution:: '%(resolution)s'")
        return display % {'severity': self.severity, 'name': self.name,
                          'state': self.state, 'message': self.message,
                          'resolution': self.resolution}

    def to_str(self):
        """
        Returns the string representation of the model
        """
        return ("Task[id=%(id)s, Name=%(name)s, status=%(status)s, percent="
                "%(percentage)s], start-time=%(start_time)s]" %
                {'id': self.id, 'name': self.name, 'status': self.state,
                 'percentage': self.percentage, 'start_time': self.start_time})
