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
import thiscovery_lib.utilities as utils
from thiscovery_lib.dynamodb_utilities import DdbBaseItem

import common.constants as const


class Deployment(DdbBaseItem):
    def __init__(self, event):
        self._logger = event.pop("logger", utils.get_logger())
        self._correlation_id = event["id"]
        event_detail = event["detail"]
        self.stack = event_detail["stack"]
        self.environment = event_detail["environment"]
        self.stack_env = f"{self.stack}-{self.environment}"
        self.timestamp = event["time"]
        self.source = event.get("source")
        super().__init__(
            table=const.DeploymentsTable(correlation_id=self._correlation_id)
        )


@utils.lambda_wrapper
def add_deployment(event, context):
    deployment = Deployment(event)
    return deployment.put()
