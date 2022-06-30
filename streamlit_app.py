from collections import namedtuple, defaultdict, Counter
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


def popularstations(year):
    with conn:
        with conn.cursor() as curs:
            curs.execute(f"""
            SELECT "START_DATE", "STATION", SUM("TOTAL")
            FROM
            (SELECT
                "START_DATE",
                "STATION", 
                "TOTAL"
            FROM
                "paws/nyc-transit"."turnstile-activity"
            ) s
            WHERE to_date("START_DATE", 'MM/DD/YYYY') BETWEEN '{month}/1/{year}' AND '{month+1}/1/{year}'
            GROUP BY "START_DATE", "STATION"
            """)
            stations_by_date = curs.fetchall()
            
    data = defaultdict(int)
    for i in stations_by_date:
        data[i[1]] += i[2]
    sorted_data = dict(Counter(data).most_common(5))

    source = pd.DataFrame({
        'Station': [x for x in sorted_data.keys()],
        'Activity': [x for x in sorted_data.values()]
    })

    st.altair_chart(
        alt.Chart(source, title=f"{month}/{year}")
        .mark_bar()
        .encode(
            x=alt.X("Station", scale=alt.Scale(nice=False)),
            y=alt.Y("Activity:Q", title='Turnstile Activity', scale=alt.Scale(domain=[0, 15000000])),
            tooltip=["Station", "Activity"],
        )
        .configure_mark(opacity=0.2, color="red")
        .configure_title(fontSize=36),
        use_container_width=True,
    )

weeklytotals()

row2_1, row2_2 = st.columns((1,1))
with row2_1:
    st.write("""
    ## Most popular stations year over year
    """)
with row2_2:
    month = st.slider("Choose a month (Jan = 1, Feb = 2, etc. Stops at 5 b/c our data range stops May 2022)", min_value=1, max_value=5, )
row3_1, row3_2, row3_3 = st.columns((1,1,1))
with row3_1:
    popularstations(2020)
with row3_2:
    popularstations(2021)
with row3_3:
    popularstations(2022)

st.write("""
## Summary 
As of May 2022, subway ridership is slightly more than half of what it was pre-pandemic.

14th Street, Grand Central, 34th Street Herald Square remain among the most popular stations.

Ridership is growing and is higher in 2022 than 2021. However, its not where it was pre pandemic.
""")


## clean up DB connection
conn.close()