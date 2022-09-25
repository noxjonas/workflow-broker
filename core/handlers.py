import json
from workflows.calculus.sum import SumWorkflow
from brokers.base import BaseBroker

def hello(event, context):
    print('request: {}'.format(json.dumps(event)))
    return {
        'statusCode': 200,
        'headers': {
            'Content-Type': 'text/plain'
        },
        'body': 'Hello, CDK! You have hit {}\n'.format(event['path'])
    }

def all_subclasses(cls):
    return set(cls.__subclasses__()).union(
        [s for c in cls.__subclasses__() for s in all_subclasses(c)])

def execute_job(event, context):
    print(f'event: {event}\ncontext: {context}')
    workflows = [sub for sub in all_subclasses(BaseBroker)]
    print(f'workflows: {workflows}')
    workflow = next((wf for wf in workflows if getattr(wf, 'name', None) == event.get('meta').get('workflow')), None)

    new_state = workflow(event, context).run()
    print('my new state?', type(new_state), new_state)

    return new_state
