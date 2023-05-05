# Google Podcast Summarizer

Google Podcast Summarizer is a Python application that leverages OpenAI's GPT-4 and the Whisper ASR API to generate transcripts and summaries of Google Podcast episodes. It uses Streamlit for the web interface and Beautiful Soup for web scraping.

## Features

- Downloads a Google Podcast episode as an mp3 file
- Splits the downloaded episode into smaller segments
- Transcribes the audio segments using OpenAI's Whisper ASR API
- Indexes the transcriptions using GPT-4 language model
- Generates a summary based on user-provided prompts

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/google-podcast-summarizer.git
```

2. Change into the directory:
```bash
cd google-podcast-summarizer
```

3. Install the required packages:
```bash
pip install -r requirements.txt
```

## Usage

1. Run the Streamlit app:
```bash
streamlit run app.py
```

2. Open the provided URL in your browser and follow the on-screen instructions.

3. Input your OpenAI API key, a Google Podcast episode URL, and a prompt for the summarization.

4. Click the 'Transcript' button to generate the transcript and then click the 'Create Index' button to index the transcriptions.

5. Click the 'Query' button to generate the summary based on your prompt.

## Dependencies

- streamlit
- beautifulsoup4
- requests
- openai
- pydub

Note: The application requires a valid OpenAI API key to function correctly.

## Live Demo

[![Google Podcast summarizer](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://oldcats-summarize-podcast-app-dmsw9u.streamlit.app/)

## Screen Recording
![image](streamlit-app-demo.gif)