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
import local.secrets
from local.dev_config import (
    GITHUB_FOLDER,
    REPOS,
    COMMIT_TIMESTAMPS,
    TIMESTAMP_DELTA,
)
import os
import subprocess
import admin_tasks.common.git_utilities as git_utils
import src.common.constants as const

from admin_tasks.common.code_metrics_utilities import StackLocCounter


metrics_table = const.CodeMetricsTable()


def main():
    earliest_commits = git_utils.date_earliest_commit_dict(GITHUB_FOLDER, REPOS)
    ts = COMMIT_TIMESTAMPS[0]
    ts_end = COMMIT_TIMESTAMPS[1]

    while ts != ts_end:
        ts_str = str(ts.date())
        print(f"Working on {ts_str}")
        for r in REPOS:
            if ts < earliest_commits[r]:
                continue

            os.chdir(os.path.join(GITHUB_FOLDER, r))
            counter = StackLocCounter(stack_name=r, commit_timestamp=ts_str)
            try:
                counter.populate_ddb(metrics_table)
            except subprocess.CalledProcessError:
                pass
        ts = ts + TIMESTAMP_DELTA


if __name__ == "__main__":
    main()
