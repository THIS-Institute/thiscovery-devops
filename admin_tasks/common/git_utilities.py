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
import functools
import os
import subprocess
from dateutil import parser


class DetailedCalledProcessError(subprocess.CalledProcessError):
    def __init__(self, called_process_error):
        self.err_message = f"{called_process_error.__str__()}\n" \
                           f"Standard error output:\n" \
                           f"{called_process_error.stderr}"

    def __str__(self):
        return self.err_message


def detailed_subprocess_error(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except subprocess.CalledProcessError as called_process_error:
            detailed_error = DetailedCalledProcessError(called_process_error)
            raise detailed_error

    return wrapper


@detailed_subprocess_error
def get_commit_delta_to_branch(revision, branch="origin/master"):
    def get_delta():
        return subprocess.run(
            [
                "git",
                "rev-list",
                "--left-right",
                "--count",
                f"{branch}...{revision}",
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
    return behind, ahead


@detailed_subprocess_error
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


@detailed_subprocess_error
def checkout_master():
    return subprocess.run(
        ["git", "checkout", "master"],
        capture_output=True,
        check=True,
        text=True,
    ).stdout.strip()


@detailed_subprocess_error
def checkout_revision(revision: str, branch_name=None):
    cmd = ["git", "checkout", revision]
    if branch_name:
        cmd += ["-b", branch_name]
    return subprocess.run(
        cmd,
        capture_output=True,
        check=True,
        text=True,
    ).stdout.strip()


@detailed_subprocess_error
def pull():
    return subprocess.run(
        ["git", "pull"],
        capture_output=True,
        check=True,
        text=True,
    ).stdout.strip()


@detailed_subprocess_error
def datetime_of_git_revision(revision):
    return subprocess.run(
        [
            "git",
            "show",
            "-s",
            "--format=%ci",
            revision,
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
        dt = datetime_of_git_revision(get_revision_of_earliest_commit())
        date_earliest_commit = dt.split()[0]
        earliest_commits[r] = parser.parse(date_earliest_commit)
    os.chdir(pwd)
    return earliest_commits


@detailed_subprocess_error
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


@detailed_subprocess_error
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
