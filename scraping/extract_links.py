import requests
import random
import os
import time
from bs4 import BeautifulSoup

def extract_and_process_links(
    html_file: str, 
    base_url: str, 
    intermediate_file: str, 
    output_file: str, 
    num_links: int, 
    user_agents: list
) -> None:
    """
    Extracts links from an HTML file, appends a base URL, fetches more links from those URLs, 
    and saves all results to output files.
    
    Args:
        html_file (str): The path to the HTML file containing links.
        base_url (str): The base URL to prepend to the extracted links.
        intermediate_file (str): The file where intermediate formatted URLs will be saved.
        output_file (str): The file where final fetched links will be saved.
        num_links (int): The number of links to process from the HTML file.
        user_agents (list): A list of user-agent strings to use for requests.
    """
    def delay() -> None:
        """Introduces a random delay to mimic human behavior."""
        time.sleep(random.uniform(2, 5))
    
    def get_links_from_url(url: str) -> list:
        """Fetches and extracts links from the given URL."""
        try:
            headers = {"User-Agent": random.choice(user_agents)}
            response = requests.get(url, headers=headers, timeout=10)
            delay()

            if response.status_code == 200:
                print(f"Request to {url} successful!")
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Find all <li> elements with the specified class
                list_items = soup.find_all('li', class_="gsc_col-xs-12 gsc_col-sm-6 gsc_col-md-12 gsc_col-lg-12")
                links = []

                # Extract links from the <a> tags within these list items
                for item in list_items:
                    a_tag = item.find('a', href=True)
                    if a_tag:
                        links.append(a_tag['href'])

                return links
            else:
                print(f"Request to {url} failed with status code: {response.status_code}")
                return []
        except requests.exceptions.RequestException as e:
            print(f"Error during request to {url}: {e}")
            return []
    
    # Step 1: Extract links from the HTML file
    with open(html_file, 'r', encoding='utf-8') as file:
        html_text = file.read()
    
    soup = BeautifulSoup(html_text, 'html.parser')
    raw_links = [a['href'] for a in soup.find_all('a', href=True)]
    formatted_urls = [f"{base_url}{raw_links[i]}" for i in range(min(num_links, len(raw_links)))]
    
    # Step 2: Save intermediate formatted URLs to a file
    with open(intermediate_file, "w", encoding="utf-8") as file:
        for url in formatted_urls:
            file.write(url + "\n")
    
    print(f"Intermediate formatted URLs saved to {intermediate_file}")
    
    # Step 3: Fetch additional links from intermediate URLs
    all_links = []
    for url in formatted_urls:
        print(f"Processing {url}")
        links = get_links_from_url(url)
        all_links.extend(links)
    
    # Step 4: Save final extracted links to the output file
    with open(output_file, "w", encoding="utf-8") as file:
        for link in all_links:
            file.write(link + "\n")

    os.remove(intermediate_file)    
    print(f"Final extracted links saved to {output_file}")

# Example usage
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


extract_and_process_links(
    html_file="data/html_selected.html",
    base_url="https://cardekho.com",
    intermediate_file="data/urls_intermediate.txt",
    output_file="data/urls.txt",
    num_links=75,
    user_agents=user_agents
)
