from aws_cdk import (
    Duration,
    Stack,
    aws_lambda as _lambda,
    aws_sqs as sqs,
    aws_apigateway as apigw,
    aws_stepfunctions as sfn,
    aws_stepfunctions_tasks as tasks,
    aws_iam as iam,
    aws_s3 as s3,
    aws_sns as sns,
    aws_s3_notifications as s3n,
    aws_dynamodb as dynamodb,
    aws_logs as logs,
    aws_sns_subscriptions as subscriptions,
    aws_lambda_event_sources as lambda_event_sources,
    aws_lambda_python_alpha as lambda_python,
)
import aws_cdk as cdk
from constructs import Construct
from deploy.api.infrastructure.chaliceapp import ChaliceApp


class BrokerStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        self.queues = []

        self.trigger_topic = sns.Topic(self, "TriggerTopic")

        self.bucket = s3.Bucket(
            self,
            "InputBucket",
            enforce_ssl=True,
            removal_policy=cdk.RemovalPolicy.DESTROY,
        )

        self.table = dynamodb.Table(
            self,
            "WorkflowTable",
            partition_key=dynamodb.Attribute(
                # submission_id?
                name="user_id#workflow_id",
                type=dynamodb.AttributeType.STRING,
            ),
            sort_key=dynamodb.Attribute(
                name="workflow#id", type=dynamodb.AttributeType.STRING
            ),
            time_to_live_attribute="ttl",
            replication_regions=[],
            billing_mode=dynamodb.BillingMode.PROVISIONED,
            removal_policy=cdk.RemovalPolicy.DESTROY,
        )

        self.table.auto_scale_write_capacity(
            min_capacity=1, max_capacity=2
        ).scale_on_utilization(target_utilization_percent=75)

        input_validator_lambda = lambda_python.PythonFunction(
            self,
            "InputValidatorLambda",
            entry="lambdas/",
            runtime=_lambda.Runtime.PYTHON_3_9,
            handler="handler",
            index="validator.py",
            environment={
                "WORKFLOW_TABLE": self.table.table_name,
                "LOG_LEVEL": "INFO",
            },
            log_retention=logs.RetentionDays.THREE_DAYS,
        )

        self.table.grant_write_data(input_validator_lambda)

        self.bucket.add_event_notification(
            s3.EventType.OBJECT_CREATED,
            s3n.LambdaDestination(input_validator_lambda)
            # could add filters here
        )
        self.bucket.grant_read(input_validator_lambda)

        publish_to_sns_lambda = _lambda.Function(
            self,
            "PublishToSnsLambda",
            runtime=_lambda.Runtime.PYTHON_3_9,
            code=_lambda.Code.from_asset("lambdas"),
            handler="publisher.handler",
            environment={
                "SNS_TOPIC_ARN": self.trigger_topic.topic_arn,
                "LOG_LEVEL": "INFO",
            },
            log_retention=logs.RetentionDays.THREE_DAYS,
        )
        publish_to_sns_lambda.add_event_source(
            lambda_event_sources.DynamoEventSource(
                self.table,
                starting_position=_lambda.StartingPosition.TRIM_HORIZON,
                batch_size=5,
                bisect_batch_on_error=True,
                filters=[
                    _lambda.FilterCriteria.filter(
                        {
                            "eventName": ["MODIFY"],
                            "dynamodb": {
                                "Keys": {"workflow#id": {"S": ["submission#0"]}},
                                "OldImage": {
                                    "is_valid": {
                                        "BOOL": _lambda.FilterRule.not_exists()
                                    }
                                },
                                "NewImage": {"is_valid": {"BOOL": [True]}},
                            },
                        }
                    )
                ],
                # on_failure=SqsDlq(dead_letter_queue),
            )
        )

        self.trigger_topic.grant_publish(publish_to_sns_lambda)

        self.api = ChaliceApp(
            self,
            broker_table=self.table,
            broker_bucket=self.bucket,
            broker_queues=self.queues,
        )

    def get_queue(self, workflow_name: str):
        queue = sqs.Queue(self, f"{workflow_name}Queue")
        self.queues.append(queue)

        self.trigger_topic.add_subscription(subscriptions.SqsSubscription(queue))
        return queue

    def register_workflows(self):
        pass
