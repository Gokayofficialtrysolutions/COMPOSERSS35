"""
Utility functions for the qoffeeapi package.
"""

def proxy(handler, response):
    """
    Extracts tuple of (status_code, response_body) from a response
    and uses the provided Tornado IPythonHandler instance to send the
    response back to the requester.

    Args:
        handler (IPythonHandler): The Tornado request handler instance.
        response (tuple): A tuple containing (status_code, response_body).
                          response_body is typically a dict or string.
    """
    status_code, response_body = response
    handler.set_status(status_code)
    if status_code != 204:
        handler.finish(response_body)