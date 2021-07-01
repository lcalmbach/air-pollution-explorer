"""
The Environmental data explorer app allows to explorer environmental datasets. 
"""

import streamlit as st
import logging
import pandas as pd
import requests

import apox_stats
import apox_info
import apox_plots
import config as cn
from datetime import datetime, timedelta
import config

__version__ = '0.0.1' 
__author__ = 'Lukas Calmbach'
__author_email__ = 'lcalmbach@gmail.com'
VERSION_DATE = '2021-06-12'
my_name = '🌎Air Pollution Explorer'
my_kuerzel = "apox"
GIT_REPO = 'https://github.com/lcalmbach/air-pol-ex'

APP_INFO = f"""<div style="background-color:powderblue; padding: 10px;border-radius: 15px;">
    <small>App created by <a href="mailto:{__author_email__}">{__author__}</a><br>
    version: {__version__} ({VERSION_DATE})<br>
    <a href="{GIT_REPO}">git-repo</a>
    """
MENU_DIC = {apox_info: 'Info', apox_stats: 'Statistiken', apox_plots: 'Grafiken'}
LOGGING_LEVEL = logging.ERROR
logging.basicConfig(format='%(levelname) %(asctime)s %(message)s', level=LOGGING_LEVEL)



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
        Verifies whether now() is not more than 1 hours ahead of the most recent record 
        in the local data table.
        """
        
        most_recent_record = get_most_recent_record(df)
        diff = datetime.now(tz=config.tz_GMT) - most_recent_record
        result = (diff < timedelta(hours = 1))
        logging.info(f'timediff is {diff}, data_is_up_to_date = {result}')
        return 
    

    def synch_local_data(df):
        def get_url():
            """
            Builds the url string for the OGD.bs RESTAPI. unfortunatley the dataset contains data until 2050, so you cannot calculate from the 
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
            logging.info(f'Extracting data from jason string')
            data = data['records']
            df_ogd = pd.DataFrame(data)['fields']
            
            # unpack records
            df_ogd = pd.DataFrame(x for x in df_ogd)
            if 'pm2_5_stundenmittelwerte_ug_m3' in (df_ogd.columns):
                df_ogd = df_ogd[df_ogd['pm2_5_stundenmittelwerte_ug_m3'] > 0]
                df_ogd.rename(columns = {'datum_zeit':'zeit', 
                    'pm10_stundenmittelwerte_ug_m3': 'PM10', 
                    'pm2_5_stundenmittelwerte_ug_m3': 'PM2.5',
                    'o3_stundenmittelwerte_ug_m3': 'O3'}
                    , inplace=True)
                df_ogd = df_ogd[['zeit','PM10','PM2.5','O3']]
                df_ogd['zeit'] = pd.to_datetime(df_ogd['zeit'])
                #make sure there are no duplicate records
                df_ogd = df_ogd[df_ogd['zeit'] > get_most_recent_record(df)]
                # add station id, todo: make this flexible 
                df_ogd['station'] = 1 
            else:
                df_ogd = pd.DataFrame()
            return df_ogd
        
        data = requests.get(get_url()).json()
        df_ogd = extract_data(data)

        if len(df_ogd) > 0:
            df = df.append(df_ogd)
            try:
                df.to_parquet('./data/apox_data.pq')
                logging.info(f'Most recent data was added to apox_data.pq file')
            except:
                st.warning('Aktuellste Daten konnten nicht gespeichert werden')
        # now add data
        return df 
    
    def get_local_data():
        df_data = pd.read_parquet('./data/apox_data.pq')
        df_stations = pd.read_json('./data/stations.json')
        df_parameters = pd.read_json('./data/parameters.json')
        logging.info(f'data was read from local files')
        return df_data, df_stations, df_parameters
    
    df_data, df_stations, df_parameters = get_local_data()
    if not data_is_up_to_date(df_data):
        df_data = synch_local_data(df_data)
    return df_data, df_stations, df_parameters


def main():
    app = st.sidebar.selectbox("Menu", options=list(MENU_DIC.keys()),
        format_func=lambda x: MENU_DIC[x])
    #app.show_menu()
    df_data, df_stations, df_parameters = get_data()
    app = app.App(df_data, df_stations, df_parameters)
    app.show_menu()


if __name__ == "__main__":
    main()
    



