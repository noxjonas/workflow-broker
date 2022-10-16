import os
import boto3
from chalice import Chalice, CORSConfig, CognitoUserPoolAuthorizer
import json

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


@app.route("/test", methods=["GET"], cors=cors_config, authorizer=authorizer)
def test():
    for k, v in os.environ.items():
        print(f"{k}: {v}")
    return json.dumps(os.environ['BROKER_QUEUES_NAMES_JSON'])


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
