#!/usr/bin/env python3
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
"""
This script queries a source thiscovery environment for the git revisions of deployed
stacks and then deploy those revisions to a target thiscovery environment.
You can use it to mirror the production environment in your dev/test environments to
carry out integration testing.
"""
import local.secrets
from local.dev_config import (
    GITHUB_FOLDER,
    SOURCE_ENV,
    TARGET_ENV,
    REPOS,
)
import os
import sys
from thiscovery_dev_tools.aws_deployer import AwsDeployer

import admin_tasks.common.git_utilities as git_utils
from admin_tasks.services_deployment_status import StackDeploymentStatus


# IMPORTANT! Ensures all deployments can only be made to TARGET_ENV
os.environ["SECRETS_NAMESPACE"] = f"/{TARGET_ENV}/"
if os.environ["SECRETS_NAMESPACE"] in ["/prod/", "/staging/"]:
    confirm = input(f'Are you sure you want to sync {os.environ["SECRETS_NAMESPACE"]} to {SOURCE_ENV}? (y/N)')
    if confirm.lower() != "y":
        print("Aborted")
        sys.exit(1)


class EnvSyncer:
    def __init__(self, stack_name):
        self.stack_name = stack_name
        self.source_sds = StackDeploymentStatus(stack_name=stack_name, env_name=SOURCE_ENV)
        self.target_sds = StackDeploymentStatus(stack_name=stack_name, env_name=TARGET_ENV)

    def deploy_source_rev_to_target_env(self):
        os.chdir(os.path.join(GITHUB_FOLDER, self.stack_name))
        git_utils.checkout_revision(revision=self.source_sds.deployed_revision)
        deployer = AwsDeployer(stack_name=self.stack_name)
        print(f"\nInitiating deployment of {self.stack_name} to {TARGET_ENV}")
        deployer.main(skip_confirmation=True)

    def main(self):
        self.source_sds.get_deployment_history()
        self.target_sds.get_deployment_history()
        if self.source_sds.deployed_revision != self.target_sds.deployed_revision:
            self.deploy_source_rev_to_target_env()
        else:
            print(f"\nStack {self.stack_name} is already in sync in {SOURCE_ENV} and {TARGET_ENV}; skipped")


if __name__ == "__main__":
    for r in REPOS:
        repo_env_syncer = EnvSyncer(stack_name=r)
        repo_env_syncer.main()
