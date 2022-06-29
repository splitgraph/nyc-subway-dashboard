from collections import namedtuple
import altair as alt
import math
import pandas as pd
import streamlit as st
import psycopg2

st.set_page_config(layout="wide", page_title="NYC Public Transit", page_icon=":train:")

conn = psycopg2.connect(
    user = st.secrets["ddn"]["username"],
    password = st.secrets["ddn"]["password"],
    host = st.secrets["ddn"]["host"],
    port = st.secrets["ddn"]["port"],
    database = st.secrets["ddn"]["database"],
)

