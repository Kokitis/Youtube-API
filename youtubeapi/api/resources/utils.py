
import yaml
from pathlib import Path

data = yaml.load(Path("/home/proginoskes/Documents/GitHub/YoutubeAPI/tests/sample_video_response.yaml").read_text())
result = parse_video_response(data['items'][0])
print(result)