import json
import os

from aws_cdk import aws_dynamodb as dynamodb

from aws_cdk import (
    aws_route53 as route53,
    aws_certificatemanager as acm,
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
    aws_cognito as cognito,
)
import aws_cdk as cdk
from chalice.cdk import Chalice


RUNTIME_SOURCE_DIR = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), os.pardir, "api", "runtime"
)


class ChaliceApp(cdk.Stack):
    def __init__(
        self,
        scope,
        _id,
        broker_table: dynamodb.Table,
        broker_bucket: s3.Bucket,
        broker_queues: list[sqs.IQueue],
        **kwargs
    ):
        super().__init__(scope, _id, **kwargs)

        stage_config = self.node.try_get_context("CONFIG")

        self.hosted_zone = route53.HostedZone.from_lookup(
            self, "baseZone", domain_name=stage_config["DomainName"]
        )

        self._cognito_setup()

        # self.dynamodb_table = self._create_ddb_table()
        self.chalice = Chalice(
            self,
            "ChaliceApp",
            source_dir=RUNTIME_SOURCE_DIR,
            stage_config={
                "api_gateway_endpoint_type": "REGIONAL",
                "api_gateway_custom_domain": {
                    "domain_name": stage_config["ApiDomain"],
                    "certificate_arn": stage_config["DomainCertificateArn"],
                },
                "environment_variables": {
                    "BROKER_TABLE": broker_table.table_name,
                    "BROKER_BUCKET": broker_bucket.bucket_name,
                    "BROKER_QUEUES_NAMES_JSON": json.dumps(
                        [queue.queue_name for queue in broker_queues]
                    ),
                    "USER_POOL_ARN": self.user_pool.user_pool_arn
                    # "APP_TABLE_NAME": self.dynamodb_table.table_name,
                },
            },
        )

        # # grant access to broker resources
        # chalice_role = self.chalice.get_role("DefaultRole")
        # broker_bucket.grant_read_write(chalice_role)
        # broker_table.grant_read_write_data(chalice_role)
        # for queue in broker_queues:
        #     queue.grant_send_messages(chalice_role)

        self.custom_domain = self.chalice.get_resource("ApiGatewayCustomDomain")
        self.a_record = route53.CfnRecordSet(
            self,
            "a-record-id",
            hosted_zone_id=self.hosted_zone.hosted_zone_id,
            name=stage_config["ApiDomain"],
            type="A",
            alias_target=route53.CfnRecordSet.AliasTargetProperty(
                dns_name=self.custom_domain.get_att("RegionalDomainName").to_string(),
                hosted_zone_id=self.custom_domain.get_att(
                    "RegionalHostedZoneId"
                ).to_string(),
                evaluate_target_health=False,
            ),
        )

        cdk.CfnOutput(self, "ApiCustomEndpoint", value=stage_config["ApiDomain"])

    def _cognito_setup(self):
        self.user_pool = cognito.UserPool(
            self,
            "WorkflowBroker",
            self_sign_up_enabled=True,
            user_verification=cognito.UserVerificationConfig(
                email_subject="Verify your email for workflow-broker",
                email_body="Thanks for signing up to workflow-broker! Your verification code is {####}",
                email_style=cognito.VerificationEmailStyle.CODE,
                sms_message="Thanks for signing up to workflow-broker! Your verification code is {####}",
            ),
            sign_in_aliases=cognito.SignInAliases(username=True, email=True),
        )

        self.app_client = self.user_pool.add_client(
            "default",
            # supported_identity_providers=[
            #     cognito.UserPoolClientIdentityProvider.AMAZON
            # ],
            auth_flows=cognito.AuthFlow(user_password=True, user_srp=True),
            o_auth=cognito.OAuthSettings(
                flows=cognito.OAuthFlows(authorization_code_grant=True),
                scopes=[cognito.OAuthScope.OPENID],
                callback_urls=["https://noxide.xyz", "http://localhost:8080"],
                # logout_urls=["https://my-app-domain.com/signin"]
            ),
            prevent_user_existence_errors=True,
            access_token_validity=Duration.minutes(60),
            id_token_validity=Duration.minutes(60),
            refresh_token_validity=Duration.days(30),
        )

    # def _create_ddb_table(self):
    #     dynamodb_table = dynamodb.Table(
    #         self,
    #         "AppTable",
    #         partition_key=dynamodb.Attribute(
    #             name="PK", type=dynamodb.AttributeType.STRING
    #         ),
    #         sort_key=dynamodb.Attribute(name="SK", type=dynamodb.AttributeType.STRING),
    #         removal_policy=cdk.RemovalPolicy.DESTROY,
    #     )
    #     cdk.CfnOutput(self, "AppTableName", value=dynamodb_table.table_name)
    #     return dynamodb_table
