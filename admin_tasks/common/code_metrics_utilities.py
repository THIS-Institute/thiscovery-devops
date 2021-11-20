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
import json
import subprocess
from thiscovery_lib.dynamodb_utilities import DdbBaseItem
import thiscovery_lib.utilities as utils

import admin_tasks.common.git_utilities as git_utils
import src.common.constants as const


class CodeMetricsItem(DdbBaseItem):
    def __init__(self, repo, timestamp, revision):
        self._logger = utils.get_logger()
        self.repo = repo
        self.timestamp = timestamp
        self.revision = revision
        super().__init__(table=const.CodeMetricsTable())


class StackLocCounter:
    def __init__(self, stack_name, commit_timestamp):
        self.commit_timestamp = commit_timestamp
        self.stack_name = stack_name
        self.git_revision = None
        self.loc = None
        self.comments = None
        self.blank = None
        self.details = None
        self.sum_dict = None

    def abort_if_already_in_ddb(self, metrics_table):
        r = metrics_table.exact_query(
            partition_value=self.stack_name, sort_value=self.commit_timestamp
        )
        if r["Count"]:
            raise subprocess.CalledProcessError(500, "None")  # hack

    def get_master_revision_at_timestamp(self):
        self.git_revision = git_utils.get_branch_revision_at_timestamp(
            self.commit_timestamp, "origin/master"
        )

    def get_metrics_for_revision(self):
        self.details = json.loads(
            git_utils.count_lines_of_code_for_revision(self.git_revision)
        )
        self.sum_dict = self.details["SUM"]
        self.loc = self.sum_dict["code"]
        self.comments = self.sum_dict["comment"]
        self.blank = self.sum_dict["blank"]

    def upload_metrics_to_ddb(self):
        ddb_item = CodeMetricsItem(
            repo=self.stack_name,
            timestamp=self.commit_timestamp,
            revision=self.git_revision,
        )
        self.details["header"]["cloc_version"] = str(
            self.details["header"]["cloc_version"]
        )
        del self.details["header"]["elapsed_seconds"]
        del self.details["header"]["files_per_second"]
        del self.details["header"]["lines_per_second"]

        ddb_item.from_dict(
            {
                **self.sum_dict,
                "detail": self.details,
                "source": "cloc",
            }
        )
        ddb_item.put(update=True)

    def populate_ddb(self, metrics_table):
        self.abort_if_already_in_ddb(metrics_table)
        self.get_master_revision_at_timestamp()
        self.get_metrics_for_revision()
        self.upload_metrics_to_ddb()

    def compute_metrics(self):
        self.get_master_revision_at_timestamp()
        self.get_metrics_for_revision()
