
from bs4 import BeautifulSoup
import re
import requests

# Specify the URL and the path where the episodes should be downloaded
url = r'https://podcasts.google.com/feed/aHR0cHM6Ly9vcGVuLmZpcnN0b3J5Lm1lL3Jzcy91c2VyL2NrbDh3a3FkY2ptMmMwODEzZTlraHN0ZHg/episode/MWY2NDI3MmYtNGFlMC00ZmRiLTlmODEtNzk0MjZjOGFmYWNi?sa=X&ved=0CAUQkfYCahgKEwjQ2KO1x_j9AhUAAAAAHQAAAAAQ_Ag'
out_dir = r'./'


# Read the url and create soup object
r = requests.get(url)
soup = BeautifulSoup(r.content, 'html.parser')


# Get the div for this podcast episode
div = soup.find_all("div", style=True)[1]

# Get the date published
date = div.find('div', attrs={'class': 'Mji2k'}).text

# Get the name of the episode and remove invalid characters (Windows)
name = div.find('div', attrs={'class': 'wv3SK'}).text
name = re.sub('[\/:*?"<>|]+', '', name)

# Get the URL
url = div.find('div', attrs={'jsname': 'fvi9Ef'}).get('jsdata')
url = url.split(';')[1]

# Construct the File name
file_name = f'{name} ({date})'

# Fetch each episode and write the file
podcast = requests.get(url)
with open(rf'{out_dir}\{file_name}.mp3', 'wb') as out:
    out.write(podcast.content)    
