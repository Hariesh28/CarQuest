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

        url = BASE_URL + '_'.join(about_car['modelName'].split()) + '/' +'_'.join(about_car['carVariantId'].split()) + URL_EXTENSION

        all_urls.append(url)

    return all_urls

def delay() -> None:
    time.sleep(random.uniform(2, 5))

def get_variant_data(raw_data: dict) -> dict | None:

    # useful_data = {}

    # specs_data = raw_data['data']['specs']
    # useful_data.update(specs_data)

    # useful_data['params'] = raw_data['params']
    # useful_data['overView'] = raw_data['overView']
    # useful_data['Mileage'] = raw_data['data']['quickOverview']['keyAndFeatureList'][-2]
    # useful_data['color_text'] = raw_data['data']['variantHighlight']['description']
    # useful_data['otherCityPrice'] = raw_data['data']['priceOtherCityTable']['items'][0]
    # useful_data['dataLayer'] = raw_data['data']['dataLayer']

    data = {}
    dataLayer = raw_data['dataLayer'][0]
    data['brand'] = dataLayer['oemName']
    data['model'] = dataLayer['modelName']
    data['variant'] = dataLayer['variantName']
    data['type'] = dataLayer['vehicleSegment']
    data['price'] = dataLayer['price_segment']
    data['fuel'] = dataLayer['fuel_type']

    dataSpecs = raw_data['data']['specs']
    for item in dataSpecs['specification'][0]['items']:

        if item['text'] == 'Displacement':
            data['displacement'] = item['value']

        if item['text'] == 'Max Power':
            data['bhp'] = item['value']

        if item['text'] == 'Max Torque':
            data['torque'] = item['value']

        if item['text'] == 'No. of Cylinders':
            data['No. of Cylinders'] = item['value']

        if item['text'] == 'Transmission Type':
            data['Transmission'] = item['value']

        if item['text'] == 'Gearbox':
            data['Gearbox'] = item['value']

        if item['text'] == 'Drive Type':
            data['Drive Type'] = item['value']

    for item in dataSpecs['specification'][1]['items']:

        if 'mileage' in item['text'].lower():
            data['mileage'] = item['value']

        if 'capacity' in item['text'].lower():
            data['Fuel Tank Capacity'] = item['value']

    for item in dataSpecs['specification'][2]['items']:

        if item['text'] == 'Front Brake Type':
            data['Front Brake Type'] = item['value']

        if item['text'] == 'Rear Brake Type':
            data['Rear Brake Type'] = item['value']

    for item in dataSpecs['specification'][3]['items']:

        if item['text'] == 'Boot Space':
            data['Boot Space'] = item['value']

        if item['text'] == 'Seating Capacity':
            data['Seating Capacity'] = item['value']

        if 'ground clearance' in item['text'].lower():
            data['Ground Clearance'] = item['value']

        if item['text'] == 'Wheel Base':
            data['Wheel Base'] = item['value']

    print(data)
    return data
