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
    def __init__(self, endpoint, **parameters):
        if endpoint.endswith('s'): 
            endpoint = endpoint[:-1]
        self.endpoint = endpoint
        self.parameters = parameters
        self.raw_response = self._request(**parameters)
        #print(len(self.raw_response['items']))
        if 'nextPageToken' in self.raw_response:
            self.raw_response['items'] = self._extractAllPages(**parameters)
        #print(len(self.raw_response['items']))

        self.validated_items = list()
        if self.status:
            for item in self.raw_response['items']:
                self.validated_items.append(self._validateApiResponse(item))

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

    def extractOne(self, function = None):
        #items = self.getItems(function)
        items = self.validated_items

        if len(items) == 0:     result = None 
        elif len(items) == 1:   result = items[0]
        else:                   result = items

        return result

    def _extractAllPages(self, **parameters):
        items = list()

        page_parameters = parameters
        index = 0
        while True:
            index += 1
            response = self._request(**page_parameters)
            #pprint(response)
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
        print("extractAllPages: ", len(items))
        return items

    def _request(self, **parameters):

        base_url = self.endpoints[self.endpoint + 's']

        try:
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
                pass
            _result[key] = (value, isinstance(value, key_type))
        return _result

    def _validateApiResponse(self, response):

        _expand = lambda s: {k:v[0] for k,v in s.items()}
        _checkIfValid = lambda a, b: all(a[k][1] for k in b)

        response_id = response['id']
        if self.endpoint == 'video':
            snippet_keys = [
                'videoName', 'videoId', 'channelId', 'channelTitle', 
                'description', 'defaultAudioLanguage', 'liveBroadcastContent'
                ]
            snippet_types = str
            required_snippet_keys = ['videoName', 'videoId', 'channelId', 'channelTitle', 'description']

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

            required_snippet_keys = ['id', 'title', 'channelId']
            statistics_keys = []
            required_statistics_keys = []

            content_details_keys = ['itemCount']
            required_content_details_keys = ['itemCount']

            snippet_types = [str, str, str,str,datetime.datetime, str]
            content_details_types = int
        elif self.endpoint == 'playlistItem':
            snippet_keys = []
            required_snippet_keys = []
            statistics_keys = []
            required_statistics_keys = []
            content_details_keys = []
            required_content_details_keys = []

            snippet_types = []
            statistics_types = []
            content_details_types = []
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
        else:
            tags = []
            is_valid  = False

        tags = [str(i).lower() for i in tags]

        result = {
            'id': response_id,
            'tags': tags,
            'isValid': is_valid,
            'snippet': parsed_snippet,
            'statistics': parsed_statistics,
            'contentDetails': parsed_content_details,
            'topicDetails': topic_details
        }
        return result

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


    def getChannel(self, key):
        parameters = {
            'id': key,
            'key': self.api_key,
            'part': "snippet,statistics,topicDetails"
        }
        api_response = self.request('channels', **parameters)
        api_response.extractOne()

        channel_id = api_response['snippet']['id']
        channel_name = api_response['snippet']['title']
        channel_date = api_response['snippet']['publishedAt']
        channel_country = api_response['snippet']['country']
        channel_description = api_response['snippet']['description']
        channel_subscribers = api_response['statistics']['subscriberCount']
        channel_views = api_response['statistics']['viewCount']
        channel_videos= api_response['statistics']['videoCount']


        channel = {
            'channelId': channel_id,
            'channelName': channel_name,
            'creationDate': channel_date,
            'country': channel_country,
            'description': channel_description,
            'subscriberCount': channel_subscribers,
            'viewCount': channel_views,
            'videoCount': channel_videos
        }

        return channel

    def getChannelElements(self, key, kind = None):
        """ Retrieves a list of all components on a given channel. 
            Parameters
            ----------
                key: str
                    The channel id
                kind: {'youtube#videos', 'video'}; default None
            Returns
            -------
            items: list<dict<>>
                A list of dict with the keys 'itemId' and 'itemKind'. 
                'itemKind' is one of {'youTube#video', 'youtube#playlist', 'youtube#channel'}        
        """

        #https://www.googleapis.com/youtube/v3/search?key={your_key_here}&channelId={channel_id_here}&part=snippet,id&order=date&maxResults=20]

        parameters = {
            'key': self.api_key,
            'part': 'id',
            'channelId': key,
            'maxResults': '50'
        }
        

        
        return items

    

    def _parseChannelData(self, response, ignore_errors = True):
        
        channel_id = response['id']
        snippet = response['snippet']
        statistics = response['statistics']

        is_valid = response['isValid']
        if is_valid:
            try: 
                result = {
                    # snippet
                    'channelName': snippet['title'],
                    'channelId': channel_id,
                    'country': snippet.get('country'),
                    'description': snippet['description'],
                    #'creationDate': snippet['publishedAt'],

                    # statistics
                    'subscriberCount': statistics['subscriberCount'],
                    'videoCount': statistics['videoCount'],
                    'viewCount': statistics['viewCount'],

                    # topics
                    #'topicIds': topic_details['topicIds'],
                    #'topicCategories': topic_details['topicCategories'],
                    'tags': []
                }
                if snippet['title'] == 'YouTube Spotlight':
                    result = None 
                else:
                    result['creationDate'] = snippet['publishedAt']
            except Exception as exception:
                print("\nSnippet\n")
                pprint(snippet)
                print("\nStatistics\n")
                pprint(statistics)
                raise exception
        elif ignore_errors:
            result = None 
        else:
            message = "Channel Api response was invalid!"
            raise ValueError(message)

        return result

    def getPlaylist(self, key):
        playlist_parameters = {
            'id': key,
            'maxResults': '50',
            'key': self.api_key,
            'part': "snippet"
        }
        api_response = self.request('playlists', **playlist_parameters)
        api_response = api_response.extractOne()
        playlist_items_parameters = {
            'key': self.api_key,
            'playlistId': key,
            'maxResults': '50',
            'part': 'snippet'
        }

        playlist_items = self.request('playlistItems', **playlist_items_parameters)
        #playlist_response['playlistItems'] = playlist_items.getItems()

        playlist_id = api_response['snippet']['id']
        playlist_name=api_response['snippet']['title']
        playlist_channel = api_response['snippet']['channel']
        playlist_videos = api_response['statistics']['videoCount']

        playlist = {
            'playlistId': playlist_id,
            'playlistnName': playlist_name,
            'playlistChannel': playlist_channel,
            'playlistVideoCount': playlist_videos,
            'playlistItems': playlist_items
        }


        return playlist

    def getPlaylistItems(self, key, playlist_key):
        parameters = {
            'key': self.api_key,
            'playlistId': playlist_key,
            'maxResults': 50,
            'part': 'snippet'
        }

        while True:
            response = self.request('playlistItems', **parameters)
            next_page_token = response['nextPageToken']
            if next_page_token is None:
                break
            else:
                playlist_items_parameters['pageToken'] = next_page_token
            

        return response

    def _parsePlaylistData(self, playlist, playlist_items):

        items = [self._parsePlaylistItemData(item) for item in playlist_items]
        playlist_id = playlist['items'][0]['id']
        playlist_snippet = playlist['items'][0]['snippet']

        playlist_response = {
            'playlistName': playlist_snippet['title'],
            'playlistId': playlist_id,
            'channelId': playlist_snippet['channelId'],
            'channelName': playlist_snippet['channelTitle'],
            'description': playlist_snippet['description'],
            'items': items
        }
        return playlist_response

    @staticmethod
    def _parsePlaylistItemData(response):
        playlist_item_id = response['id']
        snippet = response['snippet']
        # content_details = response['contentDetails']
        result = {
            'playlistItemId': playlist_item_id,
            'playlistId': snippet['playlistId'],
            'kind': snippet['resourceId']['kind'],
            'videoId': snippet['resourceId']['videoId'],
            'description': snippet['description']
        }
        return result

    def getVideo(self, key):

        parameters = {
            'id': key,
            'key': self.api_key,
            'part': 'snippet,contentDetails,statistics,topicDetails'
        }
        #response = self.request('videos', part='snippet,statistics,contentDetails,topicDetails', **parameters)
        api_response = self.request('video', **parameters)
        api_response = api_response.extractOne(self._parseVideoData)

        video_id            = api_response['snippet']['id']
        video_name          = api_response['snippet']['title']
        view_count          = api_response['statistics']['viewCount']
        like_count          = api_response['statistics']['likeCount']
        dislike_count       = api_response['statistics']['dislikeCount']
        video_date          = api_response['snippet']['publishedAt']
        video_duration      = api_response['contentDetails']['duration']
        video_channel       = api_response['snippet']['channelId']
        video_description   = api_response['snippet']['description']
        tags                = api_response['tags']


        video = {
            'videoId': video_id,
            'videoName': video_name,
            'videoViewCount': view_count,
            'videoLikeCount': like_count,
            'videoDislikeCount': dislike_count,
            'videoPublishDate': video_date,
            'videoDuration': video_duration,
            'videoChannel': video_channel,
            'videoDescription': video_description,
            'videoTags': tags
        }

        return video




    def _parseVideoData(self, video_response, ignore_errors = True):
        """
            Returns
            -------

        """
        #validated_response = self._validateApiResponse('video', video_response)
        validated_response = video_response

        video_id = validated_response['id']
        snippet = validated_response['snippet']
        statistics = validated_response['statistics']
        content_details = validated_response['contentDetails']
        tags = validated_response['tags']
        is_valid = validated_response['isValid']

        if is_valid:
            result = {
                # snippet
                'videoName': snippet['title'],
                'videoId': video_id,
                'channelId': snippet['channelId'],
                'channelTitle': snippet['channelTitle'],
                'defaultAudioLanguage': snippet.get('defaultAudioLanguage', 'n/a'),
                'description': snippet['description'],
                'liveBroadcastContent': snippet['liveBroadcastContent'],
                'publishDate': snippet['publishedAt'],
                'retrievalDate': "",
                'tags': tags,

                # statistics
                'likeCount': statistics.get('likeCount', 0),
                'dislikeCount': statistics.get('dislikeCount', 0),
                'commentCount': statistics.get('commentCount', 0),
                'viewCount': statistics['viewCount'],
                'favoriteCount': statistics['favoriteCount'],

                # content details
                'duration': content_details['duration']
            }
        else:
            if ignore_errors:
                result = None 
            else:
                message = "There was an error when parsing the raw video api resopnse."
                print("\nVideo Id\n")
                print(video_id)
                print("\nsnippet\n")
                pprint(snippet)
                print("\nstatistics\n")
                pprint(statistics)
                print("\nContent Details\n")
                pprint(content_details)
                raise ValueError(message)

        return result

    def request(self, endpoint, **parameters):

        if not endpoint.endswith('s'): endpoint += 's'

        response = ApiResponse(endpoint, **parameters)
        return response


    def get(self, kind, key):
        if kind == 'channel':
            element = self.getChannel(key)
        elif kind == 'playlist':
            element =  self.getPlaylist(key)
        elif kind == 'tag':
            element = {'string': key}
        elif kind == 'video':
            element = self.getVideo(key)
    

        return element
