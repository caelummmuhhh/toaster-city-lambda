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
    # Parse the incoming body from the event (API Gateway passes body as a string)
    try:
        body_raw = event['body']
        body = json.loads(body_raw)
    except Exception as e:
        return {
            'statusCode': 400,
            'body': json.dumps({
                'message': 'Invalid JSON format',
                'error': str(e)
            })
        }

    # Extract the items from the body
    items_ordered = body.get('items', [])
    unavailable_items = []

    # Check each item against inventory
    for order_item in items_ordered:
        found = False
        for toaster in toasters:
            if order_item['item_id'] == toaster['name']:  # Match by name
                if order_item['quantity'] > toaster['quantity']:
                    unavailable_items.append({
                        'item': toaster['name'],
                        'requested_qty': order_item['quantity'],
                        'available_qty': toaster['quantity']
                    })
                found = True
                break

        if not found:
            unavailable_items.append({
                'item': order_item['item_id'],
                'message': 'Item not found in inventory'
            })

    # Return error if any item is unavailable
    if unavailable_items:
        return {
            'statusCode': 400,
            'body': json.dumps({
                'message': 'Some items are out of stock or unavailable',
                'unavailableItems': unavailable_items
            })
        }

    # Decrement the quantity of items if the order is successful
    for order_item in items_ordered:
        for toaster in toasters:
            if order_item['item_id'] == toaster['name']:
                toaster['quantity'] -= order_item['quantity']

    # Generate a unique confirmation number
    confirmation_number = f"CONF-{str(hash(json.dumps(body)))}"

    # Return success response
    return {
        'statusCode': 200,
        'body': json.dumps({
            'message': 'Order processed successfully',
            'confirmationNumber': confirmation_number
        })
    }

def return_error_body(event):
    return {
        'statusCode': 404,
        'body': json.dumps({'message': 'Unable to process request'})
    }

def get_handler_function(path):
    if path == '/inventory-management/inventory':
        return get_inventory
    elif '/inventory-management/inventory/items/' in path and '{id}' in path:
        return get_item_by_id
    elif path == '/inventory-management/inventory/items':
        return get_item_by_name
    elif path == '/order-processing/order':
        return post_order
    else:
        return return_error_body

# Main Lambda handler function
def lambda_handler(event, context):
    # Handle URL paths of...
        # /inventory-management/inventory [GET]
        # /inventory-management/inventory/items/{id} [GET]
        # /inventory-management/inventory/items?Name=&InStock= [GET]
        # /order-processing/order [POST]
    
    path = event['resource']  # Extract resource from the event
    
    # Obtain the correct handler function based on the path
    handler_function = get_handler_function(path)

    # Call the handler function and get the response
    response = handler_function(event)
    
    # Add CORS headers
    response['headers'] = {
        'Access-Control-Allow-Origin': '*',  # Required for CORS support to work
        'Access-Control-Allow-Credentials': True  # Required for cookies, authorization headers with HTTPS
    }
    return response