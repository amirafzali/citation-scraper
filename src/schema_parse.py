from bs4 import BeautifulSoup
import dateparser
import json

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
    data = soup.select("script[type*=json]")
    json_map = {'website': '', 'publisher': '', 'headline': '', 'authors': [], 'published': {'day': '', 'month': '', 'year': ''}}
    to_return = {'status': False, 'data': json_map}
    
    site = soup.select_one('meta[property*="og:site_name"]')
    
    def schem_iteration(json_data):
        if 'headline' in json_data: 
            json_map['headline'] = json_data['headline']

        if 'publisher' in json_data and 'name' in json_data['publisher']:
            json_map['publisher'] = json_data['publisher']['name']

        if site and site['content']:
            json_map['website'] = site['content']

        if 'author' in json_data:
            authorTag = json_data['author']
            if type(authorTag) == list:
                for elm in authorTag:
                    if type(elm) == str:
                        json_map['authors'].append(get_formatted_author_name(elm))
                    elif 'name' in elm: 
                        json_map['authors'].append(get_formatted_author_name(elm['name']))
            else:
                author = 'name' in authorTag and authorTag['name']
                if author: json_map['authors'].append(get_formatted_author_name(author))

        if 'datePublished' in json_data:
            parsed = dateparser.parse(json_data['datePublished'])
            if parsed:
                date = parsed.strftime('%d %B %Y')
                day, month, year = date.split(" ")
                json_map['published'] = {'day': day, 'month': month, 'year': year}

    for inst in data:
        if not inst.string: continue

        json_data = json.loads(inst.string)
        print(json.dumps(json_data, indent=4, sort_keys=True))

        if not "@context" in json_data and not "@type" in json_data: return to_return

        schem_iteration(json_data)
        if '@graph' in json_data: [schem_iteration(elm) for elm in json_data['@graph']]
        
        to_return['status'] = True

    to_return['data'] = json_map
    return to_return