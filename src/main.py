from router import Router

def lambda_handler(event, context):
    response = Router.route(event, context)

    response['headers'] = {
        'Access-Control-Allow-Origin': '*',  # Required for CORS support to work
        'Access-Control-Allow-Credentials': True  # Required for cookies, authorization headers with HTTPS
    }

    return response