import json
import time
import random
import requests
from bs4 import BeautifulSoup
from fake_useragent import UserAgent

BASE_URL = "https://www.cardekho.com/overview/"
URL_EXTENSION = '.htm'

user_agent = UserAgent()

def get_raw_data(url: str) -> dict | None:

    try:
        headers = {
            "User-Agent": user_agent.random
        }

        response = requests.get(url, headers=headers, timeout=10)

    except requests.exceptions.RequestException as e:
        pass

    soup = BeautifulSoup(response.text, 'html.parser')

    script_section = soup.find('script', string=lambda s: s and 'window.__INITIAL_STATE__' in s)

    if script_section and script_section.string:

        try:
            script_data = script_section.string.strip()

            if script_data.endswith('};'):
                script_data = script_data[:-2]
            elif script_data.endswith(';'):
                script_data = script_data[:-1]

            json_data = script_data.split('window.__INITIAL_STATE__ = ')[1]
            json_data = json_data.split('};')[0].strip() + '}'
            raw_data = json.loads(json_data)

        except json.JSONDecodeError:
            raw_data = None

        except Exception as e:
            raw_data = None

    else:
        raw_data = None

    return raw_data


def get_all_variants(raw_data: dict) -> list[str] | None:

    all_urls = []

    try:
        data = raw_data['variantTable']['variantList']

    except (KeyError, TypeError) as e:
        return

    for i in range(len(data)):

        try:
            about_car = data[i]['dcbDto']

        except (KeyError, TypeError):
            continue

        url = BASE_URL + '_'.join(about_car['modelName'].split()) + '/' + '_'.join(about_car['carVariantId'].split()) + URL_EXTENSION

        all_urls.append(url)

    return all_urls

def delay() -> None:
    time.sleep(random.uniform(2, 5))

def extract_data(params):

    data = {}

    for parm in params:

        for item in parm['items']:

            for key, value in parm['values'].items():

                if item['text'] == key:
                    data[value] = item['value']

                elif key.lower() in item['text'].lower():
                    data[value] = item['value']

    return data

def get_variant_data(raw_data: dict) -> dict | None:

    dataSpecs = raw_data['data']['specs']

    params = [
        {
            'items': dataSpecs['specification'][0]['items'],
            'values': {
                'Displacement': 'displacement',
                'Max Power': 'bhp',
                'Max Torque': 'torque',
                'No. of Cylinders': 'no_of_cylinders',
                'Transmission Type': 'transmission',
                'Gearbox': 'gearbox',
                'Drive Type': 'drive_type'
            },
        },

        {
            'items': dataSpecs['specification'][1]['items'],
            'values': {

                'mileage': 'mileage',
                'capacity': 'capacity'
            }
        },

        {
            'items': dataSpecs['specification'][2]['items'],
            'values': {
                'Front Brake Type': 'front_brake',
                'Rear Brake Type': 'rear_brake'
            }
        },

        {
            'items': dataSpecs['specification'][3]['items'],
            'values': {
                'Boot Space': 'boot_space',
                'Seating Capacity': 'seating_capacity',
                'ground clearance': 'ground_clearance',
                'Wheel Base': 'wheel_base',
                'Gross Weight': 'gross_weight'
            }
        },

        {
            'items': dataSpecs['featured'][0]['items'],
            'values': {
                'Cruise Control': 'cruise_control',
                'KeyLess Entry': 'keyLess_entry',
                'Engine Start/Stop Button': 'engine_start/stop_button',
                'Drive Modes': 'drive_modes',
                'Drive Mode Types': 'drive_mode_types',
                'Parking Sensors': 'parking_sensors'
            }
        },

        {
            'items': dataSpecs['featured'][2]['items'],
            'values': {
                'Tyre Size': 'tyre_size',
                'Tyre Type': 'tyre_type',
                'LED Headlamps': 'LED_headlamps'
            }
        },

        {
            'items': dataSpecs['featured'][3]['items'],
            'values': {
                'No. of Airbags': 'no_of_airbags',
                'Rear Camera': 'rear_camera',
                'Hill Assist': 'hill_assist',
                'Global NCAP Safety Rating': 'NCAP_rating',
                'Touchscreen': 'touchscreen',
                'Android Auto': 'android_auto'
            }
        }
    ]

    data = {}
    dataLayer = raw_data['dataLayer'][0]
    data['brand'] = dataLayer['oemName']
    data['model'] = dataLayer['modelName']
    data['variant'] = dataLayer['variantName']
    data['type'] = dataLayer['vehicleSegment']
    data['price'] = dataLayer['price_segment']
    data['fuel'] = dataLayer['fuel_type']

    data.update(extract_data(params))

    return data

def normalize_data(data:dict[list[dict[str:str]]]) -> dict[list[dict[str:str]]]:

    fieldnames = list({key for row in data for key in row.keys()})

    for row in data:
        for field in fieldnames:
            row.setdefault(field, None)

    return data
