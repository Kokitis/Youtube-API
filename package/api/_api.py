import requests
from pprint import pprint
import datetime
from ..github import youtube_api_key, timetools
API_KEY = youtube_api_key

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
	def __init__(self, endpoint, key, **kwargs):
		if endpoint.endswith('s'): 
			endpoint = endpoint[:-1]
		self.error_information = None 
		self.request_key = key
		self.endpoint = endpoint

		self.raw_response = self._request(endpoint, key, **kwargs)

		if 'nextPageToken' in self.raw_response:
			self.raw_response['items'] = self._extractAllPages(**kwargs)
 
		self.validated_items = list()
		if self.status:
			for item in self.raw_response['items']:
				response_item = self._validateResponseItems(item)
				_passed_validation = response_item['errorInformation']
				if not _passed_validation:
					pprint(response_item)
					raise ValueError("Response Item did not pass validation.")
				else:
					self.validated_items.append(response_item)
	def __str__(self):
		string = "ApiResponse('{}', status = '{}')".format(self.endpoint, self.status)
		return string

	def getItems(self, converter = None):
		""" if function is a callable object, will return function(item) """

		if self.status and 'items' in self.raw_response:
			items = self.validated_items

			if converter is not None and callable(converter):
				items = [converter(i) for i in items]
			items = [i for i in items if i is not None]
		else:
			items = []

		return items

	def _getParameters(self, kind = None, request_key = None, provided_parameters = None):
		if kind is None:
			kind = self.endpoint

		if request_key is None and kind != 'search':
			raise ValueError("Request Key = '{}', kind = '{}'".format(request_key, kind))
		elif kind == 'channel':
			parameters = {
				'id': request_key,
				'part': "snippet,statistics,topicDetails"
			}
		elif kind == 'video':
			parameters = {
				'id': request_key,
				'part': 'snippet,contentDetails,statistics,topicDetails'
			}
		elif kind == 'playlist':
			parameters =  {
				'id': request_key,
				'maxResults': '50',
				'part': "snippet,contentDetails"
			}
		elif kind == 'playlistItems':
			parameters = {
				'playlistId': request_key,
				'maxResults': '50',
				'part': 'snippet'
			}
		elif len(provided_parameters) != 0:
			parameters = provided_parameters
		else:
			parameters = None

		if parameters is None:
			error_info = {
				'errorMessage': "Cannot properly set the parameters.",
				'inFunction': "ApiResponse._getParameters",
				'input': {
					'kind': kind,
					'request_key': request_key,
					'provided_parameters': provided_parameters
				},
				'parameters': parameters
			}
			pprint(error_info)
			raise NotImplementedError
		parameters['key'] = API_KEY
		self.parameters = parameters
		return parameters

	def extractOne(self, converter = None):
		#items = self.getItems(function)
		items = self.getItems(converter)

		if len(items) == 0:     result = None 
		elif len(items) == 1:   result = items[0]
		else:                   result = items[0]

		return result
 
	def toEntity(self, **kwargs):
		response = self.toStandard()

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
				'tags': 'videoTags'
			}
		elif self.endpoint == 'channel':
			entity = {
				'id': 'channelId',
				'name': 'channelName',
				'country': 'channelCountry',
				'creationDate': 'channelCreationDate',
				'description': 'channelDescription',
				'subscriberCount': 'channelSubscriberCount',
				'videoCount': 'channelVideoCount',
				'viewCount': 'channelViewCount'
			}
		elif self.endpoint == 'playlist':
			entity = {
				'id': 'playlistId',
				'name': 'playlistName',
				'itemCount': 'playlistItemCount',
				'description': 'playlistDescription'
			}
		else:
			raise NotImplementedError
		try:
			entity_args = {k:response[v] for k,v in entity.items()}
		except Exception as exception:
			error_information = {
				'input': {
					'kwargs': kwargs
				},
				'inFunction': "ApiResponse.toEntity",
				'errorMessage': str(exception),
				'apiResponse': self.raw_response,
				'entity': entity,
				'response': response
			}
			pprint(error_information)
			raise exception


		if self.endpoint == 'video' or self.endpoint == 'playlist':
			if 'channel' in kwargs:
				channel = kwargs['channel']
			else:
				channel = None 
			
			entity_args['channel'] = channel

		if 'tags' not in entity_args:
			entity_args['tags'] = list()

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

			channel_date = timetools.Timestamp(channel_date)

			standard = {
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

			if view_count is None:
				view_count = 0 
			if like_count is None:
				like_count = 0
			if dislike_count is None:
				dislike_count = 0 

			
			video_duration = timetools.Duration(video_duration)
			video_date = timetools.Timestamp(video_date)

			standard = {
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
			playlist_description = api_response['snippet']['description']
			standard = {
				'itemKind': 'playlist',
				'itemId': playlist_id,
				'playlistId': playlist_id,
				'playlistName': playlist_name,
				'channelId': playlist_channel,
				'playlistDescription': playlist_description,
				'playlistItemCount': playlist_videos,
				'playlistItems': None
			}

			playlist_items = self.getPlaylistItems()
			standard['playlistItems'] = playlist_items
		else:
			raise NotImplementedError

		return standard

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

	def _verifyResponse(self, parameters, response):
		error_response = response.get('error')

		if error_response:
			error_code = error_response['code']
			status = False

			if error_code == 503: # Common backend error
				error_message = "Common Backend Error."
			else:
				error_message = "Uncommon Error."

		elif len(response['items']) == 0:

			status = False
			error_code = -1
			error_message = "No items found."
		else:
			error_message = "No Errors."
			error_code = 0
			status = True

		error_info = {
			'inputs': {
				'parameters': parameters,
				'response': response
			},
			'inFunction': "ApiResponse._verifyResponse",
			'status': status,
			'errorCode': error_code,
			'errorMessage': error_message,
			
		}

		self.error = error_info
		
		return error_info

	def _request(self, kind = None, request_key = None, **parameters):

		if kind is None:
			kind = self.endpoint
		
		error_message  = None
		if request_key is None and kind != 'playlistItems':
			error_message = "'key' was not provided."

		if kind.endswith('s'):
			base_url = self.endpoints[kind]
		else:
			base_url = self.endpoints[kind + 's']

		try:
			parameters = self._getParameters(kind, request_key, parameters)
			response = requests.get(base_url, params=parameters).json()

		except Exception as exception:
			error_message = str(exception)
			response = None
			
		if error_message:
			error_information = {
				'input': {
					'kind': kind,
					'request_key': request_key,
					'parameters': parameters
				},
				'inFunction': "ApiResponse._request",
				'error_message': error_message
			}
		else:
			error_information = self._verifyResponse(parameters, response)

		self.error_information = error_information
		error_code = error_information['errorCode']
		if not error_information['status'] and error_code not in [-1, 503]:
			pprint(error_information)
			raise ValueError("An error occured in ApiResponse._request()!")
		return response

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
				if False:
					print("_generateValidatedApiResponse(): ")
					print("\tkey, keyType, value: ", (key, key_type, value))
					print("\t", str(exception))
			_result[key] = (value, isinstance(value, key_type))
		return _result

	def _validateResponseItems(self, response):

		_expand = lambda s: {k:v[0] for k,v in s.items()}
		_check = lambda a, b: all(a[k][1] for k in b)
		def _checkIfValid(validated, required, response, part):

			try:
				result = _check(validated, required)
				error_information = None
				error_message = "No Error"
			except KeyError as exception:
				error_message = str(exception)
				result = False
			error_information = {
				'input': {
					'response': response,
					'part': part,
					'validated': validated,
					'required': required
				},
				'inFunction': "_validateResponseItems",
				'errorMessage': error_message,
				'endpoint': self.endpoint,
				'rawResponse': self.raw_response
			}
			output = {'status': result, 'error': error_information}

			return output

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
			snippet_types = [str, str, str,str, timetools.Timestamp, str]
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

		snippet 		= response.get('snippet')
		statistics 		= response.get('statistics')
		content_details = response.get('contentDetails')
		topic_details 	= response.get('topicDetails', dict())

		# Validate Snippet

		if snippet and snippet_keys:
			validated_snippet = self._generateValidatedApiResponse(snippet, snippet_keys, snippet_types)
			parsed_snippet = _expand(validated_snippet)
			snippet_is_valid = _checkIfValid(validated_snippet, required_snippet_keys, response, 'snippet')
		else:
			parsed_snippet = None
			snippet_is_valid = False
		
		# Validate Statistics

		if statistics and statistics_keys:
			validated_statistics = self._generateValidatedApiResponse(statistics, statistics_keys, statistics_types)
			parsed_statistics = _expand(validated_statistics)
			statistics_is_valid = _checkIfValid(validated_statistics, required_statistics_keys, response, 'statistics')
		else:
			parsed_statistics = None
			statistics_is_valid = False
		
		# Validate ContentDetails
		if content_details and content_details_keys:
			validated_content_details = self._generateValidatedApiResponse(content_details, content_details_keys, content_details_types)
			parsed_content_details = _expand(validated_content_details)
			content_details_is_valid = _checkIfValid(validated_content_details, required_content_details_keys, response, 'contentDetails')
		else:
			parsed_content_details = None
			content_details_is_valid = False

		if isinstance(snippet_is_valid, dict)  and not snippet_is_valid['status']:
			error_message = snippet_is_valid
		#elif isinstance(statistics_is_valid, dict) and not statistics_is_valid['status']:
		#	error_message = statistics_is_valid
		elif isinstance(content_details_is_valid, dict) and not content_details_is_valid['status']:
			error_message = content_details_is_valid 
		else:
			error_message = None
		
		if error_message is not None:
			pprint(error_message)
			raise KeyError("There was a KeyError.")

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
		else:
			tags = []
			is_valid  = False

		tags = [str(i).lower() for i in tags]

		error_info = {
			'input': {
				'response': response
			},
			'inFunction': "ApiResponse._validateResponseitems'",
			'errorMessage': "Error when validating the api response.",
			'status': is_valid
		}

		result = {
			'id': response_id,
			'itemKind': response_kind,
			'tags': tags,
			'isValid': is_valid,
			'snippet': parsed_snippet,
			'statistics': parsed_statistics,
			'contentDetails': parsed_content_details,
			'topicDetails': topic_details,
			'errorInformation': error_info
		}
		return result

	def getPlaylistItems(self):
		""" Returns a list of all items contained in the playlist. """

		playlist_items = self._request('playlistItems', request_key = self.request_key)#**playlist_items_parameters)
		if playlist_items is None:
			p_items = []
		else:
			p_items = [
				{'itemId': s['id'], 'itemKind': s['kind']} for s in playlist_items['items']
			]
		return p_items

	def getChannelItems(self):

		if self.endpoint != 'channel':
			message = "Entity '{}' does not have channel items.".format(self.endpoint)
			raise ValueError(message)
		search_parameters = {
			'key': API_KEY,
			'part': 'id',
			'channelId': self.request_key,
			'maxResults': '50'
		}
		search_response = self.search(**search_parameters)

		channel_items = list()
		
		for item in search_response['items']:
			item_kind = item['id']['kind'].split('#')[1]
			item_id = item['id'][item_kind + 'Id']

			element = {
				'itemKind': item_kind,
				'itemId': item_id
			}

			channel_items.append(element)

		return channel_items

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

	@property
	def cost(self):
		_cost = 0

		return _cost

	@property 
	def status(self):
		return self.error_information.get('status', True)


class YouTube:


	def __init__(self, api_key):
		self.api_key = api_key

	def request(self, endpoint, **parameters):
		pass
	def search(self, **parameters):
		pass
