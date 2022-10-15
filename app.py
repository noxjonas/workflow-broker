#!/usr/bin/env python3
import os

import aws_cdk as cdk

from deploy.app_stack import BrokerStack
from api.infrastructure.chaliceapp import ChaliceApp
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
    queue=broker.get_queue("DummyWorkflowQueue"),
    env=cdk.Environment(
        account=os.getenv("CDK_DEFAULT_ACCOUNT"), region=os.getenv("CDK_DEFAULT_REGION")
    ),
)


ChaliceApp(
    app,
    "api",
    broker_table=broker.table,
    broker_bucket=broker.bucket,
    broker_queues=broker.queues,
    env=cdk.Environment(
        account=os.getenv("CDK_DEFAULT_ACCOUNT"), region=os.getenv("CDK_DEFAULT_REGION")
    ),
)

app.synth()
