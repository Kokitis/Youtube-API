import sys
import os 

github_folder = os.path.join(os.getenv('USERPROFILE'), 'Documents', 'Github')

sys.path.append(github_folder)

import pytools.tabletools as tabletools 
import pytools.timetools as timetools
from github_data import youtube_subscriptions, youtube_api_key