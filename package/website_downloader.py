import bs4

import requests

url = "https://raw.gwarchives.com/reddit_user_legendarylootz/"

response = requests.get(url)
html_doc =response.text

from bs4 import BeautifulSoup
soup = BeautifulSoup(html_doc, 'html.parser')

print(soup.prettify())