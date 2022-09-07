#!/usr/bin/env python3
import os

import aws_cdk as cdk

from deploy.app_stack import AppStack
from api.infrastructure.stacks.chaliceapp import ChaliceApp
import json

DEPLOYMENT_ENV = os.getenv('DEPLOYMENT_ENV', 'dev')
with open('cdk.json') as fp:
    STAGE_CONFIG = json.load(fp)['context'][DEPLOYMENT_ENV]

app = cdk.App(context={
    "CONFIG": STAGE_CONFIG
})

ChaliceApp(app, 'api', env=cdk.Environment(account=os.getenv('CDK_DEFAULT_ACCOUNT'), region=os.getenv('CDK_DEFAULT_REGION')),)

AppStack(
    app,
    "WorkflowBroker",
    env=cdk.Environment(account=os.getenv('CDK_DEFAULT_ACCOUNT'), region=os.getenv('CDK_DEFAULT_REGION')),
)

app.synth()
