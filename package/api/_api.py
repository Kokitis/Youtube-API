import requests
from progressbar import ProgressBar

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

	def _getDefaultApiParameters(self, endpoint, request_key = None, optional_parameters = None):
		if optional_parameters is None:
			optional_parameters = dict()

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
		parameters = default_parameters.get(endpoint)

		if parameters:
			parameters.update(optional_parameters)

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

		channel_response = self.request('channels', **parameters)
		channel_response = channel_response.json()
		channel_response = channel_response['items'][0]

		upload_playlist = channel_response['contentDetails']['relatedPlaylists']['uploads']

		playlist_items = self.getPlaylistItems(upload_playlist, part = 'id,snippet', **kwargs)

		channel_items = list()
		for element in playlist_items:
			"""
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
			"""

			channel_items.append(element)

		return channel_items

	def getPlaylistItems(self, playlist_id, **kwargs):

		verbose = kwargs.get('verbose')
		parameters = self._getDefaultApiParameters('playlistItems', playlist_id)
		if 'part' in kwargs:
			parameters['part'] = kwargs['part']

		playlist_items = list()
		index = 0
		progress_bar = None
		while True:
			index += 1
			api_response = self.request('playlistItems', **parameters)
			api_response = api_response.json()
			total_items = api_response['pageInfo']['totalResults']

			next_page_token = api_response.get('nextPageToken')
			page_items = api_response.get('items', [])

			playlist_items += page_items
			if verbose:
				# string = "{}\t{} of {}\t{}".format(index, len(playlist_items), total_items, next_page_token)
				# print(string)
				if progress_bar is None:
					progress_bar = ProgressBar(max_value = int(total_items))
				progress_bar.update(len(playlist_items))

			if next_page_token:
				parameters['pageToken'] = next_page_token
			else:
				break

		# result = list(ApiResponse(i) for i in api_response.json().get('items', []))
		result = [ApiResponse(i) for i in playlist_items]
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
		status_code = response.status_code
		response = response.json()
		response['statusCode'] = status_code

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
		parameters = self._getDefaultApiParameters(endpoint, key)

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
