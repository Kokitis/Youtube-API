import requests
from typing import NamedTuple, Optional, Tuple
from youtubeapi.github import youtube_api_key
import math
from pprint import pprint
import itertools

try:
	from .resources import *
except ModuleNotFoundError:
	from resources import *
endpoints = {
	'youtube#video':        'https://www.googleapis.com/youtube/v3/videos',
	'youtube#search':       'https://www.googleapis.com/youtube/v3/search',
	'youtube#channel':      'https://www.googleapis.com/youtube/v3/channels',
	'youtube#playlist':     'https://www.googleapis.com/youtube/v3/playlists',
	'youtube#playlistItem': 'https://www.googleapis.com/youtube/v3/playlistItems',
	'youtube#activities':   'https://www.googleapis.com/youtube/v3/activities',
	'youtube#watch':        'http://www.youtube.com/watch'
}


class ResourceTypes(NamedTuple):
	channel: str = "youtube#channel"
	playlist: str = "youtube#playlist"
	playlist_item: str = "youtube#playlistItem"
	video: str = "youtube#video"


resource_types = ResourceTypes()


def split_iterator(items: List, max_length: int = 50) -> List[List]:
	chain = list()
	while items:
		curent_length = len(items)
		max_index = min([curent_length, max_length])
		chain.append(list(itertools.islice(items, max_index)))
		items = items[max_index:]
	return chain


def infer_resource_type(string: str) -> str:
	""" Attempts to infer the type of resource refered to by the given id string."""
	if len(string) == 11:
		return resource_types.video
	elif len(string) == 24 and string.startswith('UC'):
		return resource_types.channel
	elif len(string) == 24 and string.startswith('UU'):
		# Is the playlist of all uploads for a given channel.
		return resource_types.playlist
	elif len(string) == 34:
		return resource_types.playlist
	elif len(string) == 68:
		return resource_types.playlist_item
	else:
		# Assume it is a tag.
		return 'youtube#tag'


def _get_default_api_parameters(resource_type, key) -> Dict[str, str]:
	default_parameters = {
		'youtube#channel':      {
			'id':   key,
			'part': "snippet,statistics,topicDetails,contentDetails"
		},

		'youtube#playlist':     {
			'id':         key,
			'maxResults': '50',
			'part':       "snippet,contentDetails"
		},

		'youtube#playlistItem': {
			'playlistId': key,
			'maxResults': '50',
			'part':       'id,snippet'
		},

		'youtube#video':        {
			'id':   key,
			'part': 'snippet,contentDetails,statistics'
		}
	}
	parameters = default_parameters[resource_type]
	parameters['key'] = youtube_api_key
	return parameters


def request(resource_type: str, key: str, params: Optional[Dict] = None) -> Dict[str, str]:
	""" Sends a request to the youtube data api and returns the raw response.
		Parameters
		----------
		resource_type: str
			Should be a valid response type with the prefix 'youtube#'
		key: str
			The youtube id for the request.
		params: Optional[Dict]
			Any extra parameters to include with the api request.
	"""
	parameters = _get_default_api_parameters(resource_type, key)
	if params is not None:
		parameters.update(params)

	base_url = endpoints[resource_type]

	raw_response = requests.get(base_url, parameters)
	status_code = raw_response.status_code
	response = raw_response.json()
	response['statusCode'] = status_code
	return response


def validate_response(response: Dict[str, str]):
	if 'error' in response:
		pprint(response['error'])
		raise ValueError


def get(resource_type: str, key: str) -> Union[Resource, List[Resource]]:
	""" Sends a request to the api and returns the parsed resource."""
	resource_items = list()
	page_token = {}
	while True:
		response = request(resource_type, key, page_token)
		validate_response(response)
		current_list_resource = parse_list_resource(response)
		resource_items += current_list_resource.items
		if current_list_resource.next_page_token:
			page_token = {'pageToken': current_list_resource.next_page_token}
		else:
			break

	if len(resource_items) == 1 and resource_type != resource_types.playlist_item:
		result = resource_items[0]
	else:
		result = resource_items
	return result


def request_channel_playlists(key: str) -> List[PlaylistResource]:
	parameters = _get_default_api_parameters(resource_types.playlist, None)
	parameters.pop('id')
	parameters['channelId'] = key
	response = requests.get(endpoints[resource_types.playlist], parameters)
	response = response.json()
	response_resource = parse_list_resource(response)
	return response_resource.items


def request_channel_videos(key: str) -> Tuple[ChannelResource, PlaylistResource, List[VideoResource]]:
	""" Returns a list of all videos associated with a specific channel."""
	channel = get(resource_types.channel, key)
	upload_playlist, channel_videos = request_playlist_items(channel.uploads)
	return channel, upload_playlist, channel_videos


def request_playlist_item_ids(playlist_id: str) -> List[str]:
	""" Returns a list of all item ids associated with a given playlist. They should all be videos."""
	playlist_items = get(resource_types.playlist_item, playlist_id)
	playlist_item_ids = [i.itemId for i in playlist_items]
	return playlist_item_ids


def request_playlist_items(key: str) -> Tuple[PlaylistResource, List[VideoResource]]:
	""" Returns a list of all videos associated with a playlist."""
	playlist = get(resource_types.playlist, key)
	playlist_item_ids = request_playlist_item_ids(key)
	print(f"Found {len(playlist_item_ids)} playlist items")
	# playlist_videos = [get(resource_types.video, playlist_item_id) for playlist_item_id in playlist_item_ids]

	playlist_videos = list()
	for keys in split_iterator(playlist_item_ids, 25):
		playlist_videos += get(resource_types.video, ",".join(keys))
	playlist_videos = [p for p in playlist_videos if p is not None]
	return playlist, playlist_videos


def search():
	raise NotImplementedError


if __name__ == "__main__":
	from dataclasses import asdict
	from pprint import pprint

	_playlist_key = "PLbIc1971kgPCFlvfYMbZ3umbad61v4fIq"
	_key = "UCjdQaSJCYS4o2eG93MvIwqg"
	result = request_channel_playlists(_key)
	for i in split_iterator(list(range(99)), 13):
		print(i)
