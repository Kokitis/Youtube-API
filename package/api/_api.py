import requests

from functools import partial
from pprint import pprint
from .resources import *

pprint = partial(pprint, width = 180)

from ..github import youtube_api_key


class YouTube:
	endpoints = {
		'videos':        'https://www.googleapis.com/youtube/v3/videos',
		'searchs':       'https://www.googleapis.com/youtube/v3/search',
		'channels':      'https://www.googleapis.com/youtube/v3/channels',
		'playlists':     'https://www.googleapis.com/youtube/v3/playlists',
		'playlistItems': 'https://www.googleapis.com/youtube/v3/playlistItems',
		'activities':    'https://www.googleapis.com/youtube/v3/activities',
		'watch':         'http://www.youtube.com/watch'
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

	def __init__(self, api_key = None):
		if api_key is None:
			self.api_key = youtube_api_key
		else:
			self.api_key = api_key

	@staticmethod
	def getDefaultApiParameters(endpoint, request_key, **optional_parameters):
		if request_key is None and endpoint != 'search':
			raise ValueError("Request Key = '{}', kind = '{}'".format(request_key, endpoint))

		if not isinstance(request_key, list):
			request_key = [request_key]

		request_key = ','.join(request_key)

		default_parameters = {
			'channels':      {
				'id':   request_key,
				'part': "snippet,statistics,topicDetails"
			},

			'playlists':     {
				'id':         request_key,
				'maxResults': '50',
				'part':       "snippet,contentDetails"
			},

			'playlistItems': {
				'playlistId': request_key,
				'maxResults': '50',
				'part':       'snippet'
			},

			'videos':        {
				'id':   request_key,
				'part': 'snippet,contentDetails,statistics,topicDetails'
			}
		}
		parameters = default_parameters[endpoint]
		if optional_parameters:
			parameters.update(optional_parameters)

		return parameters

	def calculateQuota(self, endpoint, parts):
		base_cost = 1

		method_costs = self.quota_costs[endpoint + '.list']
		base_cost += sum([v for k, v in method_costs if k in parts])
		return base_cost

	def getChannelItems(self, channel_id, **kwargs):
		parameters = {
			'id':   channel_id,
			'part': 'contentDetails'
		}
		channel_response = self.get('channels', channel_id, **parameters)

		upload_playlist = channel_response['channelUploadPlaylist']
		channel_items = self.get('playlistItems', upload_playlist, part = 'id,snippet', **kwargs)

		return channel_items

	def getVideos(self, ids):
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

	def request(self, endpoint, key, **parameters):
		"""
			Sends a raw request to the Youtube Api.
		Parameters
		----------
		endpoint: str
		key: str

		Returns
		-------

		"""
		if not endpoint.endswith('s'):
			endpoint += 's'

		parameters = self.getDefaultApiParameters(endpoint, key, **parameters)
		parameters['key'] = self.api_key

		url = self.endpoints[endpoint]

		response = requests.get(url, params = parameters)
		status_code = response.status_code
		response = response.json()
		response['statusCode'] = status_code

		return response

	def get(self, endpoint, key, **parameters):
		"""

		Parameters
		----------
		endpoint: {'channels', 'playlists', 'videos'}
		key: str

		Returns
		-------
			Resource

		"""

		response = self.request(endpoint, key, **parameters)

		response_resource = ListResource(response)
		if response_resource.status_code != 200:
			pprint(endpoint)
			pprint(key)
			pprint(parameters)
		if response_resource.next_page_token:
			next_page_response = self.get(endpoint, key, pageToken = response_resource.next_page_token)
			response_resource.items += next_page_response.items
		if len(response_resource.items) == 1:
			response_resource = response_resource.items[0]
		return response_resource

	def search(self, **parameters):
		raise NotImplementedError
