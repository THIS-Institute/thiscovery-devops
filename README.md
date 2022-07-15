# thiscovery-devops

## Purpose
Provision of account-level resources related to application deployment.
Also contains resources and code to gather and plot information about
thiscovery's codebase.

## Usage
Deploy this stack to only one environment in each AWS account.

The script admin_tasks/services_deployment_status.py is
particularly useful when trying to determine and/or
compare what microservice versions are deployed to 
each environment.

## Responsibilities 

### Data storage
1. Dynamodb "Deployments" table
2. Dynamodb "CodeMetrics" table

### Processing
1. Stores a history of all deployments by processing deployment events posted by the thiscovery AWS deployer (defined in thiscovery-dev-tools)

## Interfaces
### Events raised
None
### Events consumed
| Bus                  | Source(s)               | Event(s)   | Description                     |
|----------------------|-------------------------|------------|---------------------------------|
| Thiscovery event bus | Thiscovery AWS deployer | Deployment | Stack deployment to AWS account | 
### API endpoints
None

## Future direction
At present, the Dynamodb "CodeMetrics" table is populated 
and updated by manually running script update_code_metrics.py
Data in that table can be used, for example, to visualise the
relative size of thiscovery microservices and how that changed
in time (https://thiscovery-public-assets.s3.eu-west-1.amazonaws.com/charts/thiscovery_services_ten_days_excluding_views.html).
If this kind of visualisation proves useful to be included in
an admin dashboard, then it would make sense to update the table
and produce summary data for the graphs on a regular basis
(that is, using an AWS Lambda function running on a timer)