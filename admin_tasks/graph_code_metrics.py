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
import json
import os
import re
import subprocess
import thiscovery_lib.utilities as utils
from dateutil import parser
from highcharts import Highchart
from pprint import pprint
from thiscovery_lib.dynamodb_utilities import DdbBaseItem, Dynamodb

import admin_tasks.common.git_utilities as git_utils
import src.common.constants as const

from admin_tasks.common.code_metrics_utilities import StackLocCounter


# init globals
metrics_table = const.CodeMetricsTable()
thiscovery_loc_data_series = list()  # locs per timestamp
stack_data_series = dict()  # locs per timestamp in a dict keyed by stack
timestamps = list()


def append_stack_data_point(stack_name, data_point):
    global stack_data_series
    try:
        stack_data_series[stack_name].append(data_point)
    except KeyError:
        stack_data_series[stack_name] = [data_point]


def compute_graph_series():
    pwd = os.getcwd()
    earliest_commits = git_utils.date_earliest_commit_dict(GITHUB_FOLDER, REPOS)
    ts = COMMIT_TIMESTAMPS[0]
    ts_end = COMMIT_TIMESTAMPS[1]

    while ts != ts_end:
        ts_str = str(ts.date())
        print(f"Working on {ts_str}")
        timestamps.append(ts_str)
        thiscovery_loc_data_point = 0
        for r in REPOS:
            if ts < earliest_commits[r]:
                append_stack_data_point(r, 0)
            else:
                os.chdir(os.path.join(GITHUB_FOLDER, r))
                counter = StackLocCounter(stack_name=r, commit_timestamp=ts_str)
                try:
                    counter.compute_metrics()
                except subprocess.CalledProcessError:
                    stack_data_point = 0
                else:
                    stack_data_point = counter.loc
                append_stack_data_point(r, stack_data_point)

                # add stack loc to thiscovery total
                thiscovery_loc_data_point += stack_data_point

        # add timestamp total to thiscovery series
        thiscovery_loc_data_series.append(thiscovery_loc_data_point)
        ts = ts + TIMESTAMP_DELTA
    os.chdir(pwd)


def save_globals_to_file(output_filename):
    data = {
        "timestamps": timestamps,
        "thiscovery_total": thiscovery_loc_data_series,
        "services": stack_data_series,
    }
    with open(output_filename, "w") as output:
        output.write(json.dumps(data))


def load_globals_from_file(input_filename):
    global timestamps
    global thiscovery_loc_data_series
    global stack_data_series
    with open(input_filename) as input_file:
        data = json.loads(input_file.read())
        timestamps = data["timestamps"]
        thiscovery_loc_data_series = data["thiscovery_total"]
        stack_data_series = data["services"]


def main():
    # generate graph of thiscovery totals
    chart = Highchart()
    options = {
        "title": {"text": "Thiscovery lines of code"},
        "subtitle": {"text": "Excludes comments and blank lines"},
        "xAxis": {
            "reversed": False,
            "title": {"enabled": True, "text": "Date"},
            "maxPadding": 0.05,
            "showLastLabel": True,
        },
        "yAxis": {
            "title": {"text": "Lines of code"},
            "lineWidth": 2,
        },
        "legend": {"enabled": False},
        "tooltip": {
            "pointFormat": "{point.y}",
        },
    }
    chart.set_dict_options(options=options)
    chart.add_data_set(thiscovery_loc_data_series, "bar")
    chart.save_file("thiscovery")

    # generate repo graph
    chart = Highchart()
    repo_options = {
        **options,
        "title": {"text": "Thiscovery lines of code per service"},
    }
    chart.set_dict_options(options=options)
    for r in REPOS:
        repo_data = stack_data_series[r]
        chart.add_data_set(repo_data, "bar")
    chart.save_file("thiscovery_services")


if __name__ == "__main__":
    compute_graph_series()
    save_globals_to_file("code_metrics.json")
    # load_globals_from_file("code_metrics.json")
    main()
