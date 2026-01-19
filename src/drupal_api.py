import os
import requests
from requests.auth import HTTPBasicAuth
import pandas as pd


## Getting enviroment variables
domain = os.getenv('DOMAIN')
username = os.getenv('DRUPAL_USER')
password = os.getenv('DRUPAL_PW')

headers = {
    "Accept": "application/vnd.api+json",
    "Content-Type": "application/vnd.api+json"
}


def get_drupal_commerce_orders(parameters=None, order_type="physical"):

    if not parameters:
        parameters = {
            "include": "uid,billing_profile,shipments,order_items",
            f"fields[commerce_order--{order_type}]": "order_number,total_price,state,created,shipments,order_items,billing_profile,billing_profile",
            f"fields[commerce_order_item--{order_type}_product_variation]":"title,quantity,total_price",
            "fields[commerce_order_item--default]":"order_number,order_items",
            "fields[commerce_shipment--default]":"items",
            "filter[state-filter][condition][path]":"state",
            "filter[state-filter][condition][operator]":"NOT IN",
            "filter[state-filter][condition][value][]":"draft"
        }

    endpoint = f'{domain}jsonapi/commerce_order/{order_type}'
    url = endpoint
    clean_data = []
    while url:
        try:
            response = requests.get(url, auth=HTTPBasicAuth(username, password), params=parameters, headers=headers)
            response.raise_for_status()
            data = response.json()

            # Process current page
            clean_data.extend(clean_orders_data(data))

            # Get next page URL, if exists
            url = data.get('links', {}).get('next', {}).get('href')

            # Once we follow the first page, subsequent pages already have params in URL
            parameters = None  

        except requests.exceptions.RequestException as e:
            print("Error:", e)
            break  # Stop looping on error
    results = pd.DataFrame(clean_data)
    results['date'] = pd.to_datetime(results['date'])
    results['order_total_price'] = results['order_total_price'].astype(float)
    results['item_total_price'] = results['item_total_price'].astype(float)
    results['quantity'] = pd.to_numeric(results['quantity'], errors='coerce').fillna(0).astype('int64')

    return results
    
def get_order_relationships(order):
    relationships = []
    if order.get('relationships'):
        for relationship_group in  order['relationships'].values():

            data = relationship_group.get('data')
            if not data:
                continue
            if isinstance(data, dict):

                data = [data]

            for relationship in data:

                if isinstance(relationship, dict):

                    r_type = relationship.get('type')   
                    r_id = relationship.get('id')

                    if r_type and r_id:
                        relationships.append(
                            {
                                'type': r_type,
                                'id': r_id
                            }
                        )

    return relationships
cleaned_data = []

def find_order_relationship(includes, r_id, r_type):

    for relationship in includes:
        if relationship.get('type') == r_type and relationship.get('id') == r_id:
            return relationship.get('attributes')
    
    return {}

def clean_orders_data(data):

    for order in data['data']:
        order_clean = {
            "order_id" : order.get('id'),
            "order_number": order['attributes'].get('order_number'),
            "date": order['attributes'].get('created'),
            "order_total_price": (
                                    order.get('attributes', {})
                                        .get('total_price', {})
                                        .get('number')
                                ),
            "currency": (
                        order.get('attributes', {})
                            .get('total_price', {})
                            .get('currency_code')
                        ),
            "status": order['attributes'].get('state'),
        }
        rel_objects = get_order_relationships(order)

        for relation in rel_objects:
            if relation.get('type') == 'profile--customer':
                rel_data = find_order_relationship(data['included'], relation.get('id'), 'profile--customer')
                if rel_data:
                    order_clean['destino'] = rel_data.get('field_destino')
                    order_clean['provincia'] =  rel_data.get('field_provincia')
                    order_clean['tanatorio'] = (
                            rel_data.get('field_tanatorios_barcelona') or
                            rel_data.get('field_tanatorios_girona') or
                            rel_data.get('field_tanatorios_la_rioja') or
                            rel_data.get('field_tanatorios_madrid') or
                            rel_data.get('field_tanatorios_tarragona')
                        )
        for relation in rel_objects:
            if relation.get('type') == 'commerce_order_item--physical_product_variation':
                rel_data = find_order_relationship(data['included'], relation.get('id'), 'commerce_order_item--physical_product_variation')
                if rel_data:
                    order_clean['item_name'] = rel_data.get('title')
                    order_clean['quantity'] = rel_data.get('quantity')
                    order_clean['item_total_price'] = rel_data['total_price'].get('number')
                cleaned_data.append(order_clean)

    return cleaned_data