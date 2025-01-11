import json
import time
import random
import requests
from bs4 import BeautifulSoup

BASE_URL = "https://www.cardekho.com/overview/"
URL_EXTENSION = '.htm'

user_agents = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.0 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Linux; Android 10; SM-A505F) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Mobile Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/109.0",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.5359.125 Safari/537.36",
    "Mozilla/5.0 (Linux; Android 11; SM-G981B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.45 Mobile Safari/537.36",
    "Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36",
    "Mozilla/5.0 (iPad; CPU OS 15_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.0 Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:85.0) Gecko/20100101 Firefox/85.0",
    "Mozilla/5.0 (Linux; Android 8.0.0; Nexus 5X) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/62.0.3202.84 Mobile Safari/537.36",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 12_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 Safari/604.1",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; Trident/7.0; rv:11.0) like Gecko",
    "Mozilla/5.0 (X11; Linux i686; rv:45.0) Gecko/20100101 Firefox/45.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.10; rv:91.0) Gecko/20100101 Firefox/91.0",
    "Mozilla/5.0 (iPhone; CPU iPhone OS 11_4_1 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/11.0 Mobile/15E148 Safari/604.1",
]

def get_raw_data(url: str) -> dict | None:

    try:
        headers = {
            "User-Agent": random.choice(user_agents)
        }

        response = requests.get(url, headers=headers, timeout=10)

        if response.status_code == 200:
            print(f"Request {url} successful!")

        else:
            print(f"Request {url} failed with status code: {response.status_code}")

    except requests.exceptions.RequestException as e:
        print(f"Error during request {url}: {e}")

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
            print(f'JSON is malformed or incomplete: {url}')
            raw_data = None

        except Exception as e:
            print(f'Unexpected Error in {url}: {e}')
            raw_data = None

    else:
        print(f'No script found with specified content: {url}')
        raw_data = None

    return raw_data


def get_all_variants(raw_data: dict) -> list[str] | None:

    all_urls = []

    try:
        data = raw_data['variantTable']['variantList']

    except (KeyError, TypeError) as e:
        print(e)
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
