import yaml
from pathlib import Path
github_folder = Path.home() / 'Documents' / 'GitHub'
DATA_FOLDER:str = Path(__file__).with_name("data")
api_parameters = yaml.load((github_folder / 'github_data.yaml').read_text())
youtube_api_key = api_parameters['youtubeKey']
