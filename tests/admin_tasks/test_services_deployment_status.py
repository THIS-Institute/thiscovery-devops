#
#   Thiscovery API - THIS Institute’s citizen science platform
#   Copyright (C) 2019 THIS Institute
#
#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU Affero General Public License as
#   published by the Free Software Foundation, either version 3 of the
#   License, or (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU Affero General Public License for more details.
#
#   A copy of the GNU Affero General Public License is available in the
#   docs folder of this project.  It is also available www.gnu.org/licenses/
#
import local.dev_config as conf  # sets env variable 'TEST_ON_AWS'
import local.secrets  # sets AWS profile as env variable
import json
import os
import unittest
import requests
import thiscovery_dev_tools.testing_tools as test_tools
from pprint import pprint

from src.common.constants import STACK_NAME
from thiscovery_lib.lambda_utilities import Lambda
from admin_tasks.services_deployment_status import StackDeploymentStatus


class StackDeploymentStatusTestCase(test_tools.BaseTestCase):
    def test_get_deployment_history_ok(self):
        sds = StackDeploymentStatus(
            stack_name=STACK_NAME, env_name=conf.UNIT_TEST_NAMESPACE[1:-1]
        )
        deployment_history = sds.get_deployment_history()
        self.assertTrue(deployment_history)
        most_recent_deployment = sds.deployment_history[0]
        keys = most_recent_deployment.keys()
        self.assertIn("branch", keys)
        self.assertIn("revision", keys)
        self.assertEqual(most_recent_deployment["revision"], sds.deployed_revision)
