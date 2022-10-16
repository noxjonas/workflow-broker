#!/usr/bin/env python3
import os

import aws_cdk as cdk

from deploy.app_stack import BrokerStack
import json

from deploy.dummy_workflow import DummyWorkflow

DEPLOYMENT_ENV = os.getenv("DEPLOYMENT_ENV", "dev")
with open("cdk.json") as fp:
    STAGE_CONFIG = json.load(fp)["context"][DEPLOYMENT_ENV]

app = cdk.App(context={"CONFIG": STAGE_CONFIG})


broker = BrokerStack(
    app,
    "WorkflowBroker",
    env=cdk.Environment(
        account=os.getenv("CDK_DEFAULT_ACCOUNT"), region=os.getenv("CDK_DEFAULT_REGION")
    ),
)

DummyWorkflow(
    app,
    "DummyWorkflow",
    queue=broker.get_queue(workflow_name="DummyWorkflow"),
    env=cdk.Environment(
        account=os.getenv("CDK_DEFAULT_ACCOUNT"), region=os.getenv("CDK_DEFAULT_REGION")
    ),
)

# does nothing atm. api will have to be aware of the queues available
#   put into table/ ssm parameter? but how will the app be aware of deleted queue? cross-check with SQS?
broker.register_workflows()

app.synth()
