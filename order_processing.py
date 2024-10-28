from inventory_management import InventoryManager

class OrderProcessor(object):
    """Handles order processing for a singular order."""
    _inventory: InventoryManager
    _valid_order = True
    _unknown_items_found = False
    _items_in_stock = True

    def __init__(self, inventory: InventoryManager):
        self._inventory = inventory

    def process_order(self, order):
        self.__process_order_items__(order['items'])
        

        self.__process_payment__(order['payment_info'])
        self.__process_shipping__(order['shipping_info'])

    def __process_order_items__(self, items: list):
        # Check if each item exists and has enough stock before making any changes to inventory
        # So that we can abort without making any changes if any items are not in stock or not found
        for item in items:
            item_in_stock = self._inventory.item_enough_stock(item['id'], item['quantity'])

            if item_in_stock is None:
                self._unknown_items_found = True
                return
            if item_in_stock == False:
                self._items_in_stock = False
                return
            
        self._inventory.purchase_items(items)
    
    def __process_payment__(self, payment):
        pass

    def __process_shipping__(self, shipment):
        pass
    
    def __generate_confirmation_number__(self, order):
        pass
            
            



order = {
    'items': [
        {
            'item_id': 123,
            'quantity': 123
        }
    ],
    'payment_info': {
        'card_number': '123',
        'expiration_date': '10/20',
        'cvv': 123,
        'billing_address': {
            'address_1': '123 Main St',
            'address_2': '321 2nd Ave',
            'city': 'Columbus',
            'state': 'OH',
            'zip': 43210
        }
    },
    'shipping_info': {
        'name': 'jane doe',
        'address_1': '123 Main St',
        'address_2': '321 2nd Ave',
        'city': 'Columbus',
        'state': 'OH',
        'zip': 43210
    }
}
