import json

toasters = [
    {
        'id': 1,
        'name': 'Floral Toaster',
        'price': 12.99,
        'img': '/images/Toaster1.jpeg',
        'quantity': 10
    },
    {
        'id': 2,
        'name': 'Hamilton Toaster',
        'price': 199.49,
        'img': '/images/Toaster2.jpeg',
        'quantity': 10
    },
    {
        'id': 3,
        'name': 'Long Toaster',
        'price': 12.99,
        'img': '/images/Toaster3.jpeg',
        'quantity': 10
    },
    {
        'id': 4,
        'name': 'R2D2 Toaster',
        'price': 12.99,
        'img': '/images/Toaster4.jpeg',
        'quantity': 10
    },
    {
        'id': 5,
        'name': 'Goofy Button Toaster',
        'price': 12.99,
        'img': '/images/Toaster5.jpeg',
        'quantity': 10
    },
    {
        'id': 6,
        'name': 'Knob Toaster',
        'price': 12.99,
        'img': '/images/Toaster6.jpeg',
        'quantity': 10
    }
]

def get_inventory(event):
    return {
        'statusCode': 200,
        'body': json.dumps(toasters)
    }

def get_item_by_id(event):
    id = event['pathParameters']['id']

    for toaster in toasters:
        if str(toaster['id']) == str(id):
            return {
                'statusCode': 200,
                'body': json.dumps(toaster)
            }

    return {
        'statusCode': 404,
        'body': json.dumps({
            'message': 'Item not found'
        })
    }

def get_item_by_name(event):
    name = event['queryStringParameters']['Name']

    for toaster in toasters:
        if toaster['name'] == name:
            return {
                'statusCode': 200,
                'body': json.dumps(toaster)
            }
    
    return {
        'statusCode': 404,
        'body': json.dumps({
            'message': 'Item not found'
        })
    }

def post_order(event):
    bodyRaw = event['body']
    body = json.loads(bodyRaw)

    # TODO: Further logic

    return {
        'statusCode': 200,
        'body': json.dumps({
            'message': '***This is not finished yet***'
        })
    }

def return_error_body(event):
    return {
        'statusCode': 404,
        'body': json.dumps({
            'message': 'Unable to process request'
        })
    }

def get_handler_function(path):
    if path == '/inventory-management/inventory':
        return get_inventory
    elif path == '/inventory-management/inventory/items/{id}':
        return get_item_by_id
    elif path == '/inventory-management/inventory/items':
        return get_item_by_name
    elif path == '/order-processing/order':
        return post_order
    else:
        return return_error_body


def lambda_handler(event, context):
    # Handle URL paths of...
        # /inventory-management/inventory [GET]
        # /inventory-management/inventory/items{id} [GET]
        # /inventory-management/inventory/items?Name=&InStock=[GET]
        # /order-processing/order [POST]
    
    # Using resource as it contains the full path (i.e. includes '/{Id}')
    path = event['resource']

    # Obtains the correct function to be called
    handler_function = get_handler_function(path)

    # Calls the discovered function
    # return handler_function(event)
    response = handler_function(event)
    response['headers'] = {
        'Access-Control-Allow-Origin': '*', # Required for CORS support to work
        'Access-Control-Allow-Credentials': True, # Required for cookies, authorization headers with HTTPS
    }
    return response