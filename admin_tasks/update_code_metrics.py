#!/usr/bin/env python3
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


import src.common.constants as const


metrics_table = const.CodeMetricsTable()


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
        self.abort_if_already_in_ddb()
        self.git_revision = None
        self.loc = None
        self.comments = None
        self.blank = None
        self.details = None
        self.sum_dict = None

        self.get_master_revision_at_timestamp()
        self.count_lines_of_code_for_revision()
        self.upload_metrics_to_ddb()

    def abort_if_already_in_ddb(self):
        r = metrics_table.exact_query(
            partition_value=self.stack_name, sort_value=self.commit_timestamp
        )
        if r["Count"]:
            raise subprocess.CalledProcessError(500, "None")  # hack

    def get_master_revision_at_timestamp(self):
        def get_revision():
            return subprocess.run(
                [
                    "git",
                    "rev-list",
                    "-1",
                    "--before",
                    f"{self.commit_timestamp}",
                    "origin/master",
                ],
                capture_output=True,
                check=True,
                text=True,
            ).stdout.strip()

        try:
            self.git_revision = get_revision()
        except subprocess.CalledProcessError:
            subprocess.run(["git", "fetch"])
            self.git_revision = get_revision()

    def count_lines_of_code_for_revision(self):
        """
        Uses the cloc command line tool (https://github.com/AlDanial/cloc)
        """
        cloc_json_report = subprocess.run(
            [
                "cloc",
                "--exclude-dir=vendors,public",
                "--exclude-ext=sty",
                "--json",
                "--git",
                self.git_revision,
            ],
            capture_output=True,
            check=True,
            text=True,
        ).stdout.strip()
        self.details = json.loads(cloc_json_report)
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


def get_revision_of_earliest_commit():
    return subprocess.run(
        [
            "git",
            "rev-list",
            "--max-parents=0",
            "origin/master",
        ],
        capture_output=True,
        check=True,
        text=True,
    ).stdout.strip()


def datetime_of_earliest_repo_commit():
    return subprocess.run(
        [
            "git",
            "show",
            "-s",
            "--format=%ci",
            get_revision_of_earliest_commit(),
        ],
        capture_output=True,
        check=True,
        text=True,
    ).stdout.strip()


def main():
    pwd = os.getcwd()

    # store date of earliest commit for each repo
    earliest_commits = dict()
    for r in REPOS:
        os.chdir(os.path.join(GITHUB_FOLDER, r))
        dt = datetime_of_earliest_repo_commit()
        date_earliest_commit = dt.split()[0]
        earliest_commits[r] = parser.parse(date_earliest_commit)

    # compute data points
    thiscovery_loc_data_series = list()  # locs per timestamp
    stack_data_series = dict()  # locs per timestamp in a dict keyed by stack
    timestamps = list()

    ts = COMMIT_TIMESTAMPS[0]
    ts_end = COMMIT_TIMESTAMPS[1]

    while ts != ts_end:
        ts_str = str(ts.date())
        print(f"Working on {ts_str}")
        thiscovery_loc_data_point = 0
        for r in REPOS:
            if ts < earliest_commits[r]:
                continue

            os.chdir(os.path.join(GITHUB_FOLDER, r))
            try:
                counter = StackLocCounter(stack_name=r, commit_timestamp=ts_str)
            except subprocess.CalledProcessError:
                stack_data_point = 0
            else:
                stack_data_point = counter.loc

            try:
                stack_data_series[r].append(stack_data_point)
            except KeyError:
                stack_data_series[r] = [stack_data_point]

            # add stack loc to thiscovery total
            thiscovery_loc_data_point += stack_data_point

        # add timestamp total to thiscovery series
        thiscovery_loc_data_series.append(thiscovery_loc_data_point)
        ts = ts + TIMESTAMP_DELTA

    # generate graph of thiscovery totals
    os.chdir(pwd)
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
    main()
