from flask import Flask, render_template, request
from bs4 import BeautifulSoup
import re
import openai
import requests
from pydub import AudioSegment
import os


app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/', methods=['POST'])
def submit_url():
    url = request.form['url']
    message = f'您好，{url}\n'


    # download mp3
    file_name = download_mp3(url)
    message+= f'{file_name}已下載完成\n'

    # split mp3
    segment_length = 600000  # 10 minutes
    output_folder_path = "sliced_audio_files"
    split_audio_file(file_name, segment_length, output_folder_path)

    transcript_text = merged_transcript(output_folder_path)
    message+= f'\n\nTranscript:\n{transcript_text}'

    message+= f'\n\n摘要：\n{summary(file_name)}'
    
    return render_template('index.html', message=message)

# Whishper api
def transcript(file_name):
    f = open('./TOKEN', encoding='utf-8')
    openai.api_key = f.read()
    f.close()
    
    audio_file = open(file_name, 'rb')
    transcript_text = openai.Audio.transcribe('whisper-1', audio_file).text
    print(transcript_text)
    

    with open(f'./{file_name}.txt', 'w', encoding='utf-8') as out:
        out.write(transcript_text)    

    return transcript_text

def merged_transcript(output_folder_path):
    
    files = os.listdir(output_folder_path)

    text = ''

    for file in files:
        file_path = os.path.join(output_folder_path, file)
        print(file, file_path)
        
        temp = transcript(file_path)

        print(text, '\n')

        text += temp

    return text        


# Summary audio
def summary(file_name):
    with open(f'./{file_name}.txt', encoding='utf-8') as f:
        transcript_text = f.read()
    
    completion = openai.ChatCompletion.create(
    model="gpt-3.5-turbo",
    messages=[
        {"role": "system", "content": "摘要以下文字"},
        {"role": "user", "content": transcript_text}
    ]
    )

    result = completion.choices[0].message.content

    print(result)

    return result

    


def download_mp3(url):
    # Specify the URL and the path where the episodes should be downloaded
    # url = r'https://podcasts.google.com/feed/aHR0cHM6Ly9vcGVuLmZpcnN0b3J5Lm1lL3Jzcy91c2VyL2NrbDh3a3FkY2ptMmMwODEzZTlraHN0ZHg/episode/MWY2NDI3MmYtNGFlMC00ZmRiLTlmODEtNzk0MjZjOGFmYWNi?sa=X&ved=0CAUQkfYCahgKEwjQ2KO1x_j9AhUAAAAAHQAAAAAQ_Ag'
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
    # file_name = f'{name} ({date}).mp3'
    file_name = 'Audio.mp3'

    # Fetch each episode and write the file
    podcast = requests.get(url)
    with open(rf'{out_dir}\{file_name}', 'wb') as out:
        out.write(podcast.content)    
    
    return file_name
    
def split_audio_file(input_file_path, segment_length, output_folder_path):

    # Initialize output_folder
    files = os.listdir(output_folder_path)

    for file in files:
        file_path = os.path.join(output_folder_path, file)

        if os.path.isfile(file_path):
            os.remove(file_path)
    

    # Load the audio file
    audio_file = AudioSegment.from_mp3(input_file_path)

    # Calculate the total length of the audio file (in milliseconds)
    total_length = len(audio_file)

    # Initialize the starting time for slicing
    start_time = 0

    # Iterate through the audio file, incrementing the slicing length each time
    for i in range(0, total_length, segment_length):
        end_time = start_time + segment_length

        # Slice the audio file
        sliced_audio_file = audio_file[start_time:end_time]

        # Export the sliced audio file
        sliced_audio_file.export(f"{output_folder_path}/sliced_audio_{i // segment_length}.mp3", format="mp3")

        # Update the starting time for slicing
        start_time = end_time

if __name__ == '__main__':
    app.run(debug=True)

