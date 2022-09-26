from http import HTTPStatus
from flask import Flask, request, Response
import json

from store import Store

app = Flask(__name__)
store: Store

@app.route('/health')
def health(): 
    return Response(None, HTTPStatus.OK)

@app.route('/state', methods = ['DELETE'])
def reset():
    global store
    store = Store(25)
    return Response(None, HTTPStatus.OK)

@app.route('/add', methods = ['POST'])
def add():
    customer_id = request.form['customer_id']
    item_id = request.form['item_id']
    store.assignItem(customer_id, item_id)
    return Response(json.dumps({ "registers": store.getAllRegisterState() }), HTTPStatus.CREATED)

@app.route('/checkout', methods = ['POST'])
def checkout():
    customer_id = request.form['customer_id']
    store.checkoutCustomer(customer_id)
    return Response(json.dumps({ "registers": store.getAllRegisterState() }), HTTPStatus.CREATED)

if __name__ == '__main__':
    app.run(port=5000)