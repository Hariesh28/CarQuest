import os
import csv
import time
import fetch_data

start_time = time.time()

OUTPUT_DIR = os.path.join("data")
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "car_details.csv")
URL_FILE = os.path.join(OUTPUT_DIR, "urls.txt")
ERROR_URLS = os.path.join(OUTPUT_DIR, "error_urls.csv")
BUFFER_SIZE = 1_000

os.makedirs(OUTPUT_DIR, exist_ok=True)

def load_urls(file_path):
    with open(file_path, 'r') as file:
        return [line.strip() for line in file if line.strip()]

urls = load_urls(URL_FILE)
total_models_count = len(urls)

buffer = []

processed_model_urls = 0
failed_model_urls = 0
total_urls = 0
total_failed_urls = 0

failed_urls = []

with open(OUTPUT_FILE, mode='w', newline='', encoding='utf-8') as file:

    writer = None

    for url in urls:

        processed_variant_urls = 0
        failed_variant_urls = 0
        processed_model_urls += 1

        os.system('cls')
        print(f'Processing Car Model: {processed_model_urls}/{total_models_count} ({processed_model_urls/total_models_count*100:.2f}%) Failed Car Models: {failed_model_urls} ({failed_model_urls/total_models_count*100:.2f}%)')

        try:
            raw = fetch_data.get_raw_data(url=url)
            variants = fetch_data.get_all_variants(raw_data=raw)
            fetch_data.delay()

        except Exception as e:
            failed_model_urls += 1
            total_failed_urls += 1
            failed_urls.append({'url' : url, 'type' : 'model', 'cause' : e})
            variants = []

        if variants is None: variants = []

        total_variants = len(variants)

        for variant in variants:

            processed_variant_urls += 1
            total_urls += 1

            try:
                raw_variant = fetch_data.get_raw_data(url=variant)
            except Exception as e:
                failed_variant_urls += 1
                total_failed_urls += 1
                failed_urls.append({'url' : variant, 'type' : 'variant', 'cause' : e})
                raw_variant = None
                fetch_data.delay()
                print(f'Processed Variants {processed_variant_urls}/{total_variants} ({processed_variant_urls/total_variants*100:.2f}%) Failed Variants: {failed_variant_urls} ({failed_variant_urls/total_variants*100:.2f}%)', end='\r')
                continue

            try:
                if raw_variant:
                    variant_data = fetch_data.get_variant_data(raw_data=raw_variant)
                    variant_data['url'] = variant
                else:
                    variant_data = {}
            except Exception as e:
                failed_variant_urls += 1
                total_failed_urls += 1
                failed_urls.append({'url' : variant, 'type' : 'variant', 'cause' : e})
                variant_data = {}

            if variant_data:
                buffer.append(variant_data)

            print(f'Processed Variants {processed_variant_urls}/{total_variants} ({processed_variant_urls/total_variants*100:.2f}%) Failed Variants: {failed_variant_urls} ({failed_variant_urls/total_variants*100:.2f}%)', end='\r')


    normalized_data = fetch_data.normalize_data(data=buffer)

    if normalized_data:
        fieldnames = list(normalized_data[0].keys())

        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()

        for i in range(0, len(normalized_data), BUFFER_SIZE):

            writer.writerows(normalized_data[i:i+BUFFER_SIZE])
            print(f"Written rows {i} to {min(i + BUFFER_SIZE, len(normalized_data))}...")


    buffer.clear()

with open(ERROR_URLS, mode='w', newline='', encoding='utf-8') as file:

    writer = csv.DictWriter(file, fieldnames=['url', 'type', 'cause'])
    writer.writeheader()
    writer.writerows(failed_urls)

os.system('cls')
print(f'Data written to {OUTPUT_FILE} successfully!')
print(f'Total Number of Models Processed: {total_models_count}')
print(f'Total Number of urls Processed: {total_urls}')
print(f'Total Number of failed urls: {total_failed_urls}')
print(f'Success Rate: {(total_urls-total_failed_urls)/total_urls*100:.3f}%')

elapsed_time = time.time() - start_time

hours = int(elapsed_time // 3600)
minutes = int((elapsed_time % 3600) // 60)
seconds = int(elapsed_time % 60)

print(f"Total time taken: {hours} hrs : {minutes} mins : {seconds} secs")
