import requests
from pprint import pprint

class YouTube:
    endpoints = {
        'videos': 'https://www.googleapis.com/youtube/v3/videos',
        'searchs': 'https://www.googleapis.com/youtube/v3/search',
        'channels': 'https://www.googleapis.com/youtube/v3/channels',
        'playlists': 'https://www.googleapis.com/youtube/v3/playlists',
        'playlistItems': 'https://www.googleapis.com/youtube/v3/playlistItems',
        'activities': 'https://www.googleapis.com/youtube/v3/activities',
        'watch': 'http://www.youtube.com/watch'
    }

    def __init__(self, api_key):
        self.api_key = api_key
        self.attempts = 5
        self.errors = list()

    def getChannel(self, key, raw = False):
        parameters = {
            'id': key,
            'key': self.api_key,
            'part': "snippet,statistics,topicDetails"
        }
        response = self.request('channels', **parameters)
        channel_items = list()
        if isinstance(response, dict) and 'items' in response:
            for item in response['items']:
                channel_response = self._parseChannelData(item)
                if channel_response is not None:
                    channel_items.append(channel_response)
        elif response is None:
            pass
        else:
            message = "'items' was not found in the response"
            pprint(response)
            raise KeyError(message)
        
        if len(channel_items) == 0:
            result = None 
        elif len(channel_items) == 1:
            result = channel_items[0]
        else:
            result = channel_items
        return result

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
        items = list()
        index = 0
        while True:
            index += 1
            response = self.request('search', **parameters)
            for item in response['items']:
                item_details = item['id']
                
                items.append({
                    'itemId': item_details[item_details['kind'].split('#')[1] + 'Id'],
                    'itemKind': item_details['kind']
                })

            if 'nextPageToken' not in response.keys() or len(items) == 0:
                break 
            else:
                parameters['pageToken'] = response['nextPageToken']
        
        if kind is not None:
            items = [item for item in items if item['kind'] == 'kind']
        
        return items

    

    def _parseChannelData(self, response, ignore_errors = True):
        
        response = self._validateApiResponse('channel', response)
        channel_id = response['id']
        snippet = response['snippet']
        statistics = response['statistics']

        is_valid = response['isValid']
        if is_valid:
            result = {
                # snippet
                'channelName': snippet['title'],
                'channelId': channel_id,
                'country': snippet.get('country'),
                'description': snippet['description'],
                'creationDate': snippet['publishedAt'],

                # statistics
                'subscriberCount': statistics['subscriberCount'],
                'videoCount': statistics['videoCount'],
                'viewCount': statistics['viewCount'],

                # topics
                #'topicIds': topic_details['topicIds'],
                #'topicCategories': topic_details['topicCategories'],
                'tags': []
            }
        elif ignore_errors:
            result = None 
        else:
            message = "Channel Api response was invalid!"
            raise ValueError(message)

        return result

    def getPlaylist(self, key):
        playlist_parameters = {
            'id': key,
            'key': self.api_key,
            'part': "snippet"
        }
        playlist_response = self.request('playlists', **playlist_parameters)

        items = list()
        while True:
            playlist_items_parameters = {
                'key': self.api_key,
                'playlistId': key,
                'maxResults': '50',
                'part': 'snippet'
            }
            response = self.request('playlistItems', **playlist_items_parameters)
            next_page_token = response.get('nextpageToken')
            items += response['items']
            if next_page_token is None or len(response['items']) == 0:
                break
            else:
                playlist_items_parameters['pageToken'] = next_page_token
        playlist_response = self._parsePlaylistData(playlist_response, items)
        return playlist_response

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
            'key': self.api_key
        }
        response = self.request('videos', part='snippet,statistics,contentDetails,topicDetails', **parameters)
        
        items = list()
        if response is not None:
            for item in response['items']:
                video_response = self._parseVideoData(item)
                if video_response is not None:
                    items.append(video_response)
        else:
            response = []
        
        if len(items) == 0:     result = None 
        elif len(items) == 1:   result = items[0]
        else:                   result = items

        return result
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
    def _validateApiResponse(self, kind, response):

        _checkIfValid = lambda a, b: all(a[k][1] for k in b)

        response_id = response['id']
        if kind == 'video':
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

        elif kind == 'channel':
            snippet_keys = ['title', 'country', 'description', 'publishedAt']
            snippet_types = str
            required_snippet_keys = ['title', 'publishedAt']

            statistics_keys = ['viewCount', 'videoCount', 'subscriberCount']
            required_statistics_keys = statistics_keys
            statistics_types = int

            content_details_keys = None
            content_details_types = None
            required_content_details_keys = None
        else:
            raise NotImplementedError

        snippet = response.get('snippet')
        statistics = response.get('statistics')
        content_details = response.get('contentDetails')
        topic_details = response.get('topicDetails', dict())

        # Validate Snippet

        if snippet and snippet_keys:
            validated_snippet = self._generateValidatedApiResponse(snippet, snippet_keys, snippet_types)

            snippet_is_valid = _checkIfValid(validated_snippet, required_snippet_keys)
        else:
            validated_snippet = None
            snippet_is_valid = False
        
        # Validate Statistics

        if statistics and statistics_keys:
            validated_statistics = self._generateValidatedApiResponse(statistics, statistics_keys, statistics_types)
            statistics_is_valid = _checkIfValid(validated_statistics, required_statistics_keys)
        else:
            validated_statistics = None
            statistics_is_valid = False
        
        # Validate ContentDetails
        if content_details and content_details_keys:
            validated_content_details = self._generateValidatedApiResponse(content_details, content_details_keys, content_details_types)
            content_details_is_valid = _checkIfValid(validated_content_details, required_content_details_keys)
        else:
            validated_content_details = None
            content_details_is_valid = False



        if kind == 'video':
            tags = snippet.get('tags', [])
            tags += topic_details.get('topicCategories', [])
            tags += topic_details.get('relevantTopicDetails', [])
            is_valid = snippet_is_valid and statistics_is_valid and content_details_is_valid
        elif kind == 'channel':
            tags = []
            is_valid = snippet_is_valid and statistics_is_valid
        else:
            tags = []
            is_valid  = False

        tags = [str(i).lower() for i in tags]

        result = {
            'id': response_id,
            'tags': tags,
            'isValid': is_valid,
            'snippet': snippet,
            'statistics': statistics,
            'contentDetails': content_details,
            'topicDetails': topic_details
        }
        return result


    def _parseVideoData(self, video_response, ignore_errors = True):
        """
            Returns
            -------

        """
        validated_response = self._validateApiResponse('video', video_response)

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
        base_url = self.endpoints[endpoint]

        try:
            response = requests.get(base_url, params=parameters).json()
        except Exception as exception:
            print(str(exception))
            response = {'code': 404}
        response_code = response.get('code', 200)
        """
        if response_code == 200:
            break
        elif response['code'] == 503: #Retry for these errors.
            pass 
        else:
            pprint(response)
            raise ValueError("Api returned unsupported response code '{}'!".format(response_code))
        """
        if response.get('code') is not None:
            response = None
        return response

    def get(self, kind, key):
        if kind == 'channel':
            return self.getChannel(key)
        elif kind == 'playlist':
            return self.getPlaylist(key)
        elif kind == 'tag':
            return {'string': key}
        elif kind == 'video':
            return self.getVideo(key)
