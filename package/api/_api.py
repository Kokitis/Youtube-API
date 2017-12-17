import requests
from pprint import pprint
import datetime

class ApiResponse:
	endpoints = {
		'videos': 'https://www.googleapis.com/youtube/v3/videos',
		'searchs': 'https://www.googleapis.com/youtube/v3/search',
		'channels': 'https://www.googleapis.com/youtube/v3/channels',
		'playlists': 'https://www.googleapis.com/youtube/v3/playlists',
		'playlistItems': 'https://www.googleapis.com/youtube/v3/playlistItems',
		'activities': 'https://www.googleapis.com/youtube/v3/activities',
		'watch': 'http://www.youtube.com/watch'
	}
	api_key = None
	def __init__(self, endpoint, key, **kwargs):
		if endpoint.endswith('s'): 
			endpoint = endpoint[:-1]
		
		self.status = None
		self.error_code = None
		self.endpoint = endpoint

		self.parameters = self._getParameters(key)
		self.raw_response = self._request(**kwargs)

		if 'nextPageToken' in self.raw_response:
			self.raw_response['items'] = self._extractAllPages(**kwargs)
 
		self.validated_items = list()
		if self.status and self.endpoint != 'search':
			for item in self.raw_response['items']:
				self.validated_items.append(self._validateApiResponse(item))
		elif self.endpoint == 'search':
			self.validated_items = self.raw_response['items']

	def __iter__(self):
		for i in self.getItems():
			yield i

	def __getitem__(self, key):
		if self.status:
			if key == 'items':
				item = self.getItems()
			else:
				item = self.response.get(key)
		else:
			item = None 
		
		return item

	def __str__(self):
		string = "ApiResponse('{}', status = '{}')".format(self.endpoint, self.status)
		return string

	def getItems(self, function = None):
		""" if function is a callable object, will return function(item) """

		if self.status and 'items' in self.raw_response:
			items = self.validated_items

			if function is not None and callable(function):
				items = [function(i) for i in items]
			items = [i for i in items if i is not None]
		else:
			items = []

		return items

	def _getParameters(self, key):
		if self.endpoint == 'channel':
			parameters = {
				'id': key,
				'key': self.api_key,
				'part': "snippet,statistics,topicDetails"
			}
		elif self.endpoint == 'video':
			parameters = {
				'id': key,
				'key': self.api_key,
				'part': 'snippet,contentDetails,statistics,topicDetails'
			}
		elif self.endpoint == 'playlist':
			parameters =  {
				'id': key,
				'maxResults': '50',
				'key': self.api_key,
				'part': "snippet,contentDetails"
			}
		elif self.endpoint == 'playlistItems':
			parameters = {
				'key': self.api_key,
				'playlistId': key,
				'maxResults': '50',
				'part': 'snippet'
			}
		else:
			raise NotImplementedError

		return parameters

	def extractOne(self, function = None):
		#items = self.getItems(function)
		items = self.getItems(function)

		if len(items) == 0:     result = None 
		elif len(items) == 1:   result = items[0]
		else:                   result = items[0]

		return result
 
	def toEntity(self):

		response = self.extractOne()

		if self.endpoint == 'video':
			entity = {
				'id': 'videoId',
				'name': "videoName",
				'views': "videoViewCount",
				'likes': 'videoLikeCount',
				'dislikes': "videoDislikeCount",
				'publishDate': 'videoPublishDate',
				'duration': 'videoDuration',
				'description': 'videoDescription',
				'channel': '',
				'tags': 'videoTags'
			}
		elif self.endpoint == 'channel':
			entity = {
				'id': 'channelId',
				'name': 'channelName',
				'country': 'channelCountry',
				'creationDate': 'channalCreationDate',
				'description': 'channelDescription',
				'subscriberCount': 'channalSubscriberCount',
				'videoCount': 'channelVideoCount',
				'viewCount': 'channelVideoCount'
			}
		elif self.endpoint == 'playlist':
			entity = {
				'id': 'playlistId',
				'name': 'playlistName',
				'playlistItems': None,
				'itemCount': 'playlistItemCount',
				'description': 'playlistDescription'
			}
		else:
			raise NotImplementedError

		entity_args = {k:response[v] for k,v in entity.items()}
		return entity_args

	def toStandard(self):

		api_response = self.extractOne()

		if self.endpoint == 'channel':
			channel_id          = api_response['id']
			channel_name        = api_response['snippet']['title']
			channel_date        = api_response['snippet']['publishedAt']
			channel_country     = api_response['snippet']['country']
			channel_description = api_response['snippet']['description']
			channel_subscribers = api_response['statistics']['subscriberCount']
			channel_views       = api_response['statistics']['viewCount']
			channel_videos      = api_response['statistics']['videoCount']


			api_call = {
				'itemKind':    'channel',
				'itemId':      channel_id,
				'channelId':    channel_id,
				'channelName':  channel_name,
				'channelCreationDate': channel_date,
				'channelCountry':      channel_country,
				'channelDescription':  channel_description,
				'channelSubscriberCount': channel_subscribers,
				'channelViewCount':    channel_views,
				'channelVideoCount':   channel_videos
			}
		elif self.endpoint == 'video':
			video_id            = api_response['id']
			video_name          = api_response['snippet']['title']
			view_count          = api_response['statistics']['viewCount']
			like_count          = api_response['statistics']['likeCount']
			dislike_count       = api_response['statistics']['dislikeCount']
			video_date          = api_response['snippet']['publishedAt']
			video_duration      = api_response['contentDetails']['duration']
			video_channel       = api_response['snippet']['channelId']
			video_description   = api_response['snippet']['description']
			tags                = api_response['tags']


			api_call = {
				'itemKind': 'video',
				'itemId': video_id,
				'videoId': video_id,
				'videoName': video_name,
				'videoViewCount': view_count,
				'videoLikeCount': like_count,
				'videoDislikeCount': dislike_count,
				'videoPublishDate': video_date,
				'videoDuration': video_duration,
				'channelId': video_channel,
				'videoDescription': video_description,
				'videoTags': tags
			}
		elif self.endpoint == 'playlist':
			playlist_id     = api_response['id']
			playlist_name   = api_response['snippet']['title']
			playlist_channel= api_response['snippet']['channelId']
			playlist_videos = api_response['contentDetails']['itemCount']

			api_call = {
				'itemKind': 'playlist',
				'itemId': playlist_id,
				'playlistId': playlist_id,
				'playlistName': playlist_name,
				'channelId': playlist_channel,
				'playlistItemCount': playlist_videos,
				'playlistItems': None
			}
			playlist_items = self.getPlaylistItems(playlist_id)
			api_call['playlistItems'] = playlist_items
		else:
			raise NotImplementedError

		result = {k:api_response[v] for k,v in api_call.items()}
		return result

	def _extractAllPages(self, **parameters):
		items = list()

		page_parameters = parameters
		index = 0
		while True:
			index += 1
			response = self._request(**page_parameters)

			response_items = response.get('items', [])
			next_page_token = response.get('nextPageToken')

			_is_dict = isinstance(response, dict)

			if _is_dict:
				_items_valid = len(response_items) != 0
				items += response_items
				_page_valid  = next_page_token is not None

			else:
				_items_valid = _page_valid = False

			if _is_dict and _items_valid and _page_valid:
				page_parameters['pageToken'] = next_page_token

			else:
				break

		return items

	def _request(self, kind = None, **parameters):

		if kind is None:
			kind = self.endpoint

		base_url = self.endpoints[kind + 's']

		try:
			parameters = self._getParameters(kind)
			response = requests.get(base_url, params=parameters).json()

		except Exception as exception:
			print(str(exception))
			response = {'code': 404}
		
		error_response = response.get('error')
		if error_response:
			self.status = False
			error_code = error_response['code']
			if error_code == 503: # Common backend error
				response = None 
			elif error_code == 403:
				pprint(error_response)
				message = "Daily Usage limit reached!"
				raise ValueError(message)

			elif error_code == 400:
				pprint(parameters)
				pprint(response)
				message = "Missing a required parameter!"
				raise ValueError(message)
			else:
				response = None
		
		else:
			self.status = True


		return response

	def _getErrorStatus(self, response):
		error_response = response.get('error')
		if error_response:
			self.error_code = error_response['code']
			if self.error_code == 503: # Common backend error
				self.status = False
			elif self.error_code == 404:
				self.status = False
			else:
				message = "Unsupported error '{}'".format(self.error_code)
				pprint(response)
				raise ValueError(message)

		else:
			self.error_code = None 
			self.status = True

	@staticmethod
	def _generateValidatedApiResponse(response, keys, key_types):
		if not isinstance(key_types, list):
			key_types = [key_types] * len(keys)
		_result = dict()
		for key, key_type in zip(keys, key_types):
			value = response.get(key)
			try:
				value = key_type(value)
			except Exception as exception:
				print(exception)
			_result[key] = (value, isinstance(value, key_type))
		return _result

	def _validateApiResponse(self, response):

		_expand = lambda s: {k:v[0] for k,v in s.items()}
		_checkIfValid = lambda a, b: all(a[k][1] for k in b)

		response_id = response['id']
		
		if self.endpoint == 'video':
			snippet_keys = [
				'title', 'id', 'channelId', 'channelTitle', 
				'description', 'defaultAudioLanguage', 'liveBroadcastContent', 'publishedAt',
				]
			snippet_types = str
			required_snippet_keys = ['title', 'id', 'channelId', 'channelTitle', 'description', 'publishedAt']

			statistics_keys = ['likeCount', 'dislikeCount', 'commentCount', 'favoriteCount', 'viewCount']
			statistics_types = int
			required_statistics_keys = ['likeCount', 'dislikeCount', 'viewCount']

			content_details_keys = ['duration']
			content_details_types = str
			required_content_details_keys = ['duration']

		elif self.endpoint == 'channel':
			snippet_keys = ['title', 'country', 'description', 'publishedAt']
			snippet_types = str
			required_snippet_keys = ['title', 'publishedAt']

			statistics_keys = ['viewCount', 'videoCount', 'subscriberCount']
			required_statistics_keys = statistics_keys
			statistics_types = int

			content_details_keys = None
			content_details_types = None
			required_content_details_keys = None
		elif self.endpoint == 'playlist':
			snippet_keys = [
				'id', 'channelId', 'channelTitle', 
				'description', 'publishedAt', 'title'
			]
			snippet_types = [str, str, str,str,datetime.datetime, str]
			required_snippet_keys = ['id', 'title', 'channelId']
			#snippet_types = str

			statistics_keys = []
			required_statistics_keys = []
			statistics_types = int

			content_details_keys = ['itemCount']
			required_content_details_keys = ['itemCount']
			content_details_types = int

		elif self.endpoint == 'playlistItems':
			snippet_keys = ['channelId', 'channelTitle', 'description', 'playlistId', 'publishedAt', 'title', 'resourceId']
			required_snippet_keys = ['resourceId', 'playlistId']
			snippet_types = [str, str, str, str, datetime.datetime, str, dict]
			
			statistics_keys = []
			required_statistics_keys = []
			statistics_types = int

			content_details_keys = []
			required_content_details_keys = []
			content_details_types = None
		else:
			print("Endpoint: ", self.endpoint)
			pprint(response)
			raise NotImplementedError

		snippet = response.get('snippet')
		statistics = response.get('statistics')
		content_details = response.get('contentDetails')
		topic_details = response.get('topicDetails', dict())

		# Validate Snippet

		if snippet and snippet_keys:
			validated_snippet = self._generateValidatedApiResponse(snippet, snippet_keys, snippet_types)
			parsed_snippet = _expand(validated_snippet)
			
			snippet_is_valid = _checkIfValid(validated_snippet, required_snippet_keys)
		else:
			parsed_snippet = None
			snippet_is_valid = False
		
		# Validate Statistics

		if statistics and statistics_keys:
			validated_statistics = self._generateValidatedApiResponse(statistics, statistics_keys, statistics_types)
			parsed_statistics = _expand(validated_statistics)
			statistics_is_valid = _checkIfValid(validated_statistics, required_statistics_keys)
		else:
			parsed_statistics = None
			statistics_is_valid = False
		
		# Validate ContentDetails
		if content_details and content_details_keys:
			validated_content_details = self._generateValidatedApiResponse(content_details, content_details_keys, content_details_types)
			parsed_content_details = _expand(validated_content_details)
			content_details_is_valid = _checkIfValid(validated_content_details, required_content_details_keys)
		else:
			parsed_content_details = None
			content_details_is_valid = False

		response_kind = self.endpoint

		if self.endpoint == 'video':
			
			tags = snippet.get('tags', [])
			tags += topic_details.get('topicCategories', [])
			tags += topic_details.get('relevantTopicIds', [])
			is_valid = snippet_is_valid and statistics_is_valid and content_details_is_valid
		elif self.endpoint == 'channel':
			tags = []
			is_valid = snippet_is_valid and statistics_is_valid
		elif self.endpoint == 'playlist':
			tags = []
			is_valid = snippet_is_valid and content_details_is_valid
		elif self.endpoint == 'playlistItem':
			resource = snippet['resourceId']
			item_kind = resource['kind'].split('#')[1]
			item_id = resource[item_kind + 'Id']
			response_id = item_id 
			parsed_snippet['itemId'] = item_id 
			response_kind = resource['kind']
			tags = []
			is_valid = snippet_is_valid
		elif self.endpoint == 'search':
			item_kind = snippet['resourceId']['kind']
			response_id = snippet['resourceId'][item_kind.split('#')[1] + 'Id']
			is_valid = True
			tags = []
		else:
			tags = []
			is_valid  = False

		tags = [str(i).lower() for i in tags]

		result = {
			'id': response_id,
			'itemKind': response_kind,
			'tags': tags,
			'isValid': is_valid,
			'snippet': parsed_snippet,
			'statistics': parsed_statistics,
			'contentDetails': parsed_content_details,
			'topicDetails': topic_details
		}
		return result

	def getPlaylistItems(self, key):
		""" Returns a list of all items contained in the playlist. """

		playlist_items_parameters = self._getParameters('playlistItems')
		playlist_items_parameters['playlistId'] = key
		playlist_items = self._request('playlistItems', **playlist_items_parameters)
		p_items = playlist_items.getItems(
			lambda s: {'itemId': s['id'], 'itemKind': s['itemKind']}
		)
		return p_items

	def getChannelItems(self, key, channel = None):

		#channel = self.getChannel(key)
		search_parameters = {
			'key': self.api_key,
			'part': 'id',
			'channelId': key,
			'maxResults': '50'
		}

		search_response = self._request('search', **search_parameters)
		
		channel_items = list()
		
		for item in search_response.getItems():
			item_kind = item['id']['kind'].split('#')[1]
			item_id = item['id'][item_kind + 'Id']

			element = {
				'itemKind': item_kind,
				'itemId': item_id
			}

			channel_items.append(element)

		return channel_items

	@property
	def cost(self):
		_cost = 0

		return _cost
	@property
	def response(self):
		return self.extractOne()


class YouTube:


	def __init__(self, api_key):
		self.api_key = api_key
		self.attempts = 5
		self.errors = list()

