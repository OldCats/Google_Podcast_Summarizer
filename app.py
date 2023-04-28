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
        # st.write(st.session_state['episode_text'])


        # split mp3, stored in dir of sliced_audio_files
        progress(progress_bar, 'Processing mp3...', 0.5)
        segment_length = 600000  # 10 minutes
        output_folder_path = "sliced_audio_files"
        split_audio_file(file_name, segment_length, output_folder_path)

        # transcript
        progress(progress_bar, 'Transcript mp3...', 0.7)
        # st.session_state['transcript_text'] = 'This is Daniel speaking\n\n早上八點聽天下 掌握國際財經趨勢 臨時差 您好 歡迎收聽天下臨時差 TRACKGBT 的技術革新引發大家擔心 AI 會不會取代人類 影響到許多工作機會 但其實 AI 不只有搶工作 它也創造了新的人才需求 根據一家 AI 新創的說法 這個職缺年薪逼近了千萬台幣 甚至不一定要會寫程式 英文系畢業也能夠做 到底是什麼職業 人工智慧 AI 技術飆速發展 OpenAI 旗下聊天機器人 TRACKGBT 問世之後 更加深了 AI 搶人類工作的想法 但事實上 它也在不同產業創造了新的工作需求 其中一個人才詢問度飆升 未來可能會變得很常見 而且薪資優渥 由 OpenAI 前研究副總裁阿莫迪 成立的舊金山 AI 新創公司 Anthropic 最近開始徵求指令工程師暨圖書館員 工作內容將全部圍著 AI 打轉 這份工作的年薪折合台幣 介於 533 萬到 1,021 萬元之間 而且大概只有四分之一的時間 需要進辦公室 Anthropic 旗下的機器人 Cloud 還沒有開放公眾使用 但搶先試用的 AI 數據平台 Scale 認為 Cloud 會是 CHATGBT 強大的競爭對手 Anthropic 形容 Cloud 技術是世界最強大也最安全的 但也坦承大型語言模型是新型智慧 而教導機器學習帶出最佳結果的技術 目前還是處於嬰兒學步的階段 創造厲害的大型語言模型 非常需要善於下指令和教學的人才 指令工程師可以思考出指揮 AI 工具 完成各種任務的最佳方式 但為什麼需要圖書館員呢 因為必須把成果歸檔 建立工具圖書館和一組教材 讓其他工具學習指令 或是在下一次接收到任務時 懂得搜尋到完成任務需要的對應指令 這有點類似圖書館員製作索引標籤的專業 Anthropic 坦言這樣的人才有點難找 因為整個指令工程領域也才存在兩年多而已 紐約 Copy.ai 公司的指令工程師安娜 大學是英文系完全沒有理工背景 她形容自己的工作就是讓 AI 工具回應出最佳解答 實際工作的情況會是她撰寫文字訊息 然後餵給 AI 工具 久而久之 AI 工具就可以自己產出高品質 文法正確而且符合事實的部落格文章 安娜舉例 假如使用者輸入的是 幫我寫一個關於鞋子的產品描述 安娜會在後台看到這個使用者輸入的訊息 她的工作就是根據使用者提出的要求 設計餵給 AI 工具的指令 比方說要求 AI 寫有關這個產品的描述 並且提供可遵循的範例 鑽研指令程式的英國軟體開發者威利森說 自己和同儕被企業徵詢的機會真的大幅增加 因為他們現在被視為和人工智慧溝通的專家 指令工程師並不是真的使用程式語言 但精通制定準確的指令 促使 AI 工具輸出更符合需求 彷彿真的經過思考的結果 許多企業開始找這樣的人 因為需求太高 甚至已經有專門找接案指令工程師的人力平台 威利森說 為了讓各種 AI 模型發揮最大價值 指令工程師大概還會搶手好一陣子 那麼指令工程師的面試會是什麼形式呢 又怎麼確定能夠找到對的人 Anthropic 測試應徵者能力的方式是 讓他們和 Cloud 互動一陣子 展現他們可以透過厲害的指令 讓 Cloud 完成複雜的行為 徵才頁面也說 很重要的是 適合的人選必須具備有創意的駭客精神 以及熱愛解決謎團 他們同時善於溝通 具有組織意識 熱切希望讓強大的技術安全無虞 而且有利於社會 Anthropic 列出這個優渥職缺顯示 AI 或許即將取代某些工作 但同時也帶來職場新的需求 ResumeBuilder.com 網站的職場顧問霍勒說 就像過去幾十年技術持續發展 並且取代部分勞動力一樣 AI 機器人可能會影響我們的工作方式 就像所有新技術一樣 而 AI 機器人現在只是剛剛起步 霍勒以 ChatGBT 為例 他認為使用 ChatGBT 的經濟模式也在不斷發展 觀察 ChatGBT 怎麼樣幫企業節省開支 又怎麼重組企業內的人力 是一件有趣的事 以上就是今天的天下臨時差 由張詠琴編譯 我是李若梅 我們明天早上八點再見'

        progress(progress_bar, 'Finished. Scorll down to view transcript and summary', 1.0)

    if st.session_state['button_transcript']:
        st.write(st.session_state['episode_text'])
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