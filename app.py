"""
The Environmental data explorer app allows to explorer environmental datasets. 
"""

import streamlit as st
import logging
import pandas as pd
import requests
import numpy as np

import apox_stats
import apox_info
import apox_plots
import apox_exceedance
import apox_fireworks
import config as cn
from datetime import datetime, timedelta
import config
import tools

__version__ = '0.0.8' 
__author__ = 'Lukas Calmbach'
__author_email__ = 'lcalmbach@gmail.com'
VERSION_DATE = '2021-08-01'
my_name = '🌎Luft-Qualität-Explorer-BS'
my_kuerzel = "lqx.bs"
GIT_REPO = 'https://github.com/lcalmbach/air-pollution-explorer'

APP_INFO = f"""<div style="background-color:powderblue; padding: 10px;border-radius: 15px;">
    <small>App created by <a href="mailto:{__author_email__}">{__author__}</a><br>
    version: {__version__} ({VERSION_DATE})<br>
    <a href="{GIT_REPO}">git-repo</a>
    """
MENU_DIC = {'Info': apox_info , 
    'Statistiken': apox_stats, 
    'Grafiken': apox_plots, 
    'Grenzwert Überschreitungen': apox_exceedance,
    'Feuerwerke und Feinstaub': apox_fireworks
}
LOGGING_LEVEL = logging.ERROR
logging.basicConfig(format='%(levelname) %(asctime)s %(message)s', level=LOGGING_LEVEL)


def init():
    st.set_page_config(  # Alternate names: setup_page, page, layout
        layout="wide",  # Can be "centered" or "wide". In the future also "dashboard", etc.
        initial_sidebar_state="auto",  # Can be "auto", "expanded", "collapsed"
        page_title='LQX.bs',  # String or None. Strings get appended with "• Streamlit". 
        page_icon='🌎',  # String, anything supported by st.image, or None.
    )

# @st.cache(allow_output_mutation=True)
def get_data():
    def get_most_recent_record(df):
        """
        retrieves the most recent record from the locally stored data table
        """
        
        result = df['zeit'].max().to_pydatetime()
        logging.info(f'most recent data in local table has timestamp: {result}')
        return result


    def data_is_up_to_date(df):
        """
        Verifies whether now() is not more than 2 hours ahead of the most recent record 
        in the local data table.
        """
        
        most_recent_record = get_most_recent_record(df)
        #st.write(most_recent_record)
        diff = datetime.now(tz=config.tz_GMT) - most_recent_record
        result = (diff < timedelta(hours = 1))
        logging.info(f'timediff is {diff}, data_is_up_to_date = {result}')
        return 
    

    def synch_local_data(df):
        def get_url():
            """
            Builds the url string for the OGD.bs REST-API. unfortunatley the dataset contains data until 2050, so you cannot calculate from the 
            most recent records backwards. Therefore the most recent record in the local dataframe is taken, then the number of hour difference
            from now is calculated and the respective number of hours = records calculated. not sure why the api contains the from and to dates
            as well as the number of records, since that makes the system overdetermined, but wit works
            """
            time_stamp = get_most_recent_record(df)
            most_recent_day = time_stamp.strftime('%Y-%m-%d')
            most_recent_time = time_stamp.strftime('%H')
            today = datetime.now(tz=config.tz_GMT).strftime('%Y-%m-%d')
            now = datetime.now(tz=config.tz_GMT).strftime('%H')
            delta = (datetime.now(tz=config.tz_GMT) - get_most_recent_record(df))
            total_seconds = delta.total_seconds()
            hours = int(total_seconds // 3600)
            url = f"https://data.bs.ch/api/records/1.0/search/?dataset=100049&q=datum_zeit%3A%5B{most_recent_day}T{most_recent_time}%3A00%3A00Z+TO+{today}T{now}%3A00%3A00Z%5D&rows={hours}&sort=datum_zeit&facet=datum_zeit"
            return url
        
        def extract_data(data):
            """
            converts the json string into a dataframe with only the required columns
            """
            logging.info(f'Extracting data from json string')
            data = data['records']
            try:
                df_ogd = pd.DataFrame(data)['fields']
            except :
                print(data['records'])
            # unpack records
            df_ogd = pd.DataFrame(x for x in df_ogd)
            if 'pm2_5_stundenmittelwerte_ug_m3' in (df_ogd.columns):
                df_ogd = df_ogd[df_ogd['pm2_5_stundenmittelwerte_ug_m3'] > 0]
                df_ogd.rename(columns = {'datum_zeit':'zeit', 
                    'pm10_stundenmittelwerte_ug_m3': 'pm10', 
                    'pm2_5_stundenmittelwerte_ug_m3': 'pm2_5',
                    'o3_stundenmittelwerte_ug_m3': 'o3',
                    'no2_stundenmittelwerte_ug_m3': 'nox'
                    }
                    , inplace=True)
                df_ogd = df_ogd[['zeit','pm10','pm2_5','o3','nox']]
                df_ogd['zeit'] = pd.to_datetime(df_ogd['zeit'])
                # make sure there are no duplicate records
                df_ogd = df_ogd[df_ogd['zeit'] > get_most_recent_record(df)]
                # add station id, todo: make this flexible 
                df_ogd['station'] = 1 
            else:
                df_ogd = pd.DataFrame()
            return df_ogd
        
        data = requests.get(get_url()).json()
        df_ogd = extract_data(data)

        # save data if df_ogd has data, meaning that more recent data was discovered
        if len(df_ogd) > 0:
            df = df.append(df_ogd)
            try:
                df.to_parquet(config.DATA_FILE, compression='gzip')
                logging.info(f'die neusten Daten wurden in apox_data.pq gespeichert')
            except:
                st.warning('Die neusten Daten konnten nicht gespeichert werden')
        
        df = tools.add_time_columns(df)
        return df 
    
    def get_local_data():
        df_data = pd.read_parquet(config.DATA_FILE)
        df_stations = pd.read_json('./data/stations.json')
        df_parameters = pd.read_json('./data/parameters.json')
        df_stations.set_index("id", inplace=True)
        # PM2.5 was measured since 2017 only, a few ghost records exists since 2003
        df_data['jahr'] = df_data['zeit'].dt.year    
        df_data['pm2_5'] = np.where(df_data['jahr'] > 2016, df_data['pm2_5'], np.nan)
        logging.info(f'data was read from local files')
        return df_data, df_stations, df_parameters
    
    df_data, df_stations, df_parameters = get_local_data()
    if not data_is_up_to_date(df_data):
        df_data = synch_local_data(df_data)
    return df_data, df_stations, df_parameters


def main():
    init()
    st.sidebar.markdown(f"## {my_name}")
    app = MENU_DIC[st.sidebar.selectbox("Menu", options=list(MENU_DIC.keys()))]
    #app.show_menu()
    df_data, df_stations, df_parameters = get_data()

    app = app.App(df_data.copy(deep=True), df_stations.copy(deep=True), df_parameters.copy(deep=True))
    app.show_menu()
    header_html = "<a href = 'https://lcalmbach.github.io/lqx-help/' target = '_blank'><img src='data:image/png;base64,{}' class='img-fluid' style='width:45px;height:45px;'></a><br>".format(
        tools.get_base64_encoded_image("./images/help2.jpg"))
    st.sidebar.markdown(
        header_html, unsafe_allow_html=True,
    )
    st.sidebar.markdown(APP_INFO, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
    



