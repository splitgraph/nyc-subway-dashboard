from collections import namedtuple, defaultdict
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

# Layout
row1_1, row1_2 = st.columns((2, 3))

with row1_1:
    st.title('NYC Covid Recovery')

with row1_2:
    st.write(
        """
        ##
        Plotting subway turnstile data to show how life might be returning to normal in New York City.
        """
    )

def weeklytotals():
    data_load_state = st.text('Loading data from Splitgraph DDN...')
    with conn:
        with conn.cursor() as curs:
            curs.execute("""SELECT "turnstile-activity"."START_DATE", SUM("turnstile-activity"."TOTAL") 
                FROM "paws/nyc-transit"."turnstile-activity"
                GROUP BY "turnstile-activity"."START_DATE"
                """
            )
            result = curs.fetchall()
    
    data_load_state = st.success('Done!')

    totals = defaultdict(int)
    for (date, total) in result:
        if (total < 600000000): # there are 3 (likely) spurious spikes in the data - exclude them
            totals[date] += total
    
    data = {"DATE": [], "TOTAL": []}
    for k, v in totals.items():
        data['DATE'].append(k)
        data['TOTAL'].append(v)
    
    source = pd.DataFrame.from_dict(data)
    line_chart = alt.Chart(source).mark_line().encode(
            alt.X('DATE:T', title='Time'),
            alt.Y('TOTAL:Q', title='Weekly rides'),
        ).properties(title="MTA total weekly turnstile activity (Jan 2020-May 2022)")
        
    st.altair_chart(line_chart.configure_title(fontSize=24), use_container_width=True)
    st.write("Feburary 2020 has more than 60m weekly rides. By May 2022, we see a little over 30m.")


weeklytotals()