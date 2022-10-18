import os
import time
from pathlib import Path

import requests

ACCESS_TOKEN = None
EXPIRATION_TIME = None


def get_elastic_path_access_token():
    global ACCESS_TOKEN
    global EXPIRATION_TIME
    current_time = time.time()
    if ACCESS_TOKEN is None or EXPIRATION_TIME - 60 < current_time:
        client_id = os.getenv('ELASTIC_PATH_CLIENT_ID')
        client_secret = os.getenv('ELASTIC_PATH_CLIENT_SECRET')
        url = 'https://api.moltin.com/oauth/access_token'
        data = {
            'client_id': client_id,
            'client_secret': client_secret,
            'grant_type': 'client_credentials'
        }
        response = requests.post(url, data=data)
        response.raise_for_status()
        decoded_response = response.json()
        ACCESS_TOKEN = decoded_response['access_token']
        EXPIRATION_TIME = decoded_response['expires']
    return ACCESS_TOKEN


def fetch_products():
    access_token = get_elastic_path_access_token()
    url = 'https://api.moltin.com/v2/products'
    headers = {'Authorization': f'Bearer {access_token}'}
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    products = response.json()['data']
    return products


def fetch_product(product_id):
    access_token = get_elastic_path_access_token()
    url = f'https://api.moltin.com/v2/products/{product_id}'
    headers = {'Authorization': f'Bearer {access_token}'}
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    product = response.json()['data']
    return product


def get_product_image(file_id):
    access_token = get_elastic_path_access_token()
    url = f'https://api.moltin.com/v2/files/{file_id}'
    headers = {'Authorization': f'Bearer {access_token}'}
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    image_metadata = response.json()['data']
    image_directory = Path('./images')
    Path.mkdir(image_directory, exist_ok=True)
    image_path = Path(image_directory, image_metadata['id']+'.jpg')
    if not image_path.exists():
        response = requests.get(image_metadata['link']['href'])
        response.raise_for_status()
        with open(image_path, 'wb') as file:
            file.write(response.content)
    return image_path


def add_product_to_cart(product_id, quantity, cart_id):
    access_token = get_elastic_path_access_token()
    url = f'https://api.moltin.com/v2/carts/{cart_id}/items'
    headers = {'Authorization': f'Bearer {access_token}'}
    payload = {
        'data': {
            'id': product_id,
            'type': 'cart_item',
            'quantity': quantity
        }
    }
    response = requests.post(url, headers=headers, json=payload)
    response.raise_for_status()
    cart = response.json()
    return cart


def delete_product_from_cart(product_id, cart_id):
    access_token = get_elastic_path_access_token()
    url = f'https://api.moltin.com/v2/carts/{cart_id}/items/{product_id}'
    headers = {'Authorization': f'Bearer {access_token}'}
    response = requests.delete(url, headers=headers)
    response.raise_for_status()
    cart = response.json()
    return cart


def fetch_cart(cart_id):
    access_token = get_elastic_path_access_token()
    url = f'https://api.moltin.com/v2/carts/{cart_id}/items'
    headers = {'Authorization': f'Bearer {access_token}'}
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    cart = response.json()
    return cart


def create_customer(customer_name, customer_email, latitude, longitude):
    access_token = get_elastic_path_access_token()
    url = 'https://api.moltin.com/v2/customers'
    headers = {'Authorization': f'Bearer {access_token}'}
    payload = {
        'data': {
            'type': 'customer',
            'name': customer_name,
            'email': customer_email,
            'lat': latitude,
            'lon': longitude
        }
    }
    response = requests.post(url, headers=headers, json=payload)
    response.raise_for_status()
    customer = response.json()['data']
    return customer


def create_product(product):
    access_token = get_elastic_path_access_token()
    url = 'https://api.moltin.com/v2/products'
    headers = {'Authorization': f'Bearer {access_token}'}
    payload = {
        'data': {
            'type': 'product',
            'name': product['name'],
            'slug': str(product['id']),
            'sku': product['name'],
            'manage_stock': False,
            'description': product['description'],
            'status': 'live',
            'commodity_type': 'physical',
            'price': [
                {
                    "amount": product['price'] * 100,
                    "currency": "RUB",
                    "includes_tax": True
                }
            ]
        }
    }
    response = requests.post(url, headers=headers, json=payload)
    response.raise_for_status()
    created_product = response.json()['data']
    return created_product['id']


def create_image(image_url):
    access_token = get_elastic_path_access_token()
    url = 'https://api.moltin.com/v2/files'
    headers = {'Authorization': f'Bearer {access_token}'}
    files = {
        'file_location': (None, image_url),
    }
    response = requests.post(url, headers=headers, files=files)
    response.raise_for_status()
    created_file = response.json()['data']
    return created_file['id']


def set_product_main_image(product_id, image_id):
    access_token = get_elastic_path_access_token()
    url = f'https://api.moltin.com/v2/products/{product_id}/relationships/main-image'
    headers = {'Authorization': f'Bearer {access_token}'}
    payload = {
        'data': {
            'id': image_id,
            'type': 'main_image'
        }
    }
    response = requests.post(url, headers=headers, json=payload)
    response.raise_for_status()


def create_flow(flow_name, flow_description):
    access_token = get_elastic_path_access_token()
    url = 'https://api.moltin.com/v2/flows'
    headers = {'Authorization': f'Bearer {access_token}'}
    payload = {
        'data': {
            'type': 'flow',
            'name': flow_name,
            'slug': flow_name,
            'description': flow_description,
            'enabled': True
        }
    }
    response = requests.post(url, headers=headers, json=payload)
    response.raise_for_status()
    created_flow = response.json()['data']
    return created_flow['id']


def create_flow_field(flow_id, field: dict):
    access_token = get_elastic_path_access_token()
    url = 'https://api.moltin.com/v2/fields'
    headers = {'Authorization': f'Bearer {access_token}'}
    payload = {
        'data': {
            'type': 'field',
            'name': field['name'],
            'slug': field['name'],
            'field_type': field['type'],
            'description': field['description'],
            'required': True,
            'enabled': True,
            'relationships': {
                'flow': {
                    'data': {
                        'type': 'flow',
                        'id': flow_id,
                    }
                }
            }
        }
    }
    response = requests.post(url, headers=headers, json=payload)
    response.raise_for_status()
    created_field = response.json()['data']
    return created_field['id']


def create_flow_entry(flow_slug, field_values):
    access_token = get_elastic_path_access_token()
    url = f'https://api.moltin.com/v2/flows/{flow_slug}/entries'
    headers = {'Authorization': f'Bearer {access_token}'}
    payload = {
        'data': {
            'type': 'entry'
        }
    }
    for field_name, field_value in field_values.items():
        payload['data'][field_name] = field_value
    response = requests.post(url, headers=headers, json=payload)
    response.raise_for_status()
    created_flow_entry = response.json()['data']
    return created_flow_entry['id']


def get_all_entries(flow_slug):
    access_token = get_elastic_path_access_token()
    url = f'https://api.moltin.com/v2/flows/{flow_slug}/entries'
    headers = {'Authorization': f'Bearer {access_token}'}
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    entries = response.json()['data']
    return entries


def get_entry(flow_slug, entry_id):
    access_token = get_elastic_path_access_token()
    url = f'https://api.moltin.com/v2/flows/{flow_slug}/entries/{entry_id}'
    headers = {'Authorization': f'Bearer {access_token}'}
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    entry = response.json()['data']
    return entry
