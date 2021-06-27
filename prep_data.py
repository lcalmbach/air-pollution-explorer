import pandas as pd

df = pd.read_csv("./100049.csv", sep=';')
df = df[['Datum/Zeit','PM10 (Stundenmittelwerte)','PM2.5 (Stundenmittelwerte)','O3 (Stundenmittelwerte)']]
df = df[df['PM10 (Stundenmittelwerte)'].notnull() ]
df.rename(columns = {'Datum/Zeit':'zeit', 
    'PM10 (Stundenmittelwerte)': 'PM10', 
    'PM2.5 (Stundenmittelwerte)': 'PM2.5',
    'O3 (Stundenmittelwerte)': 'O3'}
    , inplace=True)
df['zeit']=pd.to_datetime(df['zeit'])
df['station'] = 1
df.to_parquet('apox_data.pq')




