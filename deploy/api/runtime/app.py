import os
import boto3
from chalice import Chalice, CORSConfig, CognitoUserPoolAuthorizer
import json
import time
import boto3
from botocore.exceptions import ClientError

app = Chalice(app_name="WorkflowBroker-api")
# dynamodb = boto3.resource("dynamodb")
# dynamodb_table = dynamodb.Table(os.environ.get("APP_TABLE_NAME", ""))

cors_config = CORSConfig(
    allow_origin="*",
    # allow_headers=['X-Special-Header'],
    max_age=600,
    # expose_headers=['X-Special-Header'],
    allow_credentials=False,
)
authorizer = CognitoUserPoolAuthorizer(
    "CognitoUserPool", provider_arns=[os.environ["USER_POOL_ARN"]]
)


def _get_authenticated_username():
    return app.current_request.context["authorizer"]["claims"]["cognito:username"]


dynamodb = boto3.resource("dynamodb")


def _get_broker_table():
    return dynamodb.Table(os.environ["BROKER_TABLE"])


def create_presigned_post(
    bucket_name, object_name, fields=None, conditions=None, expiration=3600
):
    """Generate a presigned URL S3 POST request to upload a file

    :param bucket_name: string
    :param object_name: string
    :param fields: Dictionary of prefilled form fields
    :param conditions: List of conditions to include in the policy
    :param expiration: Time in seconds for the presigned URL to remain valid
    :return: Dictionary with the following keys:
        url: URL to post to
        fields: Dictionary of form fields and values to submit with the POST
    :return: None if error.
    """

    # Generate a presigned S3 POST URL
    s3_client = boto3.client("s3")
    try:
        response = s3_client.generate_presigned_post(
            bucket_name,
            object_name,
            Fields=fields,
            Conditions=conditions,
            ExpiresIn=expiration,
        )
    except ClientError as e:
        app.log.exception(e)
        raise

    # The response contains the presigned URL and required fields
    return response


@app.route("/test", methods=["GET"], cors=cors_config, authorizer=authorizer)
def test():
    for k, v in os.environ.items():
        print(f"{k}: {v}")
    return json.dumps(os.environ["BROKER_QUEUES_NAMES_JSON"])


@app.route("/submit", methods=["POST"], cors=cors_config, authorizer=authorizer)
def submit():
    expiration = 60
    min_size = 1
    max_size = 10485760

    username = _get_authenticated_username()
    timestamp = int(time.time())

    object_name = f"{username}/{timestamp}/${{filename}}"

    pre_signed_post = create_presigned_post(
        os.environ["BROKER_BUCKET"],
        object_name,
        conditions=[["content-length-range", min_size, max_size]],
        expiration=expiration,
    )

    table = _get_broker_table()

    table.put_item(
        Item={
            "user_id#workflow_id": f"{username}#{timestamp}",
            "workflow#id": "submission#0",
            "pre_signed_post": pre_signed_post,
            "ttl": timestamp + expiration,
            # "state": "WAITING_FOR_FILE_UPLOAD", # figuring out whether all workflows completed should not be part of this
            "accepted_types": "to guide the frontend",  # pointless since this can be in fields of signed url?
            "content-length-range": [min_size, max_size],  # same as accepted types
            "workflows": [],  # TODO: defaults?
            "submission_form_data": {"notes": "this is my quirky workflow"},
        }
    )
    return pre_signed_post


#
# @app.route("/users/{username}", methods=["GET"], cors=cors_config)
# def get_user(username):
#     key = {
#         "PK": "User#%s" % username,
#         "SK": "Profile#%s" % username,
#     }
#     item = dynamodb_table.get_item(Key=key)["Item"]
#     del item["PK"]
#     del item["SK"]
#     return item
#
#
# @app.route("/users/{username}", methods=["DELETE"], cors=cors_config)
# def get_user(username):
#     key = {
#         "PK": "User#%s" % username,
#         "SK": "Profile#%s" % username,
#     }
#     dynamodb_table.delete_item(Key=key)
#     return {}
