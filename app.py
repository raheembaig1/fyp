import streamlit as st
import sng_parser
from pprint import pprint
from contextlib import contextmanager, redirect_stdout
from io import StringIO
from time import sleep
import speech_recognition as sr
import base64
import json
import pandas as pd
import numpy as np
from streamlit import session_state as _state
from pyvis import network as net
from stvis import pv_static
import matplotlib.pyplot as plt
import finalized_2 as instance
import processed_input as process_input
import requests 
from streamlit_lottie import st_lottie
from PIL import Image
from pyvis.network import Network
import networkx as nx
import pyrebase
from datetime import datetime

def load_animation(url):
    r = requests.get(url)
    if r.status_code != 200:
        return None
    return r.json()

def local_animation(filepath: str):
    with open(filepath, 'r') as f:
        return json.load(f)

st.set_page_config(page_title="HomeMapper", page_icon=":cyclone:", layout="wide")

# Configuration Key

firebaseConfig = {
  'apiKey': "AIzaSyB_7P-uGwj-veIRQ6r0pmvYt3icC4g5zrU",
  'authDomain': "homemapper-f7f6f.firebaseapp.com",
  'projectId': "homemapper-f7f6f",
  'databaseURL': "https://homemapper-f7f6f-default-rtdb.europe-west1.firebasedatabase.app/",
  'storageBucket': "homemapper-f7f6f.appspot.com",
  'messagingSenderId': "1066817282093",
  'appId': "1:1066817282093:web:077ea42f354a7b073558a4",
  'measurementId': "G-SVZPN84TEH"
}

# Firebase Authentication
firebase = pyrebase.initialize_app(firebaseConfig)
auth = firebase.auth()

# Database Authentication
db = firebase.database()
storage = firebase.storage()

# Authentication

st.sidebar.title("HomeMapper ")

choice = st.sidebar.selectbox('Login/Signup',['Login','Sign up']) 
email = st.sidebar.text_input("User Email")
password = st.sidebar.text_input('Password ', type = 'password')

if choice == 'Sign up':
    handle = st.sidebar.text_input('User name', value='Default')
    submit = st.sidebar.button('Create Account')

    if submit:
        try:
            user = auth.create_user_with_email_and_password(email, password)
            st.success('Account Successfully Created!')
            st.balloons()

            # Sign in
            user = auth.sign_in_with_email_and_password(email, password)
            db.child(user['localId']).child("Handle").set(handle)
            db.child(user['localId']).child("ID").set(user['localId'])
            st.title('Hello ' + handle)

        except requests.exceptions.HTTPError as e:
            error_message = e.args[0]
            error_json = json.loads(error_message.response.text)
            st.error(f"Error: {error_json['error']['message']}")


if choice == "Login":
    login = st.sidebar.checkbox('Login')
    if login:
        user = auth.sign_in_with_email_and_password(email,password)
        st.success(' Welcome')
        st.balloons()

        lottie_waves = local_animation("./waves2.json")

        def set_bg_hack_url():
            '''
            A function to unpack an image from url and set as bg.
            Returns
            -------
            The background.
            '''
            st.markdown(
                f"""
                <style>
                .stApp {{
                    background: url("./g2.gif");
                    background-size: cover
                }}
                </style>
                """,
                unsafe_allow_html=True
            )

        def sidebar_bg(side_bg):
            side_bg_ext = 'gif'
            st.markdown(
                f"""
                <style>
                [data-testid="stSidebar"] > div:first-child {{
                    background: url(data:image/{side_bg_ext};base64,{base64.b64encode(open(side_bg, "rb").read()).decode()});
                }}
                </style>
                """,
                unsafe_allow_html=True,
            )

        Header_left, header_right = st.columns([5, 3])

        with Header_left:
            st.header("IntelleTect")
            st.write('Home floor plan Designer.' )
            st.write('- Speak','  - Write','  - Design')
        set_bg_hack_url()
        side_bg = './ga.jpg'
        sidebar_bg(side_bg)
        st.write('---')

        col_left, col_right = st.columns([5, 4])

        with col_left:
            if "speech_txt" not in st.session_state:
                st.session_state['speech_txt'] = "Please enter text"

            
            def speak():
                r=sr.Recognizer()
                with sr.Microphone() as source:
                    st.write("Please Speak..")
                    audio=r.listen(source)
                    try:
                        text = r.recognize_google(audio)
                        return text
                        st.write("You said : {} ".format(text))
                        graph = sng_parser.parse(text)
                        text = st.text_area(text)
                        st.write(graph)
                        a=sng_parser.tprint(graph)
                    except: 
                        print("sorry could not recognize")

            if st.button('speak'):
                text=speak()
                st.session_state['speech_txt']= text

            info = {
                'rooms': ['washroom1','livingroom1','closet1','study1','bedroom1','bedroom2','kitchen1','balcony1'],
                'links': [
                    ['livingroom1', 'bedroom1'],
                    ['livingroom1', 'study1'],
                    ['livingroom1', 'kitchen1'],
                    ['livingroom1', 'bedroom2'],
                    ['livingroom1', 'balcony1'],
                    ['livingroom1', 'washroom1'],
                    ['livingroom1', 'closet1'],
                    ['bedroom1', 'study1'],
                    ['bedroom1', 'closet1'],
                    ['kitchen1', 'washroom1'],
                    ['bedroom2', 'washroom1'],
                    ['bedroom2', 'closet1']
                ],
                'sizes': {
                    'bedroom1': [14.67, 'SW'],
                    'bedroom2': [9.11, 'NW'],
                    'washroom1': [6.07, 'N'],
                    'balcony1': [7.60, 'SE'],
                    'livingroom1': [38.05, 'E'],
                    'kitchen1': [9.96, 'N'],
                    'closet1': [5.13, 'W'],
                    'study1': [11.32, 'S']
                }
            }

            user_input = st.text_area("Floor Plan Description", st.session_state['speech_txt'])
            graph = sng_parser.parse(user_input)
            information_extracted = process_input.process_input(user_input)
            im = instance.Generate(information_extracted)
            plt.show()
            st.image(im, width=550)
            df = pd.DataFrame({
                'Room': information_extracted['rooms'],
                'Size': [information_extracted['sizes'][room][0] for room in information_extracted['rooms']],
                'Direction': [information_extracted['sizes'][room][1] for room in information_extracted['rooms']]
            })
            df.set_index('Room', inplace=True)
            a = information_extracted['sizes']
            edited_df = st.experimental_data_editor(df)
            g = net.Network(height='500px', width='500px', heading='')
            for r in information_extracted['rooms']:
                g.add_node(r)
            for l in information_extracted['links']:
                g.add_edge(l[0], l[1])
            pv_static(g)

