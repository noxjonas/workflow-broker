from aws_cdk import (
    Stack,
    aws_lambda as _lambda,
    aws_logs as logs,
    aws_lambda_event_sources as lambda_event_sources,
)
from constructs import Construct


class DummyWorkflow(Stack):
    def __init__(self, scope: Construct, construct_id: str, *, queue, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        sqs_event = lambda_event_sources.SqsEventSource(queue)

        dummy_workflow_lambda = _lambda.Function(
            self,
            "DummyWorkflowLambda",
            runtime=_lambda.Runtime.PYTHON_3_9,
            code=_lambda.Code.from_asset("lambdas"),
            handler="handlers.dummy_workflow",
            log_retention=logs.RetentionDays.THREE_DAYS,
        )
        dummy_workflow_lambda.add_event_source(sqs_event)
