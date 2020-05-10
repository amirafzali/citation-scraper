# -*- coding: utf-8 -*-

'''
    AMIR AFZALI - 2019
'''

from bs4 import BeautifulSoup
import requests
import dateparser
import re
import json
from functools import reduce
from itertools import product


def get_formatted_author_name(name: str) -> dict:
    default = {'firstName': '', 'middleName': '', 'lastName': '', 'fullName': ''}

    if len(name.strip()) == 0: return default

    to_use = name.split(',')[0]
    name_split = to_use.split(' ')
    first = middle = last = ''

    if len(name_split) == 1:
        first = name_split[0]
    elif len(name_split) == 2:
        first, last = name_split
    elif len(name_split) == 3:
        first,middle,last = name_split
    
    return {'firstName': first, 'middleName': middle, 'lastName': last, 'fullName': to_use}

def try_schema(soup: "BeautifulSoup"):
    data = soup.select_one("script[type*=json]")
    json_map = {'website': '', 'publisher': '', 'headline': '', 'authors': [], 'published': {'day': '', 'month': '', 'year': ''}}
    
    if data and data.string:
        json_data = json.loads(data.string)

        site = soup.select_one('meta[property*="og:site_name"]')

        if not "@context" in json_data: return json_map

        if 'headline' in json_data: 
            json_map['headline'] = json_data['headline']

        if 'publisher' in json_data and 'name' in json_data['publisher']:
            json_map['publisher'] = json_data['publisher']['name']

        if site and 'content' in site:
            json_map['website'] = site['content']

        if 'author' in json_data:
            if type(json_data['author']) == list:
                for elm in json_data['author']:
                    author = json_data['author']['name']
                    if author: json_map['authors'].append(get_formatted_author_name(author))
            else:
                author = json_data['author']['name']
                if author: json_map['authors'].append(get_formatted_author_name(author))

        if 'datePublished' in json_data:
            parsed = dateparser.parse(json_data['datePublished'])
            if parsed:
                date = parsed.strftime('%d %B %Y')
                day, month, year = date.split(" ")
                json_map['published'] = {'day': day, 'month': month, 'year': year}

    print(json_map)

def grab_article_title(soup: "BeautifulSoup") -> str:

    metas = [["name", "citation_title"], ["property", "title"]]
    manual = ["title", "h1"]

    # Meta Tag Check
    for combo in metas:
        f1, f2 = combo
        meta = soup.select_one(f'meta[{f1}*={f2}]')
        if meta and meta['content']:
            return meta['content']

    # Manual Scrapes
    for tag in manual:
        if soup.find(tag): return soup[tag].string

    return "No article title found!"



def grab_author(soup: "BeautifulSoup") -> str:

    atr = ['name', 'rel', 'itemprop', 'class', 'id']
    val = ['author', 'byline', 'dc.creator', 'by', 'bioLink', "auths"]
    checks = ['meta', 'span', 'a', 'div']

    secondary = ["profile","person","author","editor"]
    combinations = list(product(atr,val,checks))


    # Multiple authors check with meta tag
    if(soup.select_one('meta[name*=citation_authors]')):
        return soup.select_one('meta[name*=citation_authors]')['content']

    if(soup.select_one('meta[name*=citation_author]')):
        meta = soup.select('meta[name=citation_author]')
        authors = ""
        for author in meta:
            authors += f"{author['content']}, "
        return authors


    # Single author check
    meta = soup.select_one('meta[name*=author]')
    if meta and meta['content']:
        return meta['content']


    for comb in combinations:
        attribute, value, check = comb
        for each in soup.select(check+'['+attribute+'*="'+value+'"]'):
            if each.string:
                return authenticate(cleanse(each.string, "author"), "author")
            for link in secondary:
                if each.select_one(f"a[href*={link}]") and each.select_one(f"a[href*={link}]").string:
                    return authenticate(cleanse(each.select_one(f"a[href*={link}]").string, "author"), "author")

    return "No author name found!"


def grab_publish_date(soup: "BeautifulSoup") -> str:
    atr = ['name', 'rel', 'itemprop', 'class', 'id']
    val = ['date', 'time', 'pub']
    checks = ['span', 'div', 'p', 'time']
    manual_combos = [atr,val,checks]

    meta_scrapes = [["property", "name"], ["published","time","content","date"]]
    meta_combos = product(*meta_scrapes)

    dates = []
    

    # Try to grab from meta data
    for combo in meta_combos:
        attr, val = combo
        meta = soup.select_one(f'meta[{attr}*={val}]')
        if meta and meta['content']:
            if parse_date(meta['content']) != 'Issue scraping date!': return parse_date(cleanse(meta['content'], "date"))

    if soup.select_one('time') and soup.select_one('time').has_attr('datetime'):
        return cleanse(parse_date(soup.select_one('time')['datetime']), "date")

    for attribute in atr:
        for value in val:
            for check in checks:
                for each in soup.select(check+'['+attribute+'*="' + value + '"]'):
                    if each.get('class') and ('pub' in each.get('class') or 'pubdate' in each.get('class')):
                        return parse_date(cleanse(each.string, "date"))
                    if each.get('itemprop') and each.get('itemprop') == 'datePublished':
                        return parse_date(cleanse(each.string, "date"))
                    if each.get('datetime'):
                        return parse_date(cleanse(each['datetime'], "date"))
                    if each.string:
                        if "Published:" in each.string or "Posted:" in each.string:
                            parse_date(cleanse(each.string, "date"))
    return "No date found!"


