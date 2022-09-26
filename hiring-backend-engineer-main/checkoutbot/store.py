import multiprocessing
import sys
from typing import Dict, List

"""
Cart represents all of the items that a single shopper has selected to purchase 
"""
class Cart:
    customer_id: int # ID of the customer that is going to purchase the items in this cart
    items: List[int] # list of IDs representing items that the shopper is going to purchase

    def __init__(self, customer_id):
        self.items = []
        self.customer_id = customer_id

    # Number of items in the cart
    def size(self):
        return len(self.items)

    # Add an item with the given ID to the cart
    def addItem(self, item_id):
        self.items.append(item_id)

"""
Register represents a single register in the store. It contains pending carts containing items from one or more shoppers.
"""
class Register:
    customer_cart_map: Dict[int, Cart] # Mapping of customer IDs to their pending cart
    lock = multiprocessing.Lock # Mutex lock to prevent modification of cart or register state when needed
    register_id: int # Unique register ID

    def __init__(self, register_id):
        self.lock = multiprocessing.Lock()
        self.register_id = register_id
        self.customer_cart_map = {}

    """ 
    Adds the given item to the specified customer's cart. If the customer doesn't have an existing cart, a new one is created.
    """
    def addItemToCart(self, customer_id, item_id):
        self.lockRegister()
        
        if customer_id in self.customer_cart_map:
            cart = self.customer_cart_map[customer_id]
            cart.addItem(item_id)
        else:
            cart = Cart(customer_id)
            cart.addItem(item_id)
            self.customer_cart_map[customer_id] = cart
        
        self.unlockRegister()
    
    """
    Checks out the given customer's cart. Removes the customer's cart from the register's state.
    """
    def checkoutCart(self, customer_id):
        self.lockRegister()

        if customer_id in self.customer_cart_map:
            del self.customer_cart_map[customer_id]
        else:
            raise Exception("A cart to checkout does not exist for the given customer.")

        self.unlockRegister()

    """
    Determines the total number of items pending for checkout at this register from all pending carts.
    """
    def getTotalItems(self):
        total_items = 0
        for cart in self.customer_cart_map.values():
            total_items += cart.size()
        return total_items
    
    """
    Locks the register from being modified (new items being added or carts being checked out.
    """
    def lockRegister(self):
        self.lock.acquire()

    """
    Unlocks the register so that its state can be modified again.
    """
    def unlockRegister(self):
        self.lock.release()

    """
    Returns the current state of the register. The state is representated by an array which is based 
    on the number of total items in the cart. Each entry in the array represents an item pending checkout
    at this register. The value of the entry represents the customer that owns the item.
    """
    def getRegisterState(self):
        register_state = []

        for cart in self.customer_cart_map.values():
            register_state += ([cart.customer_id] * cart.size())

        return register_state

"""
Store class to encapsulate all registers in the store and the logic to distribute work between them.
"""
class Store:
    registers: List[Register] # All registers in this store
    register_map: Dict[int, Register] # Mapping of a given customer to which register their pending cart is assigned

    def __init__(self, num_registers=25):
        registers = []

        for i in range(num_registers):
            registers.append(Register(i))

        self.registers = registers
        self.register_map = {}

    """
    Assigns an item to a pending cart based on the customer and register availability.
    """
    def assignItem(self, customer_id, item_id):
        if (customer_id in self.register_map):
            register = self.register_map[customer_id]     
            register.addItemToCart(customer_id, item_id)
        else:
            register = self.getLeastUtilizedRegister()
            register.addItemToCart(customer_id, item_id)
            self.register_map[customer_id] = register
    
    """
    Checks out all pending items for the given customer's cart at whichever register it is at.
    """
    def checkoutCustomer(self, customer_id):
        if (customer_id in self.register_map): 
            register = self.register_map[customer_id]
            register.checkoutCart(customer_id)
            del self.register_map[customer_id]  
        else:
            raise Exception("Attempted to checkout customer without a cart")

    """
    Finds the register with the lowest utilization based on the current total number of items that are pending at the register. 
    """
    def getLeastUtilizedRegister(self) -> Register:
        self.lockRegisters()
        lowest_items = sys.maxsize
        lowest_utilized_register = None
        
        for register in self.registers:
            total_items = register.getTotalItems()
            if total_items == 0:
                self.unlockRegisters()
                return register
            if lowest_items > total_items:
                lowest_utilized_register = register
                lowest_items = total_items

        if lowest_utilized_register == None: 
            raise Exception("Invalid register state")

        self.unlockRegisters()
        return lowest_utilized_register

    # Locks all register in the store so that their state cannot be modified
    def lockRegisters(self):
        for register in self.registers:
            register.lockRegister()

    # Unlocks all registers in the store so that their state can be modified.
    def unlockRegisters(self):
        for register in self.registers:
            register.unlockRegister()

    """
    Returns the current state of all registers in the store.
    """
    def getAllRegisterState(self):
        state = {}
        self.lockRegisters()
        for register in self.registers:
            state[register.register_id] = register.getRegisterState()
        self.unlockRegisters()
        return state