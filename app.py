import streamlit as st
# from flask import Flask, render_template, request
from bs4 import BeautifulSoup
import re
import openai
import requests
from pydub import AudioSegment
import os
import unstructured
from langchain.document_loaders import UnstructuredFileLoader

from langchain.llms import OpenAI
from langchain.chains.summarize import load_summarize_chain
from langchain.prompts import PromptTemplate
from langchain.text_splitter import RecursiveCharacterTextSplitter



# Whishper api
def transcript(file_name, TOKEN):
    openai.api_key = TOKEN
    
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


# Summary audio
def summary(transcript_text, TOKEN):
    
    # completion = openai.ChatCompletion.create(
    # model="gpt-3.5-turbo",
    # messages=[
    #     {"role": "system", "content": "摘要以下文字"},
    #     {"role": "user", "content": transcript_text}
    # ]
    # )

    # result = completion.choices[0].message.content

    llm = OpenAI(temperature=0, openai_api_key=TOKEN)
    chain = load_summarize_chain(llm, chain_type='refine', verbose=True)

    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=0)
    split_docs = text_splitter.create_documents([transcript_text])

    print(split_docs)

    return chain.run(input_documents=split_docs)


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
    with open(rf'{out_dir}\{file_name}', 'wb') as out:
        out.write(podcast.content)    
    
    episode_info = f'{name}, {date}'
    return episode_info
    
    
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
    st.write("""
    # Google Podcast Summarizer
    """)

    OPEN_AI_APIKEY = st.text_input('Enter openai [apikey](https://platform.openai.com/account/api-keys):', 'sk-......')

    example_url = 'https://podcasts.google.com/feed/aHR0cHM6Ly9mZWVkcy5zb3VuZG9uLmZtL3BvZGNhc3RzL2UwYmFjYTk4LTQ5MGQtNGY0NC04M2M5LTMyZjhlYzhlZWM0NS54bWw/episode/NDg5YTUxNTgtMmI3My00OTQwLWE5OWYtNDc4MTA2ZGM4NmQ1?sa=X&ved=0CAUQkfYCahcKEwj4zcPSwMH-AhUAAAAAHQAAAAAQLA'
    url = st.text_input('Enter the URL of a [Google podcasts](https://podcasts.google.com/) episode:', example_url)
    submit = st.button('Summarize')
    
    st.divider()
    
    if submit:
        progress_bar = st.progress(0, text = 'start...')
        progress(progress_bar, 'Checking api key...', 0.1)
        st.divider()
        
        is_valid = check_api_key(OPEN_AI_APIKEY)

        if is_valid == True:

            # download mp3
            progress(progress_bar, 'Downloading mp3...', 0.3)
            file_name = 'Audio.mp3'
            episode_info = download_mp3(url, file_name)
            st.write(f'Episode: **{episode_info}** downloaded.')


            # split mp3, stored in dir of sliced_audio_files
            progress(progress_bar, 'Processing mp3...', 0.5)
            segment_length = 600000  # 10 minutes
            output_folder_path = "sliced_audio_files"
            split_audio_file(file_name, segment_length, output_folder_path)

            # transcript
            progress(progress_bar, 'Transcript mp3...', 0.7)
            transcript_text = merged_transcript(output_folder_path, OPEN_AI_APIKEY)
            st.write('Generate transcript:')
            st.write(transcript_text)

            st.divider()

            progress(progress_bar, 'Summarizing mp3...', 0.9)
            st.write('Summary:')
            st.write(summary(transcript_text, OPEN_AI_APIKEY))

            progress(progress_bar, 'Finished. Scorll down to view transcript and summary', 1.0)

        else:
            st.write(is_valid)


if __name__ == "__main__":

    main()