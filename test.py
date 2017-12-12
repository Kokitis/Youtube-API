from package import YouTube, YouTubeDatabase, github
from pprint import pprint
import pandas
import os

API_KEY = github.youtube_api_key
subscriptions = github.youtube_subscriptions

filename = os.path.join(os.path.dirname(__file__), "RT_video_database.sqlite")

if __name__ == '__main__':
	test_video = "FrLgREKD4kk"
	test_channel = "UCjdQaSJCYS4o2eG93MvIwqg"
	test_playlist = "PL1cXh4tWqmsEQPeLEJ5V3k5knt-X9k043"
	youtube = YouTube(API_KEY)

	#pprint(youtube.getChannel(subscriptions['RealLifeLore'], True))
	
	if True:
		test_database = YouTubeDatabase(youtube, filename = 'roosterteeth_channels')
		print("Database Filename: ", test_database.filename)
		#pprint(subscriptions)
		for key, value in sorted(subscriptions.items()):

			#if key != 'RealLifeLore': continue
			keys = ['Achievement Hunter', 'Funhaus', 'LetsPlay', 'Rooster Teeth']
			#keys = ['RealLifeLore']
			if key in keys:
				test_database.importChannel(value)



	