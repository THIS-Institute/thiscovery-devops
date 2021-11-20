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
import os
import subprocess
from dateutil import parser


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


def date_earliest_commit_dict(project_folder, repositories):
    pwd = os.getcwd()
    earliest_commits = dict()
    for r in repositories:
        os.chdir(os.path.join(project_folder, r))
        dt = datetime_of_earliest_repo_commit()
        date_earliest_commit = dt.split()[0]
        earliest_commits[r] = parser.parse(date_earliest_commit)
    os.chdir(pwd)
    return earliest_commits


def get_branch_revision_at_timestamp(date_str, branch):
    def get_revision():
        return subprocess.run(
            [
                "git",
                "rev-list",
                "-1",
                "--before",
                date_str,
                branch,
            ],
            capture_output=True,
            check=True,
            text=True,
        ).stdout.strip()

    try:
        git_revision = get_revision()
    except subprocess.CalledProcessError:
        subprocess.run(["git", "fetch"])
        git_revision = get_revision()
    return git_revision


def count_lines_of_code_for_revision(revision):
    """
    Uses the cloc command line tool (https://github.com/AlDanial/cloc)
    """
    return subprocess.run(
        [
            "cloc",
            "--exclude-dir=vendors,public",
            "--exclude-ext=sty",
            "--json",
            "--git",
            revision,
        ],
        capture_output=True,
        check=True,
        text=True,
    ).stdout.strip()