from bs4 import BeautifulSoup
import dateparser
import json
import re
from itertools import product


def get_citation_fields(soup):

    website_name = grab_website(soup).strip()
    publisher = grab_publisher(soup).strip()
    article = grab_article_title(soup).strip()
    authors = grab_author(soup).strip()
    date = grab_publish_date(soup).strip()

    return [website_name, publisher, article, authors, date]

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

    return ""



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

    # Final way of trying to find some author... ugly but works
    for comb in combinations:
        attribute, value, check = comb
        for each in soup.select(check+'['+attribute+'*="'+value+'"]'):
            if each.string:
                return is_validfield(cleanse(each.string, "author"), "author")
            for link in secondary:
                if each.select_one(f"a[href*={link}]") and each.select_one(f"a[href*={link}]").string:
                    return is_validfield(cleanse(each.select_one(f"a[href*={link}]").string, "author"), "author")

    return ""


def grab_publish_date(soup: "BeautifulSoup") -> str:
    atr = ['name', 'rel', 'itemprop', 'class', 'id']
    val = ['date', 'time', 'pub']
    checks = ['span', 'div', 'p', 'time']
    meta_scrapes = [["property", "name"], ["published","time","content","date"]]

    manual_combos = product(atr,val,checks)
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

    for comb in manual_combos:
        attribute, value, check = comb
        for each in soup.select(check+'['+attribute+'*="' + value + '"]'):
            if each.get('class') and ('pub' in each.get('class') or 'pubdate' in each.get('class')):
                return parse_date(cleanse(each.string, "date"))
            elif each.get('itemprop') and each.get('itemprop') == 'datePublished':
                return parse_date(cleanse(each.string, "date"))
            elif each.get('datetime'):
                return parse_date(cleanse(each['datetime'], "date"))
            elif each.string and ("Published:" in each.string or "Posted:" in each.string):
                    parse_date(cleanse(each.string, "date"))

    return ""


def grab_publisher(soup: "BeautifulSoup") -> str:
    atr = ['name', 'rel', 'itemprop', 'class', 'id']
    val = ['publisher', 'copyright', ]
    checks = ['span', 'div', 'p', 'a', 'li']

    for meta in [soup.select_one('meta[name*=publisher]'), soup.select_one('meta[name*=copyright]')]:
        if meta and meta['content']:
            return process(meta['content'], "publisher")

    return ""

def grab_website(soup: "BeautifulSoup") -> str:
    meta = soup.select_one('meta[property*="og:site_name"]')
    if meta and meta['content']:
        return meta['content']
    return ""


def process(line: str, ptype: str) -> str:
    return is_validfield(cleanse(line, ptype), ptype)


def cleanse(line: str, ptype: str) -> str:
    clears = {"author": ["By", "More", "From"], "date": ["Published", "Updated"], 
                "publisher": ["All rights reserved", ".", "©", "Copyright", "(c)", "Part of"]}

    if not ptype in clears: return "Parsing error."

    for regex in clears[ptype]:
        line = line.replace(regex, "")
        line = line.replace(regex.lower(), "")

    line = re.sub('\d{4}', '', line).strip()

    return line.strip()


def is_validfield(line: str, ptype: str) -> str:
    if len(line) == 0:
        return ""

    if ptype == "author" or ptype == "publisher":
        if 4 < len(line) < 45:
            return line
        else:
            return ""

    return line


def parse_date(date: str) -> str:    
    try:
        parsed = dateparser.parse(date)
        
        return parsed.strftime('%d %B, %Y')
    except:
        print("Date parse issue detected")
        return ""

def is_date(date: str) -> bool:
    return not not dateparser.parse(date)

def output_JSON(website: str, publisher: str, article: str, author: str, date: str):
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



    return {'website': website, 'publisher': publisher, 'article': article, 'firstName': first_name,
            'middleName': middle_name, 'lastName': last_name, 'day': day, 'month': month, 'year': year}
