if __name__ == "__main__":
	import requests
	import yaml
	from pathlib import Path
	import json
	from pprint import pprint
	request_key = "PLbIc1971kgPCjKm56j_tNsetBn3PA5GaY"
	endpoints = {
		'youtube#video':        'https://www.googleapis.com/youtube/v3/videos',
		'youtube#search':       'https://www.googleapis.com/youtube/v3/search',
		'youtube#channel':      'https://www.googleapis.com/youtube/v3/channels',
		'youtube#playlist':     'https://www.googleapis.com/youtube/v3/playlists',
		'youtube#playlistItem': 'https://www.googleapis.com/youtube/v3/playlistItems',
		'youtube#activities':    'https://www.googleapis.com/youtube/v3/activities',
		'youtube#watch':         'http://www.youtube.com/watch'
	}

	default_parameters= {
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

	github_data = Path.home() / "Documents" / "GitHub" /"github_data.yaml"
	data = yaml.load(github_data.read_text())

	kind = "youtube#playlist"
	parameters = default_parameters[kind]
	endpoint = endpoints[kind]
	parameters['key'] = data['youtubeKey']
	response = requests.get(endpoint, parameters)
	response = response.json()

	Path("sample_playlist_response.json").write_text(json.dumps(response))
	Path("sample_playlist_response.yaml").write_text(yaml.dump(response))