def grab_publisher(soup: "BeautifulSoup") -> str:
    atr = ['name', 'rel', 'itemprop', 'class', 'id']
    val = ['publisher', 'copyright', ]
    checks = ['span', 'div', 'p', 'a', 'li']

    meta = soup.select_one('meta[name*=publisher]')
    if meta and meta['content']:
        return process(meta['content'], "publisher")
    meta = soup.select_one('meta[name*=copyright]')
    if meta and meta['content']:
        return process(meta['content'], "publisher")

    for attribute in atr:
        for value in val:
            for check in checks:
                area = soup.find('footer')
                if area:
                    for each in area.select(check+'['+attribute+'*="'+value+'"]'):
                        if each.string:
                            return process(each.string, "publisher")
                for each in soup.select(check + '[' + attribute + '*="Organization"]'):
                    for each2 in each.select("span"):
                        if each2.string:
                            return process(each2.string, "publisher")
                for each in soup.select(check + '[' + attribute + '*="footer"]'):
                    for each2 in each.select('p[' + attribute + '*="copyright"]'):
                        if each2.stripped_strings:
                            pub = list(each2.stripped_strings)[0]
                            return process(pub, "publisher")

    scope = soup.find_all(text='©')
    print(scope)
    if scope:
        return process(scope[0], "publisher")

    return "No publisher found!"


def grab_website(soup: "BeautifulSoup") -> str:
    meta = soup.select_one('meta[property*="og:site_name"]')
    if meta and meta['content']:
        return meta['content']
    return "No website name found!"


def process(line: str, ptype: str) -> str:
    return authenticate(cleanse(line, ptype), ptype)


def cleanse(line: str, ptype: str) -> str:

    clears = {"author": ["By"], "date": ["Published", "Updated"], "publisher": ["All rights reserved", ".", "©", "Copyright",
                   "(c)", "Part of"]}

    if not ptype in clears: return "Parsing error."

    for regex in clears[ptype]:
        line = line.replace(regex, "")
    line = re.sub('\d{4}', '', line).strip()

    if line.strip() == "": return 'Parsing error.'

    return line.strip()


def authenticate(line: str, ptype: str) -> str:
    if len(line) == 0:
        return f"Error retrieving {ptype} !"
    if ptype == "author" or ptype == "publisher":
        if 4 < len(line) < 45:
            return line
        else:
            return ""  # "(Possible " + type + ") " + line
    return line


def parse_date(date: str) -> str:
    print('date:',date)
    parsed = dateparser.parse(date)
    try:
        return parsed.strftime('%d %B, %Y')
    except:
        return "Issue scraping date!"

def valid_date(date: str) -> bool:
    return not not dateparser.parse(date)


def prepare_JSON(website, publisher, article, first_name, middle_name, lastName, day, month, year):
    return {'website': website, 'publisher': publisher, 'article': article, 'firstName': first_name,
            'middleName': middle_name, 'lastName': lastName, 'day': day, 'month': month, 'year': year}


def output_JSON(website, publisher, article, author, date):

    name = author.split(" ")
    split_date = date.replace(",", "").split(" ")
    day = month = year = ""
    first_name = last_name = middle_name = ""

    if len(split_date) == 3:
        day, month, year = split_date
    elif len(split_date) == 2:
        month, year = split_date
    elif len(split_date) == 1:
        year = split_date[0]

    if len(name) == 3:
        first_name, middle_name, last_name = name
    elif len(name) >= 2:
        first_name, last_name = name[0], name[1]



    return prepare_JSON(website,
                       publisher,
                       article,
                       first_name,
                       middle_name,
                       last_name,
                       day,
                       month,
                       year)


def sanitize_url(url: str) -> str:
    url = url.replace(" ", "")
    prefix = "http://" if not url.startswith("http://") and not url.startswith("https://") else ""
    return prefix+url

def get_sitation_fields(res):
    page_content = res.content
    soup = BeautifulSoup(page_content, "lxml")

    try_schema(soup)

    website_name = grab_website(soup).strip()
    publisher = grab_publisher(soup).strip()
    article = grab_article_title(soup).strip()
    authors = grab_author(soup).strip()
    date = grab_publish_date(soup).strip()

    return [website_name, publisher, article, authors, date]

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

    website_name, publisher, article, authors, date = get_sitation_fields(result)
    print("Website: " + website_name)
    print("Publisher: " + publisher)
    print("Article Title: " + article)
    print("Author Name: " + authors)
    print("Date: " + date)
    print(output_JSON(website_name, publisher, article, authors, date))

main()