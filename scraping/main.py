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
total_urls_count = len(urls)

buffer_size = 100
buffer = []
processed_urls_model = 0  # Counter to track the number of processed model URLs
 # Counter to track the number of processed  variant URLs
total_variants = 0  # Counter to track the total number of variants

# Open the output CSV file once and write incrementally
with open(OUTPUT_FILE, mode='w', newline='', encoding='utf-8') as file:
    writer = None  # Will be initialized after the first normalized data
    
    for url in urls:
        processed_urls_variant = 0 
        try:
            raw = fetch_data.get_raw_data(url=url)
            variants = fetch_data.get_all_variants(raw_data=raw)
            fetch_data.delay()
        except Exception as e:
            print(f"Error fetching data for URL {url}: {e}")
            variants = []

        total_urls_variants_count = len(variants)
        for variant in variants:
            total_variants += 1
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

            processed_urls_variant += 1
            if variant_data:
                print(f"Processed Variants {processed_urls_variant}/{total_urls_variants_count} URLs....")
                buffer.append(variant_data)

            # Write to the CSV file if buffer is full
            if len(buffer) >= buffer_size:
                normalized_data = fetch_data.normalize_data(data=buffer)
                if not writer and normalized_data:  # Initialize writer on first data batch
                    fieldnames = list(normalized_data[0].keys())
                    writer = csv.DictWriter(file, fieldnames=fieldnames)
                    writer.writeheader()
                if normalized_data:
                    writer.writerows(normalized_data)
                buffer.clear()  # Clear the buffer after writing

            fetch_data.delay()

        # Increment processed URLs and print progress
        processed_urls_model += 1
        print(f"Processed Models {processed_urls_model}/{total_urls_count} URLs....")

    # Write remaining data in buffer to the file
    if buffer:
        normalized_data = fetch_data.normalize_data(data=buffer)
        if not writer and normalized_data:  # Initialize writer if not already done
            fieldnames = list(normalized_data[0].keys())
            writer = csv.DictWriter(file, fieldnames=fieldnames)
            writer.writeheader()
        if normalized_data:
            writer.writerows(normalized_data)

print(f"Data written to {OUTPUT_FILE} successfully!")
print(f"Processed {processed_urls}/{total_urls_count} URLs.")
print(f"Tried {total_variants} variants, found {len(buffer)} in the last batch.")
