import json


def dummy_workflow(event, context):
    """
    how to pass input to this?
        signed url?

    how will it know where to deposit results?
      later, this should simply be an endpoint to post json results to
    """

    print("dummy_workflow request: {}".format(json.dumps(event)))
