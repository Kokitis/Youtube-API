import sys
import os 
from pprint import pprint
github_folder = os.path.join(os.getenv('USERPROFILE'), 'Documents', 'Github')

sys.path.append(github_folder)


from pytools import tabletools, timetools
#import pytools.tabletools as tabletools

#import pytools.timetools as timetools
#import pytools.tabletools as tabletools
from github_data import youtube_subscriptions, youtube_api_key

# Common package settings

DATA_FOLDER = os.path.join(os.path.dirname(__file__), "data")
