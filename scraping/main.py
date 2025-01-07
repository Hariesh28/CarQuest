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

for url in urls:

    raw = fetch_data.get_raw_data(url=url)
    variants = fetch_data.get_all_variants(raw_data=raw)
    fetch_data.delay()

    for variant in variants[:7]:

        raw_variant = fetch_data.get_raw_data(url=variant)
        variant_data = fetch_data.get_variant_data(raw_data=raw_variant)

        variant_data['url'] = variant

        all_data.append(variant_data)

        fetch_data.delay()


with open(OUTPUT_FILE, mode='w', newline='', encoding='utf-8') as file:

    normalized_data = fetch_data.normalize_data(data=all_data)
    fieldnames = list(normalized_data[0].keys()) if normalized_data else []

    writer = csv.DictWriter(file, fieldnames=fieldnames)

    writer.writeheader()

    writer.writerows(fetch_data.normalize_data(data=all_data))

print(f"Data written to {OUTPUT_FILE} successfully!")
