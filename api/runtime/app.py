import os
import boto3
from chalice import Chalice, CORSConfig

app = Chalice(app_name='api')
dynamodb = boto3.resource('dynamodb')
dynamodb_table = dynamodb.Table(os.environ.get('APP_TABLE_NAME', ''))

cors_config = CORSConfig(
    allow_origin='*',
    # allow_headers=['X-Special-Header'],
    max_age=600,
    # expose_headers=['X-Special-Header'],
    allow_credentials=False
)


@app.route('/users', methods=['POST'], cors=cors_config)
def create_user():
    request = app.current_request.json_body
    item = {
        'PK': 'User#%s' % request['username'],
        'SK': 'Profile#%s' % request['username'],
    }
    item.update(request)
    dynamodb_table.put_item(Item=item)
    return {}


@app.route('/users/{username}', methods=['GET'], cors=cors_config)
def get_user(username):
    key = {
        'PK': 'User#%s' % username,
        'SK': 'Profile#%s' % username,
    }
    item = dynamodb_table.get_item(Key=key)['Item']
    del item['PK']
    del item['SK']
    return item


@app.route('/users/{username}', methods=['DELETE'], cors=cors_config)
def get_user(username):
    key = {
        'PK': 'User#%s' % username,
        'SK': 'Profile#%s' % username,
    }
    dynamodb_table.delete_item(Key=key)
    return {}
