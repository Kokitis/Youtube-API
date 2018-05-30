from pprint import pprint
from functools import partial
import yaml
import json
pprint = partial(pprint, width = 200)
from ..github import timetools


class ApiResponse:
	"""
		Parsed the response from the Youtube Api. Provedes a convienient method of converting the
		requested data into an easily-parsable format(via .toStandard()) as well as a format compatible with the
		YoutubeDatabase SQL schema.

		Parameters
		----------
			api_response: dict, Requests.Response
				The output of the api_request. Each request will be saved in the 'items' field of a json object,
				and may contain more than on item.
	"""

	def __init__(self, api_response):
		if not isinstance(api_response, dict):
			status_code = api_response.status_code
			api_response = api_response.json()
			api_response['statusCode'] = status_code
		self.response = api_response
		_decoded_response = self._decodeResponse(api_response)
		self.summary = _decoded_response['responseSummary']
		self.items = _decoded_response['responseItems']
		self.endpoint = _decoded_response['responseEndpoint']

	def __bool__(self):
		return self.status

	def __str__(self):
		item_id = self.summary['responseId']
		string = "ApiResponse('{}', '{}')".format(self.endpoint, item_id)
		return string

	@staticmethod
	def _getResponseEndpoint(response):
		"""
			Determines whether the input referes to a search response from the api or an element from the api directly.
		Parameters
		----------
		response

		Returns
		-------

		"""

		response_type = response['kind']
		default_endpoints = {
			'youtube#channelListResponse':      'channels',
			'youtube#playlistListResponse':     'playlists',
			'youtube#playlistItemListResponse': 'playlistItems',
			'youtube#subscriptionListResponse': 'subscriptions',
			'youtube#videoListResponse':       'videos'
		}

		if response_type in default_endpoints:
			response_endpoint = default_endpoints[response_type]
		else:
			message = "'{}' cannot be mapped to a valid endpoint!".format(response_type)
			raise ValueError(message)

		return response_endpoint

	def _decodeResponse(self, api_response):

		# Parse Single Entity
		if isinstance(api_response, dict):
			status_code = api_response.get('statusCode', -1)
		else:
			status_code = api_response.status_code
			api_response = api_response.json()
		self.status_code = status_code
		response_items = api_response['items']

		# pprint(api_response)

		if 'error' in api_response:
			pass

		response_endpoint = self._getResponseEndpoint(api_response)

		response_items = [self._parseApiResponse(response_endpoint, item) for item in response_items]

		if response_endpoint in {'channels', 'playlists', 'videos'}:
			single_response = response_items[0]
			response_summary = {
				'responseId':       single_response['itemId'],
				'responseType':     'single' if len(response_items) == 1 else 'list',
				'responseEndpoint': response_endpoint,
				'responsePageInfo': None
			}
		else:
			response_summary = {
				'responseId':       api_response.get('id'),
				'responseType':     'list',
				'responseEndpoint': api_response['kind'],
				'responsePageInfo': self._decodePageInfo(api_response)
			}


		response_summary['rawResponse'] = api_response
		decoded_response = {
			'responseEndpoint': response_endpoint,
			'responseSummary':  response_summary,
			'responseItems':    response_items
		}

		return decoded_response

	@staticmethod
	def _decodePageInfo(api_response):
		page_info = {
			'totalResults':      api_response['pageInfo']['totalResults'],
			'nextPageToken':     api_response['nextPageToken'],
			'previousPageToken': api_response.get('prevPageToken'),
			'etag':              api_response['etag'],
			'kind':              api_response['kind']
		}
		return page_info

	@staticmethod
	def _parseApiResponse(response_type, api_response):
		"""
			Validates the response from the api and ensures each argument is of the correct datatype.
		Returns
		-------
			dict, list<dict>
		"""
		content_details = api_response.get('contentDetails')
		snippet = api_response.get('snippet')
		statistics = api_response.get('statistics')
		topic_details = api_response.get('topicDetails')

		if response_type == 'channels':
			item_id = api_response['id']
			result = {
				'itemId':                 item_id,
				'itemType':               response_type,
				'channelCountry':         snippet['country'],
				'channelUrl':             snippet['customUrl'],
				'channelDescription':     snippet['description'],
				'channelName':            snippet['title'],
				'channelCreationDate':    snippet['publishedAt'],
				'channelCommentCount':    statistics['commentCount'],
				'channelSubscriberCount': statistics['subscriberCount'],
				'channelVideoCount':      statistics['videoCount'],
				'channelViewCount':       statistics['viewCount'],
				'channelTopicCategories': topic_details['topicCategories'],
				'channelTopicIds':        topic_details['topicIds']
			}

		elif response_type == 'playlists':
			item_id = api_response['id']
			result = {
				'itemId':               item_id,
				'itemType':             response_type,
				'playlistName':         snippet['title'],
				'playlistItemCount':    content_details['itemCount'],
				'channelId':            snippet['channelId'],
				'channelName':          snippet['channelTitle'],
				'playlistDescription':  snippet['description'],
				'playlistCreationDate': snippet['publishedAt'],
			}

		elif response_type == 'playlistItems':
			item_id = api_response['id']

			playlist_item_id = snippet['resourceId']['videoId']
			playlist_item_kind = snippet['resourceId']['kind'].replace('youtube#', '')
			result = {
				'itemId':           item_id,
				'itemType':         response_type,
				'playlistItemId':   playlist_item_id,
				'playlistItemKind': playlist_item_kind,
				'channelId':        snippet['channelId'],
				'channelName':      snippet['channelTitle'],
				'itemDescription':  snippet['description'],
				'playlistId':       snippet['playlistId'],
				'itemCreationDate': snippet['publishedAt'],
				'playlistItemName': snippet['title']
			}
		elif response_type == 'subscriptions':
			item_id = api_response['id']
			subscription_id = snippet['resourceId']['channelId']
			subscription_type = snippet['resourceId']['kind'].replace('youtube#', '')
			result = {
				'itemId':                   item_id,
				'itemType':                 response_type,
				'subscriptionType':         subscription_type,
				'subscriptionId':           subscription_id,
				'subscriptionName':         snippet['title'],
				'subscriptionCreationDate': snippet['publishedAt'],
				'subscriptionItemCount':    content_details['totalItemCount']
			}
		elif response_type == 'videos':
			item_id = api_response['id']
			result = {
				'itemType':           response_type,
				'itemId':             item_id,
				'videoDuration':      content_details['duration'],
				'videoCategory':      snippet['categoryId'],
				'channelId':          snippet['channelId'],
				'channelName':        snippet['channelTitle'],
				'videoDescription':   snippet['description'],
				'videoLiveBroadcast': snippet['liveBroadcastContent'],
				'videoCreationDate':  snippet['publishedAt'],
				'videoTags':          snippet['tags'],
				'videoName':          snippet['title'],
				'videoCommentCount':  statistics['commentCount'],
				'videoDislikeCount':  statistics['dislikeCount'],
				'videoFavoriteCount': statistics.get('favoriteCount', 0),
				'videoLikeCount':     statistics['likeCount'],
				'videoViewCount':     statistics['viewCount']
			}
		else:
			message = "Cannot parse and item of type '{}'".format(response_type)
			raise ValueError(message)
		return result

	def toStandard(self):
		if self.summary['responseType'] == 'single':
			standard_response = self.items[0]
		else:
			standard_response = self.items
		return standard_response

	def toSqlEntity(self, **kwargs):
		"""
			Converts the data contained in the api response to a dict
			compatible with the YoutubeDatabase schema. The output can be directly used
			to update the database objects.
		Parameters
		----------
		kwargs
			Adds SQL relationships in the output. Includes:
			'channel': A 'channel' object
			'playlist': A 'playlist' object


		Returns
		-------
			dict

		"""
		standard_response = self.toStandard()

		if self.endpoint == 'video':
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
		elif self.endpoint == 'channel':
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
		elif self.endpoint == 'playlist':
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
				'input':              {
					'kwargs': kwargs
				},
				'inFunction':         "ApiResponse.toEntity",
				'errorMessage':       str(exception),
				'apiResponseSummary': self.summary,
				'entity':             entity,
				'response':           standard_response
			}
			pprint(error_information)
			raise exception

		if self.endpoint == 'video' or self.endpoint == 'playlist':
			channel = kwargs.get('channel')
			sql_entity_args['channel'] = channel

		if 'tags' not in sql_entity_args:
			sql_entity_args['tags'] = list()

		return sql_entity_args

	@property
	def status(self):
		status_code = self.status_code
		# status_code = self.api_response.status_code

		return status_code == 200

	def toFile(self, filename):

		filetype = filename.split('.')[-1]

		data = self.toStandard()

		if filetype == 'json':
			data_string = json.dumps(data, indent = 4, sort_keys = True)
		elif filetype == 'yaml':
			data_string = yaml.dump(data, default_flow_style = False, indent = 4)
		else:
			raise NotImplementedError

		with open(filename, 'w') as file1:
			file1.write(data_string)

