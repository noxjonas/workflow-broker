from tempfile import TemporaryDirectory
import os
import json
from typing import Tuple

import boto3
from typing.io import BinaryIO
from schema import Schema, And, Regex
import logging
import traceback

# TODO: make reusable
logger = logging.getLogger()
LOGLEVEL = os.environ.get("LOG_LEVEL", "INFO").upper()
logger.setLevel(LOGLEVEL)

input_schema = Schema({"sequence": And(Regex(r"^[ATGCNatgcn]+$"), len)})


def validate(file: BinaryIO) -> Tuple[bool, str]:
    try:
        data = json.load(file)
        input_schema.validate(data)
    except:
        valid = False
        logs = traceback.format_exc()
        logger.exception("Invalid input")
    else:
        valid = True
        logs = "OK"

    return valid, logs


def handler(event, context):
    """validate input and set the "is_valid" attribute on submission item, which will trigger the workflows"""

    s3, dynamodb = boto3.resource("s3"), boto3.resource("dynamodb")
    table = dynamodb.Table(os.environ["WORKFLOW_TABLE"])

    for record in event["Records"]:
        bucket_name = record["s3"]["bucket"]["name"]
        bucket = s3.Bucket(bucket_name)

        with TemporaryDirectory() as tmp_dir:
            f_name = os.path.join(tmp_dir, record["s3"]["object"]["eTag"])

            with open(f_name, "wb") as f:
                bucket.download_fileobj(record["s3"]["object"]["key"], f)

            with open(f_name, "rb") as f:
                is_valid, logs = validate(f)

                pk = record["s3"]["object"]["key"].replace("/", "#", 1).split("/", 1)[0]
                key = {
                    "user_id#workflow_id": pk,
                    "workflow#id": "submission#0",
                }

                table.update_item(
                    Key=key,
                    UpdateExpression="set s3_url = :su, is_valid = :iv, validation_logs = :vl",
                    ExpressionAttributeValues={
                        # TODO: create signed url to avoid having to give permissions to read the item?
                        ":su": f's3://{os.environ["WORKFLOW_TABLE"]}/{record["s3"]["object"]["key"]}',
                        ":iv": is_valid,
                        ":vl": logs,
                    },
                )

                if is_valid:
                    # since item is valid, remove "pre_signed_url" and protect item from deletion
                    table.update_item(
                        Key=key,
                        UpdateExpression="remove pre_signed_post, #ttl",
                        ExpressionAttributeNames={"#ttl": "ttl"},
                    )
