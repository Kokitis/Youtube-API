"""
	Widgets pertaining to common operations to perform on the personal channel.
"""
from typing import Dict
from pathlib import Path
from pprint import pprint
from bs4 import BeautifulSoup
import re
def import_subscriptions(path: Path)->Dict[str,str]:
	"""
		Imports all subscriptions using the html page when using ImprovedTube.
	Parameters
	----------
	path: Path
		The html file.
	"""
	pattern = "href=\"/channel/(?P<id>.+)\"[\s]+title=\"(?P<title>.+)\"[\s]"
	regex = re.compile(pattern)
	contents = path.read_text()
	soup = BeautifulSoup(contents, 'lxml')

	result = soup.find_all(regex)
	result = regex.findall(contents)
	pprint(result)


if __name__ == "__main__":
	filename = Path.home() / "Documents" / "GitHub" / "Subscriptions - YouTube.html"
	import_subscriptions(filename)