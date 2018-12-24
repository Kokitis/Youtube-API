from typing import List, Dict, Union
from dataclasses import dataclass
from .channel_resource import ChannelResource, parse_channel_resource
from .playlist_resource import PlaylistResource, parse_playlist_resource
from .playlistitem_resource import PlaylistItemResource, parse_playlistitem_resource
from .video_resource import VideoResource, parse_video_response

Resource = Union[ChannelResource, PlaylistResource, PlaylistItemResource, VideoResource]


@dataclass
class ListResource:
	resourceId: str
	resourceType: str
	previous_page_token: str
	next_page_token: str
	items: List[Resource]


def get_response_type(response: Dict) -> str:
	""" Attemps to extract the resourceType of the given response.
		Should be one of 'youtube#channel', 'youtube#playlist', 'youtube#playlistItem', 'youtubeVideo', 'youtube#searchResult'

	"""
	accepted_types = {'youtube#channel', 'youtube#playlist', 'youtube#playlistItem', 'youtube#video',
					  'youtube#searchResult'}
	kind = response['kind']
	try:
		assert kind in accepted_types
	except AssertionError:
		message = f"Expected one of {accepted_types}, got '{kind}'"
		raise ValueError(message)
	return kind


def parse_resource(response: Dict) -> Resource:
	resource_type = get_response_type(response)

	if resource_type == 'youtube#video':
		parsed_resource = parse_video_response(response)
	elif resource_type == 'youtube#channel':
		parsed_resource = parse_channel_resource(response)
	elif resource_type == 'youtube#playlist':
		parsed_resource = parse_playlist_resource(response)
	elif resource_type == 'youtube#playlistItem':
		parsed_resource = parse_playlistitem_resource(response)
	elif resource_type == 'youtube#searchResult':
		raise NotImplementedError
	else:
		raise ValueError(f"Invalid Resource Type: '{resource_type}")
	return parsed_resource


def parse_list_resource(response: Dict) -> ListResource:
	kind = response.get('kind')  # should be 'youtube#videoListResponse'
	etag: str = response.get('etag')
	next_page_token: str = response.get('nextPageToken')
	previous_page_token: str = response.get('prevPageToken')
	items: List = [parse_resource(i) for i in response.get('items', [])]

	parsed_resource = ListResource(
		resourceId = etag,
		resourceType = kind,
		previous_page_token = previous_page_token,
		next_page_token = next_page_token,
		items = items
	)
	return parsed_resource
