import os

from aws_cdk import aws_dynamodb as dynamodb

from aws_cdk import (
    aws_route53 as route53,
    aws_certificatemanager as acm,
)
import aws_cdk as cdk
from chalice.cdk import Chalice


RUNTIME_SOURCE_DIR = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), os.pardir, 'runtime')


class ChaliceApp(cdk.Stack):

    def __init__(self, scope, id, **kwargs):
        super().__init__(scope, id, **kwargs)

        stage_config = self.node.try_get_context("CONFIG")


        self.hosted_zone = route53.HostedZone.from_lookup(self, "baseZone", domain_name=stage_config["DomainName"])

        self.dynamodb_table = self._create_ddb_table()
        self.chalice = Chalice(
            self, 'ChaliceApp', source_dir=RUNTIME_SOURCE_DIR,
            stage_config={
                "api_gateway_endpoint_type": "REGIONAL",
                "api_gateway_custom_domain": {
                    "domain_name": stage_config["ApiDomain"],
                    "certificate_arn": stage_config["DomainCertificateArn"],
                },
                'environment_variables': {
                    'APP_TABLE_NAME': self.dynamodb_table.table_name
                }
            }
        )

        self.dynamodb_table.grant_read_write_data(
            self.chalice.get_role('DefaultRole')
        )

        self.custom_domain = self.chalice.get_resource("ApiGatewayCustomDomain")
        self.a_record = route53.CfnRecordSet(
            self,
            "a-record-id",
            hosted_zone_id=self.hosted_zone.hosted_zone_id,
            name=stage_config["ApiDomain"],
            type="A",
            alias_target=route53.CfnRecordSet.AliasTargetProperty(
                dns_name=self.custom_domain.get_att('RegionalDomainName').to_string(),
                hosted_zone_id=self.custom_domain.get_att('RegionalHostedZoneId').to_string(),
                evaluate_target_health=False,
            ),
        )

        cdk.CfnOutput(self, "ApiCustomEndpoint", value=stage_config["ApiDomain"])



    def _create_ddb_table(self):
        dynamodb_table = dynamodb.Table(
            self, 'AppTable',
            partition_key=dynamodb.Attribute(
                name='PK', type=dynamodb.AttributeType.STRING),
            sort_key=dynamodb.Attribute(
                name='SK', type=dynamodb.AttributeType.STRING
            ),
            removal_policy=cdk.RemovalPolicy.DESTROY)
        cdk.CfnOutput(self, 'AppTableName',
                      value=dynamodb_table.table_name)
        return dynamodb_table
