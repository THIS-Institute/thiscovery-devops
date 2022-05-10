#!/usr/bin/env python3
import local.secrets
from local.dev_config import (
    GITHUB_FOLDER,
    SECRETS_NAMESPACE,
    ENVS,
    REPOS,
    DEPLOYMENT_HISTORY_GROUPING,
)
import os
import subprocess
import thiscovery_lib.utilities as utils
from prettytable import PrettyTable

import admin_tasks.common.git_utilities as git_utils
from src.common.constants import DeploymentsTable


ERROR_STR = "Error"

repos_table = PrettyTable()
if DEPLOYMENT_HISTORY_GROUPING == "stack":
    stack_env_columns = [
        "Stack",
        "Env",
    ]
else:
    stack_env_columns = [
        "Env",
        "Stack",
    ]

repos_table.field_names = [
    *stack_env_columns,
    "Behind",
    "Ahead",
    "Deployed rev",
    "Revision datetime",
    "thiscovery-lib rev",
    "Epsagon",
    "Deployment datetime",
]


class StackDeploymentStatus:
    def __init__(self, stack_name, env_name=None):
        self.stack_name = stack_name
        self.env_name = env_name
        if env_name is None:
            self.env_name = SECRETS_NAMESPACE[1:-1]

        self.deployment_history = None
        self.deployed_revision = None
        self.deployed_revision_behind = None
        self.deployed_revision_ahead = None
        self.deployed_revision_datetime = None
        self.deployment_datetime = None
        self.epsagon_layer = None
        self.thiscovery_lib_rev = None
        self.latest_deployment = None
        self.logger = utils.get_logger()

    def get_deployment_history(self):
        deployments_table = DeploymentsTable(
            profile_name=utils.namespace2profile(utils.name2namespace(self.env_name)),
            aws_namespace=self.env_name,  # force Dynamodb client to use this instead of the SECRETS_NAMESPACE config
        )
        self.deployment_history = deployments_table.query_recent_deployments(
            stack_env=f"{self.stack_name}-{self.env_name}"
        )["Items"]
        try:
            self.latest_deployment = self.deployment_history[0]
        except IndexError:
            raise utils.ObjectDoesNotExistError(
                f"No deployment found for stack {self.stack_name} in environment {self.env_name}",
                details={},
            )
        self.deployed_revision = self.latest_deployment["revision"][:8]
        self.deployment_datetime = self.latest_deployment["created"]
        self.epsagon_layer = self.latest_deployment.get("epsagon_layer_version", "NA")
        self.thiscovery_lib_rev = self.latest_deployment.get(
            "thiscovery_lib_revision", "NA"
        )[:8]
        return self.deployment_history

    def get_deployed_revision_delta_to_master(self):
        try:
            (
                self.deployed_revision_behind,
                self.deployed_revision_ahead,
            ) = git_utils.get_commit_delta_to_branch(self.deployed_revision)
        except git_utils.DetailedCalledProcessError as err:
            self.logger.error(err, extra={})
            self.deployed_revision_behind = ERROR_STR
            self.deployed_revision_ahead = ERROR_STR

    def get_deployed_revision_datetime(self):
        git_utils.checkout_master()
        git_utils.pull()
        try:
            self.deployed_revision_datetime = git_utils.datetime_of_git_revision(
                self.deployed_revision
            )
        except git_utils.DetailedCalledProcessError as err:
            self.logger.error(err, extra={})
            self.deployed_revision_datetime = ERROR_STR

    def append_stack_report_to_repos_table(self):
        try:
            deployed_revision_datetime = self.deployed_revision_datetime[0:19]
            deployment_datetime = self.deployment_datetime[0:19]
        except TypeError:
            deployed_revision_datetime = "NA"
            deployment_datetime = "NA"
        if DEPLOYMENT_HISTORY_GROUPING == "stack":
            env_stack_order = [
                self.stack_name,
                self.env_name,
            ]
        else:
            env_stack_order = [
                self.env_name,
                self.stack_name,
            ]
        repos_table.add_row(
            [
                *env_stack_order,
                self.deployed_revision_behind,
                self.deployed_revision_ahead,
                self.deployed_revision,
                deployed_revision_datetime,
                self.thiscovery_lib_rev,
                self.epsagon_layer,
                deployment_datetime,
            ]
        )


def main(r, e):
    print(f"Working on {r} {e}")
    os.chdir(os.path.join(GITHUB_FOLDER, r))
    sds = StackDeploymentStatus(stack_name=r, env_name=e)
    try:
        sds.get_deployment_history()
    except utils.ObjectDoesNotExistError:
        sds.deployed_revision_behind = "NA"
        sds.deployed_revision_ahead = "NA"
        sds.deployed_revision = "NA"
    else:
        sds.get_deployed_revision_datetime()
        sds.get_deployed_revision_delta_to_master()
    sds.append_stack_report_to_repos_table()


if __name__ == "__main__":
    if DEPLOYMENT_HISTORY_GROUPING == "stack":
        for r in REPOS:
            for e in ENVS:
                main(r, e)
    else:
        for e in ENVS:
            for r in REPOS:
                main(r, e)
    print("\nStack deployment status compared to origin/master:")
    print(repos_table)
