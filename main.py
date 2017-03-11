import os
import datetime
import isodate
import requests
import pandas
import csv
from pprint import pprint
API_KEY = "AIzaSyBAg1vti0zVI_iSuXwJ2LcJ6dAzOQfjt98"
my_channel_id = "UCZLiV1nlp-U32u0QP7Ng2Ow"
#https://console.developers.google.com/apis/credentials?project=youtubeexplorer-152313
#sample command to get subscriber count:
#https://www.googleapis.com/youtube/v3/channels?part=statistics&id=channel_id&key=your_key
my_subscriptions = {
    'Achievement Hunter': "UCsB0LwkHPWyjfZ-JwvtwEXw",
    'Ahoy': "UCE1jXbVAGJQEORz9nZqb5bQ",
    'akidearest': "UC_1HVMnw-610qx54iEiWk7A",
    'All Your History': "SWfMqbdv272gE",
    'ApollosLibrary': "UC0wBZerLDQyPwae7n5z3V0Q",
    'Beaglerush': "UCfW_QCRY30-w3nbr71bd2pg",
    'Beta64': "UCtByt51SvEuImGDC2bAiC6g",
    'Brandon Folts': "UCFrjdcImgcQVyFbK04MBEhA",
    'BroScienceLife': "UCduKuJToxWPizJ7I2E6n1kA",
    'BrownMan': "UCFbgt4fSBvjT9rKjE8qfSjw",
    'CaspianReport': "UCwnKziETDbHJtx78nIkfYug",
    'CGP Grey': "UC2C_jShtL725hvbm1arSV9w",
    'CinemaSins': "UCYUQQgogVeQY8cMQamhHJcg",
    'consumer': "UC2DYZIou2ZN-stBPv3aks6Q",
    'CrazyRussianHacker': "UCe_vXdMrHHseZ_esYUskSBw",
    'Crouton Crackerjacks': "UC_rvx8_N98wNEDXx5TIufZQ",
    'DefendtheHouse': "UC7ezYtIOQSq7_Pk7d5OVJig",
    'DidYouKnowGaming?': "UCyS4xQE6DK4_p3qXQwJQAyA",
    'Digi Bros': "UC25wd2ubLpgmbBMibeoDnCA",
    'Digibro': "UCHhnf3RgHabfk5f2gUX6EVQ",
    'Digibro After Dark': "UC1VFTzhwUTp0gArl78br2SQ"
}

def channel_request(part, channelid):
    parameters = {
        'part': part,
        'key': API_KEY,
        'id': channelid
    }
    response = request('channels', parameters)
    return response

def request(subject, parameters):
    url = "https://www.googleapis.com/youtube/v3/{subject}".format(subject = subject)
    response = requests.get(url, params = parameters)
    print(response.url)
    response = response.json()
    return response

def getChannelList(channel_id, detailed = False, pageLimit = 100):
    """ Retrieves a list of all videos uploaded by a specific channel."""
    debugMessage = "getChannelList(channel_id = {0}, detailed = {1}, pageLimit = {2}".format(channel_id, detailed, pageLimit)
    print(debugMessage)
    videoList = list()
    playlistList = list()
    pageToken = None
    search_url = "https://www.googleapis.com/youtube/v3/search"
    video_url = "https://www.googleapis.com/youtube/v3/videos"
    parameters = {
        'order': 'date',
        'part': 'snippet',
        'channelId': channel_id,
        'maxResults': 50,
        'key': API_KEY,
        'pageToken': pageToken
    }
    for index in range(pageLimit):
        response = requests.get(search_url, params = parameters).json()
        print("Page {0}, {1} videos".format(index+1, len(response['items'])))

        if len(response['items']) == 0 or 'nextPageToken' not in response.keys(): 
            videoList += [i for i in response['items'] if i['id']['kind'] == 'youtube#video']
            break
        else:
            
            videoList += [i for i in response['items'] if i['id']['kind'] == 'youtube#video']
            parameters['pageToken'] = response['nextPageToken']
    
    if detailed:
        #https://www.googleapis.com/youtube/v3/videos?id=9bZkp7q19f0&part=contentDetails&key={YOUR_API_KEY}
        statistics_parameters = {
            'part': 'statistics',
            'id': "9MxbvZ2Wd5I",
            'key': API_KEY
        }
        content_parameters = {
            'part': 'contentDetails',
            'id': '',
            'key': API_KEY
        }
        videoStatisticsList = list()
        for video in videoList:          
            video_id = video['id']['videoId']
            
            statistics_parameters['id'] = video_id
            content_parameters['id'] = video_id
            
            statistics_response = requests.get(video_url, params = statistics_parameters).json()
            content_response = requests.get(video_url, params = content_parameters).json()
            
            video['statistics'] = statistics_response['items'][0]['statistics']
            #pprint(content_response)
            video['contentDetails'] = content_response['items'][0]['contentDetails']
            
            videoStatisticsList.append(video)
        videoList = videoStatisticsList
            
    
    
    print("Found {0} videos!".format(len(videoList)))
    return videoList
#digibro_videos = getChannelList(my_subscriptions['Digibro'], detailed = True)


if __name__ == "__main__":
    print("Running main script...")
    after_dark_videos = getChannelList(my_subscriptions['Digibro After Dark'], detailed = True)
    after_dark_videos = sorted(after_dark_videos, key = lambda s: isodate.parse_duration(s['contentDetails']['duration']))
    for index, v in enumerate(after_dark_videos):
        datePublished = v['snippet']['publishedAt']
        title = v['snippet']['title']
        statistics = v['statistics']
        views = statistics['viewCount']
        duration = v['contentDetails']['duration']
        favorability = None
        try:
            likes = int(statistics['likeCount'])
            dislikes = int(statistics['dislikeCount'])
            favorability = likes / (likes + dislikes)
        except:pass
        print("{0}\t{1:<7}\t{2:.1%}\t{3:<10}\t{4}".format(datePublished, views, favorability, duration, title[:50]))
print("Finished!")
    