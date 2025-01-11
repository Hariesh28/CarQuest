import os
import csv
import fetch_data

OUTPUT_DIR = os.path.join("data")
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "car_details.csv")
URL_FILE = os.path.join(OUTPUT_DIR, "urls.txt")

os.makedirs(OUTPUT_DIR, exist_ok=True)

def load_urls(file_path):
    with open(file_path, 'r') as file:
        return [line.strip() for line in file if line.strip()]

urls = load_urls(URL_FILE)

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

    for variant in variants:

        total_urls += 1

        try:
            raw_variant = fetch_data.get_raw_data(url=variant)
        except Exception as e:
            print(f"Error fetching raw data for variant {variant}: {e}")
            raw_variant = None

        try:
            if raw_variant:
                variant_data = fetch_data.get_variant_data(raw_data=raw_variant)
                variant_data['url'] = variant
            else:
                variant_data = {}
        except Exception as e:
            print(f"Error extracting variant data for {variant}: {e}")
            variant_data = {}

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
