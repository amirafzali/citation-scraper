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


def check_article_title(soup):
    # Meta Tag Check
    meta = soup.select_one('meta[name*=citation_title]')
    if meta and meta['content']:
        return meta['content']

    meta = soup.select_one('meta[property*=title]')
    if meta and meta['content']:
        return meta['content']

    # Manual Scrapes
    elif soup.find("title"):
        return soup.title.string
    elif soup.find("h1"):
        return soup.h1.string

    return "No article title found!"


def check_author(soup):
    atr = ['name', 'rel', 'itemprop', 'class', 'id']
    val = ['author', 'byline', 'dc.creator', 'by', 'bioLink', "auths"]
    checks = ['meta', 'span', 'a', 'div']

    if(soup.select_one('meta[name*=citation_author]')):
        meta = soup.select('meta[name=citation_author]')
        authors = ""
        for author in meta:
            authors += f"{author['content']}, "
        return authors

    meta = soup.select_one('meta[name*=author]')
    # print(metaCheck)
    if meta and meta['content']:
        return meta['content']

    for attribute in atr:
        for value in val:
            for check in checks:
                for each in soup.select(check+'['+attribute+'*="'+value+'"]'):
                    if each.string:
                        return authenticate(cleanse(each.string, "author"), "author")
                    if each.select_one("a[href*=profile]") and each.select_one("a[href*=profile]").string:
                        return authenticate(cleanse(each.select_one("a[href*=profile]").string, "author"), "author")
                    if each.select_one("a[href*=person]") and each.select_one("a[href*=person]").string:
                        return authenticate(cleanse(each.select_one("a[href*=person]").string, "author"), "author")
                    if each.select_one("a[href*=author]") and each.select_one("a[href*=author]").string:
                        return authenticate(cleanse(each.select_one("a[href*=author]").string, "author"), "author")
                    if each.select_one("a[href*=editor]") and each.select_one("a[href*=editor]").string:
                        return authenticate(cleanse(each.select_one("a[href*=editor]").string, "author"), "author")

    return "No author name found!"


def check_time(soup):
    atr = ['name', 'rel', 'itemprop', 'class', 'id']
    val = ['date', 'time', 'pub']
    checks = ['span', 'div', 'p', 'time']

    meta = soup.select_one('meta[property*=published]')
    if meta and meta['content']:
        return cleanse(parse_date(meta['content']), "date")

    meta = soup.select_one('meta[property*=time]')
    if meta and meta['content']:
        return cleanse(parse_date(meta['content']), "date")

    meta = soup.select_one('meta[name*=published]')
    if meta and meta['content']:
        return cleanse(parse_date(meta['content']), "date")

    meta = soup.select_one('meta[name*=date]')
    if meta and meta['content'] and not meta['name'].find('validate'):
        return cleanse(parse_date(meta['content']), "date")

    if soup.select_one('time') and soup.select_one('time').has_key('datetime'):
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


def check_publisher(soup):
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


def check_website(soup):
    meta = soup.select_one('meta[property*=og:site_name]')
    if meta and meta['content']:
        return meta['content']
    return "No website name found!"


def process(string, type):
    return authenticate(cleanse(string, type), type)


def cleanse(string, type):
    if type == "author":
        string = string.replace("By", " ")
        string = string.replace("by", " ")
    elif type == "date":
        string = string.replace("Published", "")
        string = string.replace("Updated", "")
    elif type == "publisher":
        replace = ["All rights reserved", ".", "©", "Copyright",
                   "copyright", "(c)", "Part of", "part of"]
        for criteria in replace:
            string = string.replace(criteria, "")
        string = re.sub('\d{4}', '', string).strip()
    if string.strip() == "":
        return 'Parsing error.'
    return string.strip()


def authenticate(string, type):
    if len(string) == 0:
        return "Error retrieving " + type + "!"
    if type == "author" or type == "publisher":
        if 4 < len(string) < 45:
            return string
        else:
            return ""  # "(Possible " + type + ") " + string
    return string


def parse_date(date):
    print(date)
    parsed = dateparser.parse(date)
    try:
        return parsed.strftime('%d %B, %Y')
    except:
        return "Issue scraping date!"


def prepareJSON(website, publisher, article, first_name, middle_name, lastName, day, month, year):
    dict = {'website': website, 'publisher': publisher, 'article': article, 'firstName': first_name,
            'middleName': middle_name, 'lastName': lastName, 'day': day, 'month': month, 'year': year}
    return json.dumps(dict)


def setupandprepare(website, publisher, article, author, date):
    name_dict = author.split(" ")
    date_dict = date.replace(",", "").split(" ")
    day = month = year = ""
    first_name = last_name = middle_name = ""
    if len(date_dict) == 3:
        day, month, year = date_dict
    elif len(date_dict) == 2:
        month = date_dict[1]
        year = date_dict[2]
    elif len(date_dict) == 1:
        year = date_dict[2]
    if len(name_dict) == 3:
        first_name, middle_name, last_name = name_dict
    elif len(name_dict) == 2:
        first_name = name_dict[0]
        last_name = name_dict[1]

    return prepareJSON(website,
                       publisher,
                       article,
                       first_name,
                       middle_name,
                       last_name,
                       day,
                       month,
                       year)


while True:
    URL = input("Please enter the website URL: ")
    try:
        headers = requests.utils.default_headers()
        headers.update({
            'User-Agent': 'Mozilla/5.0 (X11; Ubuntu; Linux x86_64;rv:52.0) Gecko/20100101 Firefox/52.0',
        })
        result = requests.get(URL.replace(" ", ""),
                              timeout=15.0, headers=headers)
        break
    except requests.exceptions.Timeout as e:
        print("\nRequest took over 15 seconds. Website down? Try again.\n\n")
    except requests.exceptions.MissingSchema as e:
        print("\nInvalid URL format. Did you forget http://?\n\n")
    except requests.exceptions.InvalidSchema as e:
        print("\nInvalid URL format. Did you forget http://?\n\n")
    except e:
        print('An error occured. Please restart tool.')

page_content = result.content
soup = BeautifulSoup(page_content, "lxml")
website_name = check_website(soup)
publisher = check_publisher(soup)
article = check_article_title(soup).strip()
authors = check_author(soup).strip()
date = check_time(soup).strip()
print("Website: " + website_name)
print("Publisher: " + publisher)
print("Article Title: " + article)
print("Author Name: " + authors)
print("Date: " + date)
print(setupandprepare(website_name, publisher, article, authors, date))
