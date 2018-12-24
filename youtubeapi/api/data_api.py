import requests
from typing import NamedTuple, Optional
from youtubeapi.github import youtube_api_key
import tqdm
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


def get_default_api_parameters(resource_type, key) -> Dict[str, str]:
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
			'part':       'snippet'
		},

		'youtube#video':        {
			'id':   key,
			'part': 'snippet,contentDetails,statistics,topicDetails'
		}
	}
	parameters = default_parameters[resource_type]
	parameters['key'] = youtube_api_key
	return parameters


def request(resource_type: str, key: str, page_token: Optional[str] = None) -> Dict[str, str]:
	""" Sends a request to the youtube data api and returns the raw response.
		Parameters
		----------
		resource_type: str
			Should be a valid response type with the prefix 'youtube#'
		key: str
			The youtube id for the request.
	"""
	parameters = get_default_api_parameters(resource_type, key)
	if page_token:
		parameters['pageToken'] = page_token
	base_url = endpoints[resource_type]
	raw_response = requests.get(base_url, parameters)
	status_code = raw_response.status_code
	response = raw_response.json()
	response['statusCode'] = status_code
	return response

def validate_response(response:Dict[str,str]):
	if 'error' in response:
		pprint(response['error'])
		raise ValueError

def get(resource_type: str, key: str) -> Union[Resource, List[Resource]]:
	""" Sends a request to the api and returns the parsed resource."""
	resource_items = list()
	page_token = False
	while True:
		response = request(resource_type, key, page_token)
		validate_response(response)
		current_list_resource = parse_list_resource(response)
		resource_items += current_list_resource.items
		if current_list_resource.next_page_token:
			page_token = current_list_resource.next_page_token
		else:
			break


	if len(resource_items) == 1:
		result = resource_items[0]
	else:
		result = resource_items
	return result


def request_channel_videos(key: str) -> List[VideoResource]:
	""" Returns a list of all videos associated with a specific channel."""
	channel = get(resource_types.channel, key)
	upload_playlist_key = channel.uploads
	channel_videos = request_playlist_videos(upload_playlist_key)
	return channel_videos


def request_playlist_videos(key: str) -> List[VideoResource]:
	""" Returns a list of all videos associated with a playlist."""
	playlist = get(resource_types.playlist, key)
	playlist_items = get(resource_types.playlist_item, playlist.itemId)
	print(f"Found {len(playlist_items)} playlist items")
	playlist_videos = list()
	for playlist_item in playlist_items:
		video = get(resource_types.video, playlist_item.itemId)
		playlist_videos.append(video)
	return playlist_videos


def search():
	raise NotImplementedError


if __name__ == "__main__":
	from dataclasses import asdict
	from pprint import pprint

	_playlist_key = "PLbIc1971kgPCFlvfYMbZ3umbad61v4fIq"
	_key = "UCjdQaSJCYS4o2eG93MvIwqg"
	_result = request_channel_videos(_key)
	#_result = request(resource_types.playlist_item, "UUboMX_UNgaPBsUOIgasn3-Q")
	pprint(_result)


