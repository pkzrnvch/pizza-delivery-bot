import json
from pathlib import Path

from dotenv import load_dotenv

from elastic_path_api import (create_product,
                              create_image,
                              set_product_main_image,
                              create_flow,
                              create_flow_field,
                              create_flow_entry)


def main():
    load_dotenv()

    with open('menu.json', 'r', encoding='utf-8') as menu_file:
        products = json.load(menu_file)
    image_directory = Path('./images')
    Path.mkdir(image_directory, exist_ok=True)
    for product in products:
        product_id = create_product(product)
        image_url = product['product_image']['url']
        image_id = create_image(image_url)
        set_product_main_image(product_id, image_id)

    pizzerias_flow_id = create_flow(
        'pizzerias',
        'pizzerias addresses and geolocation'
    )
    pizzerias_flow_fields = [
        {
            'name': 'alias',
            'description': 'pizzeria name',
            'type': 'string'
        },
        {
            'name': 'address',
            'description': 'pizzeria address',
            'type': 'string'
        },
        {
            'name': 'lon',
            'description': 'longitude',
            'type': 'float'
        },
        {
            'name': 'lat',
            'description': 'latitude',
            'type': 'float'
        },
        {
            'name': 'delivery_chat_id',
            'description': 'chat id for delivery notifications',
            'type': 'integer'
        }
    ]
    for field in pizzerias_flow_fields:
        create_flow_field(pizzerias_flow_id, field)

    with open('addresses.json', 'r', encoding='utf-8') as addresses_file:
        pizzerias = json.load(addresses_file)
    for pizzeria in pizzerias:
        flow_fields = {
            'alias': pizzeria['alias'],
            'address': pizzeria['address']['full'],
            'lon': float(pizzeria['coordinates']['lon']),
            'lat': float(pizzeria['coordinates']['lat']),
            'delivery_chat_id': 30952486
        }
        create_flow_entry('pizzerias', flow_fields)

    customers_flow_id = create_flow(
        'Customers',
        'Extends the default customer model'
    )
    customer_fields = [
        {
            'name': 'lon',
            'description': 'customer location longitude',
            'type': 'float'
        },
        {
            'name': 'lat',
            'description': 'customer location latitude',
            'type': 'float'
        }
    ]
    for field in customer_fields:
        create_flow_field(customers_flow_id, field)


if __name__ == '__main__':
    main()
