from typing import Dict
from dataclasses import dataclass
from pytools import timetools
@dataclass
class PlaylistItemResource:
	resourceId: str
	resourceType: str
	itemId: str
	itemType: str
	playlistId: str
	channelId: str
	channelName: str
	name: str
	description: str
	date: str
	position: int

def parse_playlistitem_resource(response:Dict[str,str])->PlaylistItemResource:
	response = response
	kind = response.get('kind')
	resource_id = response.get('id')

	snippet = _parseSnippet(response.get('snippet', {}))
	content_details = _parse_content_details(response.get('contentDetails', {}))
	status = _parse_status(response.get('status', {}))

	parsed_resource = PlaylistItemResource(
		resourceId = resource_id,
		resourceType = kind,
		itemId = snippet['itemId'],
		itemType = snippet['itemType'],
		playlistId = snippet['playlistId'],
		channelId = snippet['channelId'],
		channelName = snippet['channelName'],
		name = snippet['playlistItemName'],
		description = snippet['playlistItemDescription'],
		date = snippet['playlistItemDate'],
		position = snippet['playlistItemPosition']
	)
	return parsed_resource


def _parseSnippet(response):
	item_position = int(response.get('position', 0))
	item_date = response.get('publishedAt')
	item_resource_info = response.get('resourceId', {})
	resource_type = item_resource_info.get('kind')
	resource_id = item_resource_info.get('videoId')
	if item_date:
		item_date = timetools.Timestamp(item_date)

	standard_snippet = {
		'playlistItemDate':        item_date,
		'channelId':               response.get('channelId'),
		'playlistItemName':        response.get('title'),
		'playlistItemDescription': response.get('description', ''),
		'channelName':             response.get('channelTitle', ''),
		'playlistId':              response.get('playlistId', ''),
		'playlistItemPosition':    item_position,
		'itemId':                  resource_id,
		'itemType':                resource_type
	}
	return standard_snippet


def _parse_content_details(response):
	return response


def _parse_status(response):
	return response

