import streamlit as st
from bs4 import BeautifulSoup
import re
import openai
import requests
from pydub import AudioSegment
import os

from langchain.text_splitter import CharacterTextSplitter
from llama_index.node_parser import SimpleNodeParser
from llama_index import Document
from llama_index import GPTSimpleVectorIndex


# Whishper api
def transcript(file_name):
    openai.api_key = st.session_state['OPEN_AI_APIKEY']
    audio_file = open(file_name, 'rb')
    
    try:
        transcript_text = openai.Audio.transcribe('whisper-1', audio_file).text
    except openai.error.AuthenticationError as e:
        return e
    
    except Exception as e:
        return e

    else:
        with open(f'./{file_name}.txt', 'w', encoding='utf-8') as out:
            out.write(transcript_text)    

        return transcript_text


def merged_transcript(output_folder_path, TOKEN):
    
    files = os.listdir(output_folder_path)
    files = sorted(files)

    text = ''

    for file in files:
        file_path = os.path.join(output_folder_path, file)
        print(file, file_path)
        
        temp = transcript(file_path, TOKEN)

        print(temp)
        print(text, '\n')

        text += temp

    return text        


# Create index
def create_index(transcript_text):
    
    if st.session_state['index'] == '':
        # split text
        splitter = CharacterTextSplitter(        
            separator = " ",
            chunk_size = 200,
            chunk_overlap  = 20,
            length_function = len,
        )
        texts = splitter.split_text(transcript_text)

        # create nodes
        parser = SimpleNodeParser(text_splitter=splitter)
        docs = [Document(x) for x in texts]
        nodes = parser.get_nodes_from_documents(docs)

        # create index
        os.environ["OPENAI_API_KEY"] = st.session_state['OPEN_AI_APIKEY']
        st.session_state['index'] = GPTSimpleVectorIndex([])
        st.session_state['index'].insert_nodes(nodes)
    
    else:
        st.write('Already indexed.')

    return st.session_state['index']


def download_mp3(url, file_name):
    # Specify the URL and the path where the episodes should be downloaded
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

    # Fetch each episode and write the file
    podcast = requests.get(url)
    with open(rf'{out_dir}/{file_name}', 'wb') as out:
        out.write(podcast.content)    
    
    episode_info = f'{name}, {date}'
    return episode_info
    
    
def split_audio_file(input_file_path, segment_length, output_folder_path):

    # Initialize output_folder
    if not os.path.exists(output_folder_path):
        os.mkdir(output_folder_path)

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

def check_api_key(TOKEN):
    try:
        openai.api_key = TOKEN
        response = openai.Completion.create(
            engine = 'text-davinci-002',
            prompt = 'test api key',
            max_tokens = 10,
            n = 1,
            stop = None, 
            temperature=0.5
        )
        return True
        
    except Exception as e:
        error_message = "Error" + str(e) + '\n'
        return error_message


def progress(progress_bar, progress_text, progress):
    progress_bar.progress(progress, text=progress_text)

    return progress_bar
    

def main():

    if 'button_transcript' not in st.session_state:
        st.session_state['button_transcript'] = False
    if 'button_create_index' not in st.session_state:
        st.session_state['button_create_index'] = False
    if 'index' not in st.session_state:
        st.session_state['index'] = ''
    if 'button_query' not in st.session_state:
        st.session_state['button_query'] = False
    if 'response' not in st.session_state:
        st.session_state['response'] = ''
    

    st.write("""
    # Google Podcast Summarizer
    """)

    OPEN_AI_APIKEY = st.text_input('Enter openai [apikey](https://platform.openai.com/account/api-keys):', 'sk-......')

    if 'is_valid' not in st.session_state:
        st.session_state['is_valid'] = check_api_key(OPEN_AI_APIKEY)

    example_url = 'https://podcasts.google.com/feed/aHR0cHM6Ly9mZWVkcy5zb3VuZG9uLmZtL3BvZGNhc3RzL2UwYmFjYTk4LTQ5MGQtNGY0NC04M2M5LTMyZjhlYzhlZWM0NS54bWw/episode/NDg5YTUxNTgtMmI3My00OTQwLWE5OWYtNDc4MTA2ZGM4NmQ1?sa=X&ved=0CAUQkfYCahcKEwj4zcPSwMH-AhUAAAAAHQAAAAAQLA'
    url = st.text_input('Enter the URL of a [Google podcasts](https://podcasts.google.com/) episode:', example_url)
    button_transcript = st.button('Transcript')
    
    st.divider()
    
    
    if button_transcript and check_api_key(OPEN_AI_APIKEY) == True:
        st.session_state['button_transcript'] = True
        st.session_state['OPEN_AI_APIKEY'] = OPEN_AI_APIKEY
        
        progress_bar = st.progress(0, text = 'start...')
        st.session_state['is_valid'] = check_api_key(OPEN_AI_APIKEY)
        st.divider()


        # download mp3
        progress(progress_bar, 'Downloading mp3...', 0.3)
        file_name = 'Audio.mp3'
        episode_info = download_mp3(url, file_name)
        st.session_state['episode_text'] = f'Episode: **{episode_info}** downloaded.'
        st.write(st.session_state['episode_text'])


        # split mp3, stored in dir of sliced_audio_files
        progress(progress_bar, 'Processing mp3...', 0.5)
        segment_length = 600000  # 10 minutes
        output_folder_path = "sliced_audio_files"
        split_audio_file(file_name, segment_length, output_folder_path)

        # transcript
        progress(progress_bar, 'Transcript mp3...', 0.7)
        st.session_state['transcript_text'] = transcript(file_name)

        progress(progress_bar, 'Finished. Scorll down to view transcript and summary', 1.0)

    if st.session_state['button_transcript']:
        st.subheader('Generate transcript')
        st.write(st.session_state['transcript_text'])

        st.divider()

        button_create_index = st.button('Create Index')

        if button_create_index:
            st.session_state['button_create_index'] = True
    
    if st.session_state['button_create_index']:
        progress_bar = st.progress(0, text = 'start...')
        index = create_index(st.session_state['transcript_text'])
        progress(progress_bar, 'Transcript has been indexed.', 1.0)
        
        st.divider()

        st.subheader('Prompt')
        prompt = st.text_input('', '請條列重點')
        button_query = st.button('Query')
        if button_query:
            st.session_state['button_query'] = True 
            st.session_state['response'] = index.query(prompt)
            st.write(st.session_state['response'])



    if button_transcript and check_api_key(OPEN_AI_APIKEY) != True:
        progress_bar = st.progress(0, text = 'start...')
        progress(progress_bar, 'Checking api key...', 0.1)
        st.write(check_api_key(OPEN_AI_APIKEY))


if __name__ == "__main__":

    main()