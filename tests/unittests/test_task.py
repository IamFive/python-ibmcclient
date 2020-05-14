# coding: utf-8
import unittest
from mock.mock import patch

import responses

import ibmc_client
from ibmc_client.constants import GET
from ibmc_client.exceptions import TaskFailed
from ibmc_client.resources.task import Task
from tests.unittests import BaseUnittest


class TestTaskClient(BaseUnittest):
    """ iBMC task client unit test stubs """

    @responses.activate
    def testGetInitialTask(self):
        get_task_url = ('https://server1.ibmc.com/redfish/v1/TaskService'
                        '/Tasks/1')
        response_list = [
            responses.Response(method=GET, url=get_task_url,
                               json=self.load_json_file(
                                   'get-initial-task-response.json'))
        ]

        self.start_mocked_http_server(response_list)
        with ibmc_client.connect(**self.server) as client:
            task = client.task.get('1')
            self.assertEqual(task.id, '1')
            self.assertEqual(task.name, 'mock task')
            self.assertEqual(task.state, 'Running')
            self.assertEqual(task.start_time, '2020-04-28T08:17:41+08:00')
            self.assertIsNone(task.end_time)
            self.assertIsNone(task.percentage)
            self.assertEqual(task.messages, {})
            self.assertIsNone(task.message_id)
            self.assertIsNone(task.message)
            self.assertIsNone(task.message_args)
            self.assertIsNone(task.resolution)
            self.assertIsNone(task.severity)

    @responses.activate
    def testGetCompleteTask(self):
        get_task_url = ('https://server1.ibmc.com/redfish/v1/TaskService'
                        '/Tasks/4')
        task_json = self.load_json_file('get-complete-task-response.json')
        response_list = [
            responses.Response(method=GET, url=get_task_url,
                               json=task_json)
        ]

        self.start_mocked_http_server(response_list)
        with ibmc_client.connect(**self.server) as client:
            task = client.task.get('4')
            self.assertEqual(task.id, '4')
            self.assertEqual(task.name, 'volume creation task')
            self.assertEqual(task.state, 'Completed')
            self.assertEqual(task.start_time, '2020-04-28T10:50:12+08:00')
            self.assertEqual(task.end_time, '2020-04-28T10:50:17+08:00')
            self.assertIsNone(task.percentage)
            messages = task_json.get('Messages')
            self.assertEqual(task.messages, messages)
            self.assertEqual(task.message_id, 'iBMC.1.0.VolumeCreationSuccess')
            self.assertEqual(task.message, messages['Message'])
            self.assertEqual(task.message_args, messages['MessageArgs'])
            self.assertEqual(task.resolution, messages['Resolution'])
            self.assertEqual(task.severity, messages['Severity'])

    @responses.activate
    @patch('ibmc_client.api.task.task.sleep', return_value=None)
    def testWaitTask(self, patched_time_sleep):
        resp_list = [responses.Response(
            method=GET,
            url='https://server1.ibmc.com/redfish/v1/TaskService/Tasks/1',
            json=self.load_json_file('delete-volume-task-response.json')
        )] * 10

        resp_list.append(responses.Response(
            method=GET,
            url='https://server1.ibmc.com/redfish/v1/TaskService/Tasks/1',
            json=self.load_json_file(
                'delete-volume-task-finished-response.json')
        ))

        self.start_mocked_http_server(resp_list)
        with ibmc_client.connect(**self.server) as client:
            task = client.task.wait_task_by_id('1')
            self.assertEqual(patched_time_sleep.call_count, 10)
            self.assertEqual(task.state, 'Completed')

    def testRaiseIfFailed(self):
        resp = self.new_mocked_response(
            'create-volume-task-exception-response.json')
        task = Task(resp)
        try:
            task.raise_if_failed()
        except TaskFailed as e:
            self.assertEqual(
                e.message,
                ("[Warning] Task(volume creation task)'s final state is "
                 "Exception. Reason:: 'The value [0, 0] of the property "
                 "Oem/Huawei/Drives is invalid because the drive ID list "
                 "contains invalid drive ID.' "
                 "Resolution:: 'Try again using a valid value.'"))


if __name__ == '__main__':
    unittest.main()
