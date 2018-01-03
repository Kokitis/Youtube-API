import requests
from pprint import pprint
import datetime
from ..github import youtube_api_key, timetools

API_KEY = youtube_api_key


class ApiResponse:
	"""
		Parsed the response from the Youtube Api. Provedes a convienient method of converting the
		requested data into an easily-parsable format(via .toStandard()) as well as a format compatible with the
		YoutubeDatabase SQL schema.

		Parameters
		----------
			api_response: requests.models.Response
			kwargs:
	"""

	def __init__(self, api_response, **kwargs):

		self.api_response = api_response
		self.endpoint = self._getEndpoint(self.api_response.json())

		self.data = self._parseApiResponse()
		self.item_id = self.toStandard()['itemId']

	def __str__(self):
		string = "ApiResponse('{}', '{}')".format(self.endpoint, self.item_id)
		return string

	def _getEndpoint(self, response):
		"""
			Attempts to determine the endpoint from the api response.
		Parameters
		----------
		response: dict
			The output or the .json() method of the requests.Response object.

		Returns
		-------

		"""

		response_type = response['kind']


		if response_type == 'youtube#channelListResponse':
			endpoint = 'channels'
		elif response_type == 'youtube#playlistListResponse':
			endpoint = 'playlists'
		elif response_type == 'youtube#videoListResponse':
			endpoint = 'videos'
		else:
			pprint(response)
			raise NotImplementedError

		return endpoint

	def _parseApiResponse(self):
		"""
			Validates the response from the api and ensures each argument is of the correct datatype.
		Returns
		-------
			dict, list<dict>
		"""
		if self.endpoint == 'playlistItems':
			raise NotImplementedError
		else:
			first_item = self.api_response.json()['items'][0]
			validated_json_response = self._validateResponseAttributes(first_item)
		return validated_json_response

	def _defineRequestedAttributes(self):
		"""
			Returns the keys that will be the most commonly used.
		Returns
		-------

		"""

		if self.endpoint == 'videos':
			snippet_keys = [
				'title', 'id', 'channelId', 'channelTitle',
				'description', 'defaultAudioLanguage', 'liveBroadcastContent', 'publishedAt',
			]
			required_snippet_keys = ['title', 'id', 'channelId', 'channelTitle', 'description', 'publishedAt']

			statistics_keys = ['likeCount', 'dislikeCount', 'commentCount', 'favoriteCount', 'viewCount']
			required_statistics_keys = ['likeCount', 'dislikeCount', 'viewCount']

			content_details_keys = ['duration']
			required_content_details_keys = ['duration']


		elif self.endpoint == 'channels':
			snippet_keys = ['title', 'country', 'description', 'publishedAt']

			required_snippet_keys = ['title', 'publishedAt']

			statistics_keys = ['viewCount', 'videoCount', 'subscriberCount']
			required_statistics_keys = statistics_keys

			content_details_keys = None
			required_content_details_keys = None
		elif self.endpoint == 'playlists':
			snippet_keys = [
				'id', 'channelId', 'channelTitle',
				'description', 'publishedAt', 'title'
			]
			required_snippet_keys = ['id', 'title', 'channelId']

			statistics_keys = []
			required_statistics_keys = []

			content_details_keys = ['itemCount']
			required_content_details_keys = ['itemCount']

		elif self.endpoint == 'playlistItems':
			snippet_keys = ['channelId', 'channelTitle', 'description', 'playlistId', 'publishedAt', 'title',
				'resourceId']
			required_snippet_keys = ['resourceId', 'playlistId']

			statistics_keys = []
			required_statistics_keys = []

			content_details_keys = []
			required_content_details_keys = []
		else:
			raise NotImplementedError

		attributes = {
			'snippetKeys':                snippet_keys,
			'snippetRequiredKeys':        required_snippet_keys,

			'statisticsKeys':             statistics_keys,
			'statisticsRequiredKeys':     required_statistics_keys,

			'contentDetailsKeys':         content_details_keys,
			'contentDetailsRequiredKeys': required_content_details_keys
		}

		return attributes


	def extractOne(self, converter = None):
		# items = self.getItems(function)
		items = self.getItems(converter)

		if len(items) == 0:
			result = None
		elif len(items) == 1:
			result = items[0]
		else:
			result = items[0]

		return result

	def toSqlEntity(self, **kwargs):
		"""
			Converts the data contained in the api response to a dict
			compatible with the YoutubeDatabase schema. The output can be directly used
			to update the database objects.
		Parameters
		----------
		kwargs

		Returns
		-------
			dict

		"""
		standard_response = self.toStandard()

		if self.endpoint == 'videos':
			entity = {
				'id':          'videoId',
				'name':        "videoName",
				'views':       "videoViewCount",
				'likes':       'videoLikeCount',
				'dislikes':    "videoDislikeCount",
				'publishDate': 'videoPublishDate',
				'duration':    'videoDuration',
				'description': 'videoDescription',
				'tags':        'videoTags'
			}
		elif self.endpoint == 'channels':
			entity = {
				'id':              'channelId',
				'name':            'channelName',
				'country':         'channelCountry',
				'creationDate':    'channelCreationDate',
				'description':     'channelDescription',
				'subscriberCount': 'channelSubscriberCount',
				'videoCount':      'channelVideoCount',
				'viewCount':       'channelViewCount'
			}
		elif self.endpoint == 'playlists':
			entity = {
				'id':          'playlistId',
				'name':        'playlistName',
				'itemCount':   'playlistItemCount',
				'description': 'playlistDescription'
			}
		else:
			raise NotImplementedError

		try:
			sql_entity_args = {k: standard_response[v] for k, v in entity.items()}
		except Exception as exception:
			error_information = {
				'input':        {
					'kwargs': kwargs
				},
				'inFunction':   "ApiResponse.toEntity",
				'errorMessage': str(exception),
				'apiResponse':  self.api_response,
				'entity':       entity,
				'response':     standard_response
			}
			pprint(error_information)
			raise exception

		if self.endpoint == 'videos' or self.endpoint == 'playlists':
			if 'channels' in kwargs:
				channel = kwargs['channels']
			else:
				raise NotImplementedError

			sql_entity_args['channels'] = channel

		if 'tags' not in sql_entity_args:
			sql_entity_args['tags'] = list()

		return sql_entity_args

	def toStandard(self, **kwargs):
		""" Converts the api response into a standardized format. All relevent data
			for the requested entities is represented as a standard dictionary where each
			key is mapped to either a scalar variable or a list, as needed.
		Returns
		-------

		"""
		#api_response = self.extractOne()
		api_response = self.data

		_toNum = lambda s: int(s) if s else -1

		if self.endpoint == 'channels':
			channel_id = api_response['id']
			channel_name = api_response['snippet']['title']
			channel_date = api_response['snippet']['publishedAt']
			channel_country = api_response['snippet']['country']
			channel_description = api_response['snippet']['description']
			channel_subscribers = api_response['statistics']['subscriberCount']
			channel_views = api_response['statistics']['viewCount']
			channel_videos = api_response['statistics']['videoCount']

			channel_date = timetools.Timestamp(channel_date)

			standard = {
				'itemKind':               'channel',
				'itemId':                 channel_id,
				'channelId':              channel_id,
				'channelName':            channel_name,
				'channelCreationDate':    channel_date,
				'channelCountry':         channel_country,
				'channelDescription':     channel_description,
				'channelSubscriberCount': channel_subscribers,
				'channelViewCount':       channel_views,
				'channelVideoCount':      channel_videos
			}
		elif self.endpoint == 'videos':
			video_id = api_response['id']
			video_name = api_response['snippet']['title']
			view_count = api_response['statistics']['viewCount']
			like_count = api_response['statistics']['likeCount']
			dislike_count = api_response['statistics']['dislikeCount']
			video_date = api_response['snippet']['publishedAt']
			video_duration = api_response['contentDetails']['duration']
			video_channel = api_response['snippet']['channelId']
			video_description = api_response['snippet']['description']
			tags = api_response['tags']

			video_duration = timetools.Duration(video_duration)
			video_date = timetools.Timestamp(video_date)

			standard = {
				'itemKind':          'video',
				'itemId':            video_id,
				'videoId':           video_id,
				'videoName':         video_name,
				'videoViewCount':    _toNum(view_count),
				'videoLikeCount':    _toNum(like_count),
				'videoDislikeCount': _toNum(dislike_count),
				'videoPublishDate':  video_date,
				'videoDuration':     video_duration,
				'channelId':         video_channel,
				'videoDescription':  video_description,
				'videoTags':         tags
			}
		elif self.endpoint == 'playlists':

			playlist_id = api_response['id']
			playlist_name = api_response['snippet']['title']
			playlist_channel = api_response['snippet']['channelId']
			playlist_videos = api_response['contentDetails']['itemCount']
			playlist_description = api_response['snippet']['description']
			standard = {
				'itemKind':            'playlist',
				'itemId':              playlist_id,
				'playlistId':          playlist_id,
				'playlistName':        playlist_name,
				'channelId':           playlist_channel,
				'playlistDescription': playlist_description,
				'playlistItemCount':   playlist_videos,
				'playlistItems':       None
			}

			playlist_items = kwargs.get('playlistItems', [])
			standard['playlistItems'] = playlist_items
		else:
			raise NotImplementedError

		return standard



	def _verifyResponseStatusCode(self, response):
		error_response = response.get('errors')

		if error_response:
			error_code = error_response['code']
			status = False

			if error_code == 503:  # Common backend error
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
			'inputs':       {
				'response':   response
			},
			'inFunction':   "ApiResponse._verifyResponse",
			'status':       status,
			'errorCode':    error_code,
			'errorMessage': error_message,

		}

		self.error = error_info

		return error_info


	def _validateResponseAttributes(self, response):

		_extractKeys = lambda data, keys: {k:data.get(k) for k in keys}

		response_id = response['id']

		snippet = response.get('snippet')
		statistics = response.get('statistics')
		content_details = response.get('contentDetails')
		topic_details = response.get('topicDetails', dict())

		attribute_definitions = self._defineRequestedAttributes()
		snippet_keys = attribute_definitions['snippetKeys']
		snippet_required_keys = attribute_definitions['snippetRequiredKeys']
		statistics_keys = attribute_definitions['statisticsKeys']
		statistics_required_keys = attribute_definitions['statisticsRequiredKeys']

		content_details_keys = attribute_definitions['contentDetailsKeys']
		content_details_required_keys = attribute_definitions['contentDetailsRequiredKeys']

		# Validate response attributes

		_isValid = lambda data, keys: data is not None and all(data[k] is not None for k in keys) # check if any are None

		validated_snippet = None
		validated_statistics = None
		validated_content_details = None

		# Validate Snippet

		if snippet and snippet_keys:
			validated_snippet = _extractKeys(snippet, snippet_keys)
		snippet_is_valid = _isValid(validated_snippet, snippet_required_keys)


		# Validate Statistics

		if statistics and statistics_keys:
			validated_statistics = _extractKeys(statistics, statistics_keys)
		statistics_is_valid = _isValid(validated_statistics, statistics_required_keys)

		# Validate ContentDetails

		if content_details and content_details_keys:
			validated_content_details = _extractKeys(content_details, content_details_keys)
		content_details_is_valid = _isValid(validated_content_details, content_details_required_keys)

		# Add tags and check if all parts are valid

		if self.endpoint == 'videos':
			tags = snippet.get('tags', [])
			tags += topic_details.get('topicCategories', [])
			tags += topic_details.get('relevantTopicIds', [])
			is_valid = snippet_is_valid and statistics_is_valid and content_details_is_valid

		elif self.endpoint == 'channels':
			tags = []
			is_valid = snippet_is_valid and statistics_is_valid

		elif self.endpoint == 'playlists':
			tags = []
			is_valid = snippet_is_valid and content_details_is_valid

		elif self.endpoint == 'playlistItem':
			resource = snippet['resourceId']
			item_kind = resource['kind'].split('#')[1]
			item_id = resource[item_kind + 'Id']
			response_id = item_id
			validated_snippet['itemId'] = item_id
			tags = []
			is_valid = snippet_is_valid
		else:
			tags = []
			is_valid = False

		tags = [str(i).lower() for i in tags]

		error_info = {
			'input':        {
				'response': response
			},
			'inFunction':   "ApiResponse._validateResponseitems'",
			'errorMessage': "Error when validating the api response.",
			'status':       is_valid
		}

		result = {
			'id':               response_id,
			'itemKind':         self.endpoint,
			'tags':             tags,
			'isValid':          is_valid,
			'snippet':          validated_snippet,
			'statistics':       validated_statistics,
			'contentDetails':   validated_content_details,
			'topicDetails':     topic_details,
			'errorInformation': error_info
		}
		return result



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

	def __init__(self, api_key):
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

	def getPlaylistItems(self, key):
		""" Returns a list of all items contained in the playlist. """

		playlist_items = self.get('playlistItems', key)  # **playlist_items_parameters)
		if playlist_items is None:
			p_items = []
		else:
			p_items = [
				{'itemId': s['id'], 'itemKind': s['kind']} for s in playlist_items['items']
			]
		return p_items

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

		if status_code != 200:  # 200 == success
			print("Status Code: ", status_code)

		return response

	def get(self, endpoint, key):
		"""

		Parameters
		----------
		endpoint: {'channels', 'playlists', 'videos'}
		key: str

		Returns
		-------
			dict


		"""
		if not endpoint.endswith('s'): endpoint += 's'
		parameters = self._getParameters(endpoint, key)

		response = self.request(endpoint, **parameters)

		response = ApiResponse(response)

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

	def _extractAllPages(self, **parameters):
		raise NotImplementedError
		items = list()

		page_parameters = parameters
		index = 0
		while True:
			index += 1
			response = self.request(endpoint, **page_parameters)

			response_items = response.get('items', [])
			next_page_token = response.get('nextPageToken')

			_is_dict = isinstance(response, dict)

			if _is_dict:
				_items_valid = len(response_items) != 0
				items += response_items
				_page_valid = next_page_token is not None

			else:
				_items_valid = _page_valid = False

			if _is_dict and _items_valid and _page_valid:
				page_parameters['pageToken'] = next_page_token

			else:
				break

		return items