from package import YouTubeDatabase, github, widgets

import os

subscriptions = github.youtube_subscriptions

filename = os.path.join(os.path.dirname(__file__), "RT_video_database.sqlite")
test_filename = os.path.join(os.path.dirname(__file__), 'test_database.sqlite')
if os.path.exists(test_filename):
	os.remove(test_filename)

if __name__ == '__main__':
	#print("Running Tests...")
	test_video = "FrLgREKD4kk"
	test_channel = 'UCkxctb0jr8vwa4Do6c6su0Q'
	test_playlist = "PL1cXh4tWqmsGfdkQofe9pEbHDE7cQyJH2"
	youtube = YouTubeDatabase(filename = test_filename)

	#youtube.importChannel(test_channel)
	#youtube.importPlaylist(test_playlist)

	
	if True:
		#subscriptions = {k:v for k,v in subscriptions.items() if v == test_channel}
		widgets.importSubscriptions(youtube, subscriptions, start_index = 0)

