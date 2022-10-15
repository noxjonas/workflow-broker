import json
import os
import boto3
from tempfile import TemporaryDirectory
from boto3.dynamodb.types import TypeDeserializer

deserializer = TypeDeserializer()

def validate(event, context):
    """
    on success -> add entry to the workflow table
    on failure -> also add the entry... but it will be in FAILED state
    """
    print("request: {}".format(json.dumps(event)))
    print("WORKFLOW_TABLE", os.environ["WORKFLOW_TABLE"])
    s3, dynamodb = boto3.resource("s3"), boto3.resource('dynamodb')
    table = dynamodb.Table(os.environ["WORKFLOW_TABLE"])

    for record in event["Records"]:
        bucket_name = record["s3"]["bucket"]["name"]
        bucket = s3.Bucket(bucket_name)

        with TemporaryDirectory() as tmp_dir:
            f_name = os.path.join(tmp_dir, record["s3"]["object"]["eTag"])

            with open(f_name, 'wb') as f:
                bucket.download_fileobj(record["s3"]["object"]["key"], f)

            with open(f_name, "rb") as f:
                out = json.load(f)
                print('output', out)
                table.put_item(Item={
                    "user_id#workflow_id": "jonas#uuid8574312", "workflow#id": "input#0", "input": out
                })


#
#
#
# a = {
#     "Records": [
#         {
#             "eventVersion": "2.1",
#             "eventSource": "aws:s3",
#             "awsRegion": "eu-central-1",
#             "eventTime": "2022-10-13T19:02:29.851Z",
#             "eventName": "ObjectCreated:Put",
#             "userIdentity": {"principalId": "AWS:AIDA4M5CIZDBSDR6WU4MU"},
#             "requestParameters": {"sourceIPAddress": "82.7.77.111"},
#             "responseElements": {
#                 "x-amz-request-id": "7PQA2PKCE0TZ8XQD",
#                 "x-amz-id-2": "01KR+PJyuEXxEQL2niKoPHI4VQJ3da9oldbKQWP3gSXN8laO8x7qQVCAQ9kyQSRkYWTarS/+zsuwi4xfN0+RY/KJCIKUIW1p",
#             },
#             "s3": {
#                 "s3SchemaVersion": "1.0",
#                 "configurationId": "MWRkMGZmYWMtYzEzNS00OTNmLTlmZDAtNmFiNDI4ZDc0N2Yy",
#                 "bucket": {
#                     "name": "workflowbroker-inputbucket3bf8630a-tq0dhr6i0pl5",
#                     "ownerIdentity": {"principalId": "A3GA2H3QJM5JCZ"},
#                     "arn": "arn:aws:s3:::workflowbroker-inputbucket3bf8630a-tq0dhr6i0pl5",
#                 },
#                 "object": {
#                     "key": "12515351",
#                     "size": 44,
#                     "eTag": "150087a7ff63dc20f72905347f184edc",
#                     "sequencer": "00634860C5C84D2DF6",
#                 },
#             },
#         }
#     ]
# }


def publish_to_sns(event, context):
    print("push_to_sns request: {}".format(json.dumps(event)))
    sns = boto3.client('sns')

    for record in event["Records"]:
        message = {k: deserializer.deserialize(v) for k, v in record["dynamodb"]["NewImage"].items()}
        response = sns.publish(
            TargetArn=os.environ["SNS_TOPIC_ARN"],
            Message=json.dumps({'default': json.dumps(message)}),
            MessageStructure='json'
        )
        print('response from publish', response)


b = {
    "Records": [
        {
            "eventID": "00ec73f6168acc6c4d2e4d1b00aa0c85",
            "eventName": "INSERT",
            "eventVersion": "1.1",
            "eventSource": "aws:dynamodb",
            "awsRegion": "eu-central-1",
            "dynamodb": {
                "ApproximateCreationDateTime": 1665694495,
                "Keys": {
                    "user_id#workflow_id": {
                        "S": "jonas#uuid8574312"
                    },
                    "workflow#id": {
                        "S": "input#0"
                    }
                },
                "NewImage": {
                    "input": {
                        "M": {
                            "sequence": {
                                "S": "ATGTAGCTAGTACTTAAGATTA"
                            }
                        }
                    },
                    "user_id#workflow_id": {
                        "S": "jonas#uuid8574312"
                    },
                    "workflow#id": {
                        "S": "input#0"
                    }
                },
                "SequenceNumber": "100000000014963977539",
                "SizeBytes": 147,
                "StreamViewType": "NEW_AND_OLD_IMAGES"
            },
            "eventSourceARN": "arn:aws:dynamodb:eu-central-1:852354451651:table/WorkflowBroker-WorkflowTable0AE28607-2HQJDNGZQCLI/stream/2022-10-13T18:55:48.250"
        }
    ]
}


def dummy_workflow(event, context):
    """
    how to pass input to this?
        signed url?

    how will it know where to deposit results?
      later, this should simply be an endpoint to post json results to
    """

    print("dummy_workflow request: {}".format(json.dumps(event)))
