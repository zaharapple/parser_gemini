import csv
import re
import argparse
import logging
from datetime import datetime
import bs4
import requests
from tqdm import tqdm
from .settings import TITLES_CSV, CATEGORY_MAP, SEARCH_TAGS, CHANGES_PRICE, prom_category_mappings

EXCLUDE_PRODUCT_CODES = ('TB-0001', 'TB-0002')
CODES_UP_PRICE = ('GB-016-10-B', 'GB-016-10-kh', 'GB-0162-14-BW')

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class GeminiParserXML:
    only_english = re.compile(r'[^a-zA-Z0-9-_]')

    def __init__(self, main_url, multiplier):
        self.main_url = main_url
        self.multiplier = multiplier
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/94.0.4606.81 Safari/537.36'}

    def _get_products(self):
        try:
            with requests.Session() as session:
                response = session.get(self.main_url)
                soup = bs4.BeautifulSoup(response.text, 'lxml')
                return soup.find_all('offer')
        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching products: {e}")
            return []

    def _parse_products(self, products):
        data_list = []

        for product in tqdm(products, desc="Parsing products"):
            code = product.find('vendorcode').text.split()[-1]

            if code in EXCLUDE_PRODUCT_CODES:
                continue

            params = {param.get('name'): param.get_text() for param in product.find_all('param')}
            images = [picture.get_text() for picture in product.find_all('picture')][:10]
            link = product.find('url').text
            category_name = link.split('/')[3]
            id_group = CATEGORY_MAP.get(category_name) or ''

            in_stock = '!' if product['in_stock'] == 'true' else '-'
            price = round(float(product.find('price').text) * self.multiplier)
            rounded_price = str(price + (5 - price % 5) % 5)
            change_price = CHANGES_PRICE.get(code)

            if change_price:
                logger.info(f'Change prices: {code}: {price} >> {change_price}')

            if int(rounded_price) <= 0:
                continue

            data_list.append({
                'Product_Code': code,
                'Item_Name': product.find('name').text,
                'Item_Name_Ukr': product.find('name').text,
                'Search_Queries': ', '.join(SEARCH_TAGS),
                'Search_Queries_Ukr': ', '.join(SEARCH_TAGS),
                'Description': product.find('name').text,
                'Description_Ukr': product.find('name').text,
                'Product_Type': 'r',
                'Price': change_price or rounded_price,
                'Price_From': None,
                'Currency': 'UAH',
                'Unit_of_Measurement': 'pcs',
                'Image_Link': ', '.join(images),
                'Weight_kg': params.get('Weight'),
                'Width_cm': params.get('Width'),
                'Height_cm': params.get('Height'),
                'Length_cm': params.get('Length'),
                'Availability': in_stock,
                'Country_of_Origin': params.get('Country of Origin'),
                'Group_Number': id_group,
                'Subdivision_Link': prom_category_mappings.get(product.find('categoryid').text, ''),
                'Product_Identifier': product['id'],
                'Unique_Identifier': product['id'],
            })

        return data_list

    def parsing(self):
        products = self._get_products()
        file_name = f'GEMINI_{datetime.now().strftime("%d_%b_%Y")}'
        data_list = self._parse_products(products)

        with open(f'{file_name}.csv', 'w', encoding='UTF8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=TITLES_CSV)
            writer.writeheader()
            writer.writerows(data_list)


def main():
    parser = argparse.ArgumentParser(description="Parse Gemini XML products.")
    parser.add_argument('main_url', type=str, help='The main URL of the XML file to parse.')
    parser.add_argument('--multiplier', type=float, default=1.10, help='Multiplier for the price calculation (default: 1.10).')
    args = parser.parse_args()

    gemini = GeminiParserXML(main_url=args.main_url, multiplier=args.multiplier)
    gemini.parsing()


if __name__ == '__main__':
    main()
