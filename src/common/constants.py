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
from thiscovery_lib.dynamodb_utilities import DdbBaseTable


STACK_NAME = "thiscovery-devops"


class DeploymentsTable(DdbBaseTable):
    name = "Deployments"
    partition = "stack_env"
    sort = "modified"

    def __init__(self, correlation_id=None):
        super().__init__(stack_name=STACK_NAME, correlation_id=correlation_id)


class CodeMetricsTable(DdbBaseTable):
    name = "CodeMetrics"
    partition = "repo"
    sort = "timestamp"

    def __init__(self, correlation_id=None):
        super().__init__(stack_name=STACK_NAME, correlation_id=correlation_id)
        self.table = self._ddb_client.get_table(self.name)

    def exact_query(self, partition_value, sort_value):
        return self.table.query(
            KeyConditionExpression=f"{self.partition} = :{self.partition} "
            f"AND #ts = :{self.sort}",
            ExpressionAttributeNames={
                "#ts": self.sort,
            },
            ExpressionAttributeValues={
                f":{self.partition}": partition_value,
                f":{self.sort}": sort_value,
            },
        )
