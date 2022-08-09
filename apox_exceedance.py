import streamlit as st
import tools

min_number_months_measured = 8

class App:
    """
    """

    def __init__(self, df_data, df_stations, df_parameters):
        self.df_data = tools.add_time_columns(df_data)
        self.df_stations = df_stations
        self.dic_stations = df_stations['name'].to_dict()
        self.station = {}
        self.df_parameters = df_parameters

        self.start_jahr =  int(self.df_data['jahr'].min())
        self.end_jahr = int(self.df_data['jahr'].max())
        self.settings = {}
    

    def filter_data(self):
        df = self.df_data

        if 'date_from' in self.settings:
            start_series = self.df_data['datum'].min().to_pydatetime().date()
            end_series = self.df_data['datum'].max().to_pydatetime().date()
            if self.settings['date_from'] > start_series or self.settings['date_to'] < end_series:
                df = df[(df['zeit'].dt.date >= self.settings['date_from']) & (df['zeit'].dt.date <= self.settings['date_to'])]
        if 'years' in self.settings:
            if self.settings['years'][0] != self.start_jahr or self.settings['years'][1] != self.end_jahr:
                df = df[df['jahr'].isin(range(self.settings['years'][0], self.settings['years'][1]))]
        return df


    def get_years_with_monthly_data(self,df,par):
        min_number_months_measured = 8

        df = df.groupby(['jahr','monat'])[par].agg(['count'])
        df = df[df['count']>0].reset_index()
        df = df.groupby(['jahr'])['count'].agg(['count']).reset_index()
        
        df = df[df['count'] > min_number_months_measured].reset_index()
        return(df['jahr'].unique().tolist())


    def analyse_exceedances(self, gl, par, rec, df):
        def analyse_year(df):
            def get_text():
                first_value = df['jahr'].min()
                last_value = df['jahr'].max()
                min_year = first_value if first_value > self.settings['years'][0] else self.settings['years'][0]
                max_year = last_value if last_value < self.settings['years'][1] else self.settings['years'][1]
                years = len(df[df['exceedance'] > 0])
                text = f"""In den Jahren {min_year} bis {max_year} wurde der Grenzwert für 
                {rec['name_long']} in {years} Jahren überschritten. Überschreitungen des Jahresgrenzwerts werden nur in Jahren ausgewiesen,
                in welchen während mindestestens {min_number_months_measured} Monaten gemessen wurde."""
                return text
            
            def get_cols():
                cols = []
                cols.append({'name':'Jahr', 'type':["numericColumn","numberColumnFilter","customNumericFormat"], 'precision':0})
                cols.append({'name':'Mittelwert', 'type':["numericColumn","numberColumnFilter","customNumericFormat"], 'precision':1})
                cols.append({'name':'Anzahl Messungen', 'type':["numericColumn","numberColumnFilter","customNumericFormat"], 'precision':0})
                cols.append({'name':'Abweichung vom Grenzwert', 'type':["numericColumn","numberColumnFilter","customNumericFormat"], 'precision':1})
                return cols

            df = df.groupby([gl['time_agg_field']])[par].agg(['mean', 'count']).reset_index()
            years_with_monthly_data = self.get_years_with_monthly_data(self.df_data, par)
            df = df[df[gl['time_agg_field']].isin(years_with_monthly_data)]
            df['exceedance'] = df['mean'] - gl['value']
            figure_text = get_text()
            df = df[df['exceedance'] > 0]
            df = df.rename(columns={'jahr':'Jahr', 'mean': 'Mittelwert', 'count': 'Anzahl Messungen', 'exceedance': 'Abweichung vom Grenzwert'} )
            
            return df, get_cols(), figure_text

        def analyse_day(df):
            def get_text():
                first_value = df['jahr_'].min()
                last_value = df['jahr_'].max()
                min_year = first_value if first_value > self.settings['years'][0] else self.settings['years'][0]
                max_year = last_value if last_value < self.settings['years'][1] else self.settings['years'][1]
                years = last_value - first_value + 1
                max_exceedance_year_record = df.nlargest(1, columns=['is_exceedance_sum'])
                max_exceedance_year = max_exceedance_year_record.iloc[0]['jahr_']
                max_exceedances = max_exceedance_year_record.iloc[0]['is_exceedance_sum']
                if 'max_exceedances' in gl:
                    no_exceedance = len(df[df['is_exceedance_sum'] > gl['max_exceedances']])
                    allowed_exceedances = f"""Pro Jahr darf der Grenzwert ({gl['value']}{rec['unit']}) höchstens {gl['max_exceedances']} Mal überschritten werden. Dieser 
                    Wert wurde in {no_exceedance} von {years} Jahren überschritten. Am meisten Überschreitungen ({max_exceedances:,.0f}) gab es im Jahr {max_exceedance_year:.0f}."""
                else:
                    no_exceedance = len(df[df['is_exceedance_sum'] > 1])
                    allowed_exceedances = ""
                
                text = f"""In den Jahren {min_year} bis {max_year} wurde der Grenzwert für 
                    {rec['name_long']} in {no_exceedance} Jahren überschritten. {allowed_exceedances}"""
                return text

            def get_cols():
                cols = []
                cols.append({'name':'Jahr', 'type':["numericColumn","numberColumnFilter","customNumericFormat"], 'precision':0})
                cols.append({'name':f"Anz<{gl['value']}", 'type':["numericColumn","numberColumnFilter","customNumericFormat"], 'precision':0})
                cols.append({'name':f"Anz>={gl['value']}", 'type':["numericColumn","numberColumnFilter","customNumericFormat"], 'precision':0})
                cols.append({'name':'Überschreitungen(%)', 'type':["numericColumn","numberColumnFilter","customNumericFormat"], 'precision':1})
                return cols

            df = df.groupby(['jahr',gl['time_agg_field']])[rec['name_short']].agg(['mean', 'count']).reset_index()
            df['exceedance'] = df['mean'] - gl['value']
            df['is_exceedance'] = df['exceedance'].apply(lambda val: 1 if val > 0 else 0)
            df['no_exceedance'] = abs(df['is_exceedance'] - 1)
            
            df = df.groupby(['jahr'])['exceedance','no_exceedance','is_exceedance',].agg(['sum']).reset_index()
            df['pct_exceedances'] = df['is_exceedance'] / (df['no_exceedance'] + df['is_exceedance']) * 100
            df.columns = df.columns.map('_'.join)
            figure_text = get_text()
            df = df[df['is_exceedance_sum'] > gl['max_exceedances']]
            df = df.rename(columns={'jahr_':'Jahr', 'no_exceedance_sum': f"Anz<{gl['value']}", 'is_exceedance_sum': f"Anz>={gl['value']}", 'pct_exceedances_':'Überschreitungen(%)'} )
            df = df[['Jahr', f"Anz<{gl['value']}", f"Anz>={gl['value']}",'Überschreitungen(%)']]
            
            return df, get_cols(), figure_text

        def analyse_hour(df):
            def get_text():
                if gl['max_exceedances'] > 0:
                    col = f"Anz>={gl['value']}"
                    exceedances_hours = df[col].sum()
                    no_exceedance = len(df[df[col]>gl['max_exceedances']])
                    allowed_exceedances = f"""Pro Jahr darf der Grenzwert höchstens {gl['max_exceedances']} Mal überschritten werden. Der 
                    Grenzwert wurde in {no_exceedance} von {len(df)} Jahren überschritten."""
                else:
                    allowed_exceedances = ""
                text = f"""In den Jahren {self.settings['years'][0]} bis {self.settings['years'][1]} wurde der Grenzwert für 
                {rec['name_long']} in {len(df)} Jahren und insgesamt während {exceedances_hours} Stunden überschritten. {allowed_exceedances}"""
                return text

            def get_cols():
                cols = []
                cols.append({'name':'Jahr', 'type':["numericColumn","numberColumnFilter","customNumericFormat"], 'precision':0})
                cols.append({'name':f"Anz<{gl['value']}", 'type':["numericColumn","numberColumnFilter","customNumericFormat"], 'precision':0})
                cols.append({'name':f"Anz>={gl['value']}", 'type':["numericColumn","numberColumnFilter","customNumericFormat"], 'precision':0})
                cols.append({'name':'Überschreitungen(%)', 'type':["numericColumn","numberColumnFilter","customNumericFormat"], 'precision':1})
                return cols

            df = df[['jahr', rec['name_short']]]
            df['exceedance'] = df[rec['name_short']] - gl['value']
            df['is_exceedance'] = df['exceedance'].apply(lambda val: 1 if val > 0 else 0)
            df['no_exceedance'] = abs(df['is_exceedance'] - 1)
            
            df = df.groupby(['jahr'])['exceedance','no_exceedance','is_exceedance',].agg(['sum']).reset_index()
            df['pct_exceedances'] = df['is_exceedance'] / (df['no_exceedance'] + df['is_exceedance']) * 100
            df.columns = df.columns.map('_'.join)
            df = df.rename(columns={'jahr_':'Jahr', 'no_exceedance_sum': f"Anz<{gl['value']}", 'is_exceedance_sum': f"Anz>={gl['value']}", 'pct_exceedances_':'Überschreitungen(%)'} )
            df = df[['Jahr', f"Anz<{gl['value']}", f"Anz>={gl['value']}",'Überschreitungen(%)']]
            return df, get_cols(), get_text()
        st.markdown(f"#### Überschreitungen: {gl['legend']} für {rec['name_long']}: {gl['value']} {rec['unit']}")
        if gl['time_agg_field'] == 'jahr':
            df, cols, text = analyse_year(df)
        elif gl['time_agg_field'] == 'datum':
            df, cols, text  = analyse_day(df)
        elif gl['time_agg_field'] == 'stunde':
            df, cols, text  = analyse_hour(df)
        
        if len(df)>0:
            col1, col2 = st.columns(2)
            with col1:
                tools.show_table(df, cols, tools.get_table_settings(df))
            with col2:
                st.markdown(text)
        else:
            st.markdown(text)
        

    def show_exceedance(self, df):
        for par in self.parameters:
            rec = self.df_parameters[par]
            for gl in rec['guidelines']:
                self.analyse_exceedances(gl, par, rec, df)


    def show_menu(self):
        _station_id = st.sidebar.selectbox('Station', list(self.dic_stations.keys()),
            format_func=lambda x: self.dic_stations[x])    
        self.parameters = st.sidebar.multiselect("Parameter",options = list(self.df_parameters.columns), default=list(self.df_parameters.columns))
        self.settings['years'] = st.sidebar.slider('Jahr', self.start_jahr, self.end_jahr, (self.start_jahr, self.end_jahr))
        df = self.filter_data()
        self.show_exceedance(df)

        
    