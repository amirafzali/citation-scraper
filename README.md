# citation-scraper
A python3 script powered by BeautifulSoup4 that scrapes citation information from a given article/website.


The tool first attempts to retrieve information through meta tags and JSON data scripts, and then performs deeper searches to find missing fields.

The tool utilizes a tag priority system that assigns weights to parsed elements, depending on their likelyhood of being the correct citation field.

### Build Instructions

`pip3 install -r requirements.txt`

### Run instructions

`python3 src/citation.py`
