import json

from brokers.aws.lambdas import LambdaBroker
import boto3


class SumWorkflow(LambdaBroker):
    name = 'calc-sum'

    def __init__(self, event, context):
        super().__init__(event, context)

    def get(self):
        return {
            "numbers": {
                "Description": "Numbers to add",
                "Type": "CommaDelimitedList",
                "Default": "2,2"
            }
        }

    def validate(self):
        print(self.event, self.context)
        numbers = self.event.get("parameters")["numbers"]
        try:
            [float(i.strip()) for i in numbers.split(',')]
        except (ValueError, TypeError) as e:
            raise Exception('Bad Request')

    def run(self):
        numbers = self.event.get("parameters")["numbers"]
        numbers = [float(i.strip()) for i in numbers.split(',')]
        _lambda = boto3.client('lambda')
        print('i am trying?')
        response = _lambda.invoke(
            FunctionName='calc-sum-lambda',
            InvocationType='Event',
            ClientContext='string',
            Payload=json.dumps({'numbers': numbers}),
        )
        print('response?', type(response), response)
        self.event['invoke_response'] = response['StatusCode']
        return self.event

    def watch(self, state):
        state['watch'] = "I peeped"
        return state

    def abort(self, state):
        state["abort"] = "I am terminating"
        return state
