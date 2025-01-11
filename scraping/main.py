import os
import csv
import fetch_data

OUTPUT_DIR = os.path.join("data")
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "car_details.csv")

urls = [
    'https://www.cardekho.com/tata/nexon',
    'https://www.cardekho.com/carmodels/Toyota/Toyota_Fortuner'
]

all_data = []
total_urls = 0

for url in urls:

    try:
        raw = fetch_data.get_raw_data(url=url)
        variants = fetch_data.get_all_variants(raw_data=raw)
        fetch_data.delay()

    except Exception as e:
        print(f"Error fetching data for URL {url}: {e}")
        variants = []

    for variant in variants[:7]:

        total_urls += 1

        try:
            raw_variant = fetch_data.get_raw_data(url=variant)
        except Exception as e:
            print(f"Error fetching raw data for variant {variant}: {e}")
            raw_variant = None

        variant_data['url'] = variant

        if variant_data:
            all_data.append(variant_data)

        fetch_data.delay()


with open(OUTPUT_FILE, mode='w', newline='', encoding='utf-8') as file:

    normalized_data = fetch_data.normalize_data(data=all_data)
    fieldnames = list(normalized_data[0].keys()) if normalized_data else []

    writer = csv.DictWriter(file, fieldnames=fieldnames)

    writer.writeheader()

    writer.writerows(fetch_data.normalize_data(data=all_data))

print(f"Data written to {OUTPUT_FILE} successfully!")
print(f'Tried {total_urls}, found {len(all_data)}')
