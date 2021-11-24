#!/usr/bin/env python3
import local.secrets
from local.dev_config import GITHUB_FOLDER, SECRETS_NAMESPACE, ENVS, REPOS
import os
import subprocess
import thiscovery_lib.utilities as utils
from prettytable import PrettyTable

from src.common.constants import DeploymentsTable


repos_table = PrettyTable()
repos_table.field_names = [
    "Environment",
    "Stack",
    "Commits behind",
    "Commits ahead",
    "Deployed revision",
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

    def get_deployment_history(self):
        deployments_table = DeploymentsTable(
            profile_name=utils.namespace2profile(utils.name2namespace(self.env_name)),
            aws_namespace=self.env_name,  # force Dynamodb client to use this instead of the SECRETS_NAMESPACE config
        )
        self.deployment_history = deployments_table.query_recent_deployments(
            stack_env=f"{self.stack_name}-{self.env_name}"
        )["Items"]
        try:
            self.deployed_revision = self.deployment_history[0]["revision"]
        except IndexError:
            raise utils.ObjectDoesNotExistError(
                f"No deployment found for stack {self.stack_name} in environment {self.env_name}",
                details={},
            )
        return self.deployment_history

    def get_commit_delta_to_master(self):
        def get_delta():
            return subprocess.run(
                [
                    "git",
                    "rev-list",
                    "--left-right",
                    "--count",
                    f"origin/master...{self.deployed_revision}",
                ],
                capture_output=True,
                check=True,
                text=True,
            ).stdout.strip()

        try:
            delta = get_delta()
        except subprocess.CalledProcessError:
            subprocess.run(["git", "fetch"])
            delta = get_delta()
        behind, ahead = delta.split("\t")
        self.deployed_revision_behind = behind
        self.deployed_revision_ahead = ahead
        return behind, ahead

    def append_stack_report_to_repos_table(self):
        repos_table.add_row(
            [
                self.env_name,
                self.stack_name,
                self.deployed_revision_behind,
                self.deployed_revision_ahead,
                self.deployed_revision,
            ]
        )


def main():
    for e in ENVS:
        for r in REPOS:
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
                sds.get_commit_delta_to_master()
            sds.append_stack_report_to_repos_table()
    print("\nStack deployment status compared to origin/master:")
    print(repos_table)


if __name__ == "__main__":
    main()
