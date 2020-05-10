# -*- coding: utf-8 -*-
'''
    AMIR AFZALI - 2019-2020
'''

from bs4 import BeautifulSoup
import requests
import json
from schema_parse import try_schema
from manual_parse import get_citation_fields, output_JSON

def sanitize_url(url: str) -> str:
    url = url.replace(" ", "")
    prefix = "http://" if not url.startswith("http://") and not url.startswith("https://") else ""
    return prefix+url

def main():
    while True:

        URL = sanitize_url(input("Please enter the website URL: "))
        TIMEOUT = 15.0

        try:
            headers = requests.utils.default_headers()
            headers.update({
                'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64;rv:52.0) Gecko/20100101 Firefox/52.0',
            })
            result = requests.get(URL,
                                timeout=TIMEOUT, headers=headers)
            break

        except requests.exceptions.Timeout as e:
            print("\nRequest took over 15 seconds. Website down? Try again.\n\n")
        except requests.exceptions.MissingSchema as e:
            print("\nInvalid URL format")
        except requests.exceptions.InvalidSchema as e:
            print("\nInvalid URL format")
        except:
            print('An error occured. Please restart tool.')

    page_content = result.content
    soup = BeautifulSoup(page_content, "lxml")
    schema = try_schema(soup)
    
    if schema['status']:
        print(schema['data'])
    else:
        website_name, publisher, article, authors, date = get_citation_fields(soup)
        print("Website: " + website_name)
        print("Publisher: " + publisher)
        print("Article Title: " + article)
        print("Author Name: " + authors)
        print("Date: " + date)
        print(output_JSON(website_name, publisher, article, authors, date))

main()