import requests

from functools import partial
from pprint import pprint
from .resources import *
from typing import List, Union

pprint = partial(pprint, width = 180)

from ..github import youtube_api_key

ResourceType = Union[VideoResource, ChannelResource, PlaylistResource, PlaylistItemResource, SearchResource]


class YouTube:
	endpoints = {
		'youtube#video':        'https://www.googleapis.com/youtube/v3/videos',
		'youtube#search':       'https://www.googleapis.com/youtube/v3/search',
		'youtube#channel':      'https://www.googleapis.com/youtube/v3/channels',
		'youtube#playlist':     'https://www.googleapis.com/youtube/v3/playlists',
		'youtube#playlistItem': 'https://www.googleapis.com/youtube/v3/playlistItems',
		'youtube#activities':    'https://www.googleapis.com/youtube/v3/activities',
		'youtube#watch':         'http://www.youtube.com/watch'
	}

	quota_costs = {
		'videos.list':        {
			'contentDetails':       2,
			'fileDetails':          1,
			'id':                   0,
			'liveStreamingDetails': 2,
			'localizations':        2,
			'player':               0,
			'processingDetails':    1,
			'recordingDetails':     2,
			'snippet':              2,
			'statistics':           2,
			'status':               2,
			'suggestions':          1,
			'topicDetails':         2
		},
		'playlists.list':     {
			'contentDetails': 2,
			'id':             0,
			'localizations':  2,
			'player':         0,
			'snippet':        2,
			'status':         2
		},
		'playlistItems.list': {
			'contentDetails': 2,
			'id':             0,
			'snippet':        2,
			'status':         2
		},
		'channels.list':      {
			'auditDetails':        4,
			'brandingSettings':    2,
			'contentDetails':      2,
			'contentOwnerDetails': 2,
			'id':                  0,
			'invideoPromotion':    2,  # (deprecated)
			'localizations':       2,
			'snippet':             2,
			'statistics':          2,
			'status':              2,
			'topicDetails':        2,
		},
		'subscriptions.list': {
			'contentDetails':    2,
			'id':                0,
			'snippet':           2,
			'subscriberSnippet': 2
		},
		'comments.list':      {
			'id':      0,
			'snippet': 1
		},
		'activities.list':    {
			'contentDetails': 2,
			'id':             0,
			'snippet':        2
		}
	}

	def __init__(self, api_key: str = None):
		if api_key is None:
			self.api_key = youtube_api_key
		else:
			self.api_key = api_key

	@staticmethod
	def getDefaultApiParameters(endpoint: str, request_key: Union[str, List[str]], **optional_parameters) -> Dict[
		str, str]:
		if request_key is None and endpoint != 'search':
			raise ValueError("Request Key = '{}', kind = '{}'".format(request_key, endpoint))

		if not isinstance(request_key, list):
			request_key = [request_key]

		request_key = ','.join(request_key)

		default_parameters = {
			'youtube#channel':      {
				'id':   request_key,
				'part': "snippet,statistics,topicDetails,contentDetails"
			},

			'youtube#playlist':     {
				'id':         request_key,
				'maxResults': '50',
				'part':       "snippet,contentDetails"
			},

			'youtube#playlistItem': {
				'playlistId': request_key,
				'maxResults': '50',
				'part':       'snippet'
			},

			'youtube#video':        {
				'id':   request_key,
				'part': 'snippet,contentDetails,statistics,topicDetails'
			}
		}
		parameters = default_parameters[endpoint]
		if optional_parameters:
			parameters.update(optional_parameters)

		return parameters

	def calculateQuota(self, endpoint: str, parts: List[str]):
		base_cost = 1

		method_costs = self.quota_costs[endpoint + '.list']
		base_cost += sum([v for k, v in method_costs if k in parts])
		return base_cost

	def getChannelItems(self, channel_id: str, **kwargs) -> ListResource:
		parameters = {
			'id':   channel_id,
			'part': 'contentDetails'
		}
		channel_response = self.get('youtube#channel', channel_id, **parameters)
		if len(channel_response) == 0:
			return None

		upload_playlist = channel_response[0]['channelUploadPlaylist']
		channel_items = self.get('playlistItems', upload_playlist, part = 'id,snippet', **kwargs)

		return channel_items

	def getVideos(self, ids: Union[str, int]) -> ListResource:
		if not isinstance(ids[0], str):
			ids = [i.item_id for i in ids]
		max_page_length = 50
		start_index = 0
		end_index = max_page_length

		response = None
		while start_index < len(ids):
			if end_index >= len(ids): end_index = len(ids)

			api_response = self.get('videos', ids[start_index:end_index])
			if response is None:
				response = api_response
			else:
				response.items += api_response.items

			start_index += max_page_length
			end_index += max_page_length
		return response

	def request(self, endpoint: str, key: str, **parameters) -> Dict:
		"""
			Sends a raw request to the Youtube Api.
		Parameters
		----------
		endpoint: str
		key: str

		Returns
		-------

		"""
		if 'youtube' not in endpoint:
			endpoint = 'youtube#' + endpoint

		parameters = self.getDefaultApiParameters(endpoint, key, **parameters)
		parameters['key'] = self.api_key

		url = self.endpoints[endpoint]

		response = requests.get(url, params = parameters)
		status_code = response.status_code
		response = response.json()
		response['statusCode'] = status_code

		return response

	def get(self, endpoint: str, key: str, **parameters) -> ListResource:
		"""

		Parameters
		----------
		endpoint: str
		key: str

		Returns
		-------
			Resource

		"""
		if endpoint.endswith('s'):
			endpoint = endpoint[:-1]
		if '#' not in endpoint:
			endpoint = 'youtube#' + endpoint

		response = self.request(endpoint, key, **parameters)

		response_resource = ListResource(response)
		if response_resource.status_code != 200:
			pprint(endpoint)
			pprint(key)
			pprint(parameters)
		if response_resource.next_page_token:
			next_page_response = self.get(endpoint, key, pageToken = response_resource.next_page_token)
			response_resource.items += next_page_response.items
		return response_resource

	def search(self, **parameters):
		raise NotImplementedError
