from aws_cdk import (
    Duration,
    Stack,
    aws_lambda as _lambda,
    aws_sqs as sqs,
    aws_apigateway as apigw,
    aws_stepfunctions as sfn,
    aws_stepfunctions_tasks as tasks,
    aws_iam as iam
)
import aws_cdk as cdk
from constructs import Construct


class AppStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # The code that defines your stack goes here

        # # example resource
        # queue = sqs.Queue(
        #     self, "DeployQueue",
        #     visibility_timeout=Duration.seconds(300),
        # )

        # Defines an AWS Lambda resource
        my_lambda = _lambda.Function(
            self, 'MyLambda',
            runtime=_lambda.Runtime.PYTHON_3_9,
            code=_lambda.Code.from_asset('core'),
            handler='handlers.hello',
        )

        pre_run_hook_lambda = _lambda.Function(
            self, 'PreRunHookLambda',
            runtime=_lambda.Runtime.PYTHON_3_9,
            code=_lambda.Code.from_asset('core'),
            handler='pre_run_hook.handler',
        )

        execute_job_lambda = _lambda.Function(
            self, 'ExecuteJobLambda',
            runtime=_lambda.Runtime.PYTHON_3_9,
            code=_lambda.Code.from_asset('core'),
            handler='handlers.execute_job',
        )

        execute_job_lambda.add_to_role_policy(iam.PolicyStatement(
            effect=iam.Effect.ALLOW,
            actions=[
                'lambda:InvokeFunction',
            ],
            resources=[
                'arn:aws:lambda:eu-central-1:852354451651:function:calc-sum-lambda',
            ],
        ))

        state_machine = sfn.StateMachine(
            self, "WorkflowBrokerStateMachine",
            definition=sfn.Chain
            .start(
                tasks.LambdaInvoke(
                    self, "MyLambdaTask",
                    lambda_function=my_lambda
                )
            )
            .next(
                sfn.Wait(self, "random wait 1s", time=sfn.WaitTime.duration(cdk.Duration.seconds(1)))
            )
            .next(
                tasks.LambdaInvoke(
                    self, "PreRunTask",
                    lambda_function=pre_run_hook_lambda,
                    input_path="$.Payload",
                )
            ).next(
                tasks.LambdaInvoke(
                    self, "RunTask",
                    lambda_function=execute_job_lambda,
                    input_path="$.Payload",
                )
            )
            .next(
                sfn.Succeed(self, "GreetedWorld")
            )
        )

