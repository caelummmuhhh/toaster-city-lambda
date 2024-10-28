import json

class InventoryManager(object):
    """Handles Inventory."""
    _data = []

    def __init__(self):
        self.__populate_data__()


    def __populate_data__(self):
        with open('inventory.json', 'r') as rfile:
            #TODO: check if file exists or connect to a database
            self._data = json.load(rfile)


    def get_inventory(self, only_in_stock: bool = False):
        """Retrieves all items in inventory based on param."""
        if not only_in_stock:
            return self._data
        
        res = []
        for item in self._data:
            if item['quantity'] > 0:
                res.append(item)
        return res


    def get_item_by_id(self, id: int):
        """Retrieves item in inventory based on id."""
        for item in self._data:
            if item['id'] == id:
                return item
        return None


    def get_item_by_name(self, name: str):
        """Retrieves item in inventory based on name."""
        for item in self._data:
            if name.lower() == item['name'].lower():
                return item
        return None
    

    def item_enough_stock(self, item_id, quantity) -> bool:
        """
        Returns true if item stock >= quantity, false if not.
        Returns nothing if item not found
        """
        item = self.get_item_by_id(item_id)
        if not item:
            return None
        return item['quantity'] >= quantity

    
    def purchase_item(self, item_id: int, quantity: int) -> int:
        """Removes certain item quantity from stock. If not enough quantity, does nothing."""
        for i, item in enumerate(self._data):
            if item['id'] != item_id:
                continue
            if item['quantity'] < quantity:
                return
            
            self._data[i]['quantity'] -= quantity


    def purchase_items(self, items: list):
        """
        Remove specified quantities from each item, if enough stock, if not, does nothing for that item.
        Expected items list format:
        items = [
            {
            'id': int,
            'quantity': int
            }
        ]
        """

        for item in items:
            self.purchase_item(item['id'], item['quantity'])