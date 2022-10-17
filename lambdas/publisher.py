import decimal
import json
import os
import boto3

from boto3.dynamodb.types import TypeDeserializer
import logging

logger = logging.getLogger()
LOGLEVEL = os.environ.get("LOG_LEVEL", "INFO").upper()
logger.setLevel(LOGLEVEL)

deserializer = TypeDeserializer()


def replace_decimals(obj):
    if isinstance(obj, list):
        for i in range(len(obj)):
            obj[i] = replace_decimals(obj[i])
        return obj
    elif isinstance(obj, dict):
        for k in obj:
            obj[k] = replace_decimals(obj[k])
        return obj
    elif isinstance(obj, decimal.Decimal):
        if obj % 1 == 0:
            return int(obj)
        else:
            return float(obj)
    else:
        return obj


def handler(event, context):
    sns = boto3.client("sns")

    for record in event["Records"]:
        message = {
            k: deserializer.deserialize(v)
            for k, v in record["dynamodb"]["NewImage"].items()
        }
        message.pop(
            "pre_signed_post", None
        )  # irrelevant at this point (may not be deleted yet)
        message = replace_decimals(message)
        logger.info(f"publishing message {json.dumps(message)}")

        response = sns.publish(
            TargetArn=os.environ["SNS_TOPIC_ARN"],
            Message=json.dumps(
                {"default": json.dumps(message)}
            ),  # TODO: why is this nested in default?
            MessageStructure="json",
            # Subject='perhaps something here',
            # MessageAttributes=.... <- should be able to use this as filter
        )
        logger.info(
            f"SNS publish response ({response['ResponseMetadata']['HTTPStatusCode']}): {response}"
        )
