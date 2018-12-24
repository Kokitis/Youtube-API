from typing import Dict, List
from dataclasses import dataclass
from pytools import timetools

@dataclass
class PlaylistResource:
	resourceId: str
	resourceType: str
	itemId: str
	itemType: str

	channelId: str
	channelName: str

	description: str
	date: timetools.Timestamp
	language: str
	tags: List[str]
	itemCount: int


def parse_playlist_resource(response: Dict[str, str], parse_all: bool = False) -> PlaylistResource:
	kind = response.get('kind')
	resource_id = response.get('id')
	item_id = resource_id

	snippet = _parseSnippet(response.get('snippet', {}))
	content_details = _parseContentDetails(response.get('contentDetails', {}))
	if parse_all:
		status = _parseStatus(response.get('status', {}))
		player = _parsePlayer(response.get('player', {}))
		localizations = _parseLocalizations(response.get('localizations', {}))
	parsed_resource = PlaylistResource(
		resourceId = resource_id,
		resourceType = kind,
		itemId = item_id,
		itemType = kind,

		channelId = snippet['channelId'],
		channelName = snippet['channelName'],

		description = snippet['playlistDescription'],
		date = snippet['playlistDate'],
		language = snippet['playlistLanguage'],
		tags = snippet['playlistTags'],
		itemCount = content_details['playlistItemCount']
	)
	return parsed_resource


def _parseContentDetails(content_details):
	item_count = int(content_details.get('itemCount', 0))

	standard_content_details = {
		'playlistItemCount': item_count
	}
	return standard_content_details


def _parseSnippet(snippet):
	playlist_date = snippet.get('publishedAt')
	if playlist_date:
		playlist_date = timetools.Timestamp(playlist_date)
	else:
		playlist_date = None
	standard_snippet = {
		'playlistDate':        playlist_date,
		'channelId':           snippet.get('channelId'),
		'channelName':         snippet.get('channelTitle', ''),
		'playlistName':        snippet.get('title', ''),
		'playlistDescription': snippet.get('description', ''),
		'playlistTags':        snippet.get('tags', []),
		'playlistLanguage':    snippet.get('defaultLanguage', '')
	}

	return standard_snippet


def _parseStatus(response):
	return response


def _parsePlayer(response):
	return response


def _parseLocalizations(response):
	return response

if __name__ == "__main__":
	import yaml
	from pathlib import Path

	data = yaml.load(Path("/home/proginoskes/Documents/GitHub/YoutubeAPI/tests/sample_video_response.yaml").read_text())
	result = parse_playlist_resource(data['items'][0])
	print(result)