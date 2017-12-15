from package import YouTube, YouTubeDatabase, github, ApiResponse
from pprint import pprint
import pandas
import os

API_KEY = github.youtube_api_key
subscriptions = github.youtube_subscriptions

filename = os.path.join(os.path.dirname(__file__), "RT_video_database.sqlite")

if __name__ == '__main__':
	print("Running Tests...")
	test_video = "FrLgREKD4kk"
	test_channel = "UCjdQaSJCYS4o2eG93MvIwqg"
	test_playlist = "PL1cXh4tWqmsEQPeLEJ5V3k5knt-X9k043"
	youtube = YouTube(API_KEY)
	
	test_parameters = {
		'id': test_video,
		'key': API_KEY,
		'part': 'snippet' 
	}
	#result = ApiResponse('video', **test_parameters)
	result = youtube.getPlaylist(test_playlist)
	#pprint(youtube.getChannel(subscriptions['RealLifeLore']))

	#pprint(result.raw_response)
	
	if True:
		test_database = YouTubeDatabase(youtube, filename = 'youtube_database')
		#print("Database Filename: ", test_database.filename)
		#pprint(subscriptions)
		for key, value in sorted(subscriptions.items()):

			#if key != 'RealLifeLore': continue
			#keys = ['Achievement Hunter', 'Funhaus', 'LetsPlay', 'Rooster Teeth']
			keys = ['RealLifeLore']
			#completed = [i for index, i in enumerate(subscriptions.keys()) if index <55]
			#if key not in completed:
			if key in keys:
				test_database.importChannel(value)



	