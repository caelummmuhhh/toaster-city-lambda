
class _BaseHandler(object):
    def __init__(self):
        pass

    def handle_request(self, event, context) -> tuple[int, dict | str]:
        """
        Handles a request
        
        Returns
        -------
        tuple[int, dict | str]
            An HTTP status code and a body that's either a str or dict.
        """
        pass