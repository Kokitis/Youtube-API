import requests
from pprint import pprint

from ._api_response import ApiResponse

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

	def __init__(self, api_key = None):
		if api_key is None:
			self.api_key = youtube_api_key
		else:
			self.api_key = api_key
	def _getParameters(self, endpoint, request_key = None, provided_parameters = None):
		if provided_parameters is None:
			provided_parameters = []
		if request_key is None and endpoint != 'search':
			raise ValueError("Request Key = '{}', kind = '{}'".format(request_key, endpoint))
		elif endpoint == 'channels':
			parameters = {
				'id':   request_key,
				'part': "snippet,statistics,topicDetails"
			}
		elif endpoint == 'videos':
			parameters = {
				'id':   request_key,
				'part': 'snippet,contentDetails,statistics,topicDetails'
			}
		elif endpoint == 'playlists':
			parameters = {
				'id':         request_key,
				'maxResults': '50',
				'part':       "snippet,contentDetails"
			}
		elif endpoint == 'playlistItems':
			parameters = {
				'playlistId': request_key,
				'maxResults': '50',
				'part':       'snippet'
			}
		elif len(provided_parameters) != 0:
			parameters = provided_parameters
		else:
			parameters = None

		if parameters is None:
			error_info = {
				'errorMessage': "Cannot properly set the parameters.",
				'inFunction':   "ApiResponse._getParameters",
				'input':        {
					'kind':                endpoint,
					'request_key':         request_key,
					'provided_parameters': provided_parameters
				},
				'parameters':   parameters
			}
			pprint(error_info)
			raise NotImplementedError

		return parameters


	def _getChannelItems(self, key):
		search_parameters = {
			'key':        self.api_key,
			'part':       'id,snippet',
			'channelId':  key,
			'maxResults': '50'
		}
		search_response = self.search(**search_parameters)
		return search_response

	def getChannelItems(self, channel_id):

		search_response = self._getChannelItems(channel_id)
		channel_items = list()

		for item in search_response['items']:
			item_snippet = item['snippet']
			item_kind = item['id']['kind'].split('#')[1]
			item_id = item['id'][item_kind + 'Id']

			item_name = item_snippet['title']
			item_channel_name = item_snippet['channelTitle']
			item_channel_id = item_snippet['channelId']

			element = {
				'itemKind':        item_kind,
				'itemId':          item_id,
				'itemName':        item_name,
				'itemChannelName': item_channel_name,
				'itemChannelId':   item_channel_id
			}

			channel_items.append(element)

		return channel_items

	def getPlaylistItems(self, playlist_id):

		parameters = self._getParameters('playlistItems', playlist_id)
		api_response = self.request('playlistItems', **parameters)
		result = list(ApiResponse(i) for i in api_response.json().get('items', []))
		result = list(i for i in result if i)
		return result

	def request(self, endpoint, **parameters):
		"""
			Sends a raw request to the Youtube Api.
		Parameters
		----------
		endpoint
		parameters

		Returns
		-------

		"""
		if not endpoint.endswith('s'):
			endpoint += 's'
		url = self.endpoints[endpoint]
		parameters['key'] = self.api_key
		response = requests.get(url, params = parameters)

		return response

	def get(self, endpoint, key):
		"""

		Parameters
		----------
		endpoint: {'channels', 'playlists', 'videos'}
		key: str

		Returns
		-------
			ApiResponse


		"""
		if not endpoint.endswith('s'): endpoint += 's'
		parameters = self._getParameters(endpoint, key)

		response = self.request(endpoint, **parameters)

		response = ApiResponse(response)

		while response.next_page_token:
			next_response = self.request(
				endpoint,
				nextPageToken = response.next_page_token,
				**parameters
			)
			response.addResponse(next_response)

		return response

	def search(self, **parameters):

		endpoint = self.endpoints['searchs']
		items = list()

		while True:
			response = requests.get(endpoint, params = parameters)
			response = response.json()
			response_items = response.get('items', [])
			items += response_items
			next_page_token = response.get('nextPageToken')
			if next_page_token is not None and len(response_items) != 0:
				parameters['pageToken'] = next_page_token
			else:
				break
		response['items'] = items
		return response

