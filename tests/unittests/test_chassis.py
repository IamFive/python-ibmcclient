# coding: utf-8

import unittest

import responses

import ibmc_client
from ibmc_client.constants import GET
from tests.unittests import BaseUnittest


class TestChassisClient(BaseUnittest):
    """ iBMC chassis client unit test stubs """

    @responses.activate
    def testGetChassis(self):
        get_task_url = 'https://server1.ibmc.com/redfish/v1/Chassis/1'
        response_list = [
            responses.Response(method=GET, url=get_task_url,
                               json=self.load_json_file(
                                   'get-chassis-response.json'))
        ]

        drive_idx_list = list(range(0, 8)) + [40, 41]
        for idx in drive_idx_list:
            response_list.append(responses.Response(
                method=GET,
                url=('https://server1.ibmc.com/redfish/v1/Chassis/1/Drives/'
                     'HDDPlaneDisk%d' % idx),
                json=self.load_json_file('get-drive-%d.json' % idx)
            ))

        self.start_mocked_http_server(response_list)
        with ibmc_client.connect(**self.server) as client:
            chassis = client.chassis.get()
            self.assertEqual(len(chassis.drives), 10)


if __name__ == '__main__':
    unittest.main()
