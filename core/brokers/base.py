class BaseBroker:
    def __init__(self, event, context):
        self.event = event
        self.context = context
        self.parameters = event.get('parameters', None)

    def get(self):
        """parameters"""
        raise Exception('must overwrite get method')

    def validate(self):
        """parameters
        raise one of: Exception('Bad Request'), Exception('Unauthorized')
        """
        pass

    def run(self):
        pass

    def watch(self, state):
        pass

    def abort(self, state):
        pass
