import json


def handler(event, context):
    print(f'event: {event}\ncontext: {context}')
    return {
        'parameters': {
          'numbers': '60, 9'
        },
        'meta': {
            'workflow': 'calc-sum',
        }
    }
