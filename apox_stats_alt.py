import streamlit as st
import pandas as pd
import json
from streamlit.report_thread import get_report_ctx

#from queries import qry
import config as cn
import tools
from st_aggrid import AgGrid

conn = {}

class Analyses:
    """
    """

    dic_analyses = [
        {'key': '1', 'name': 'summary data', 'type': 'data', 'text': """A summary table aggregates information of the underlying data. Typically the data table holds some categorical fields such as location or sample type, parameter or year
        for which quantitative fields such as waterlevel, temperature or concentration, should be summarized (aggregated). The where clause is defined in the filter.
        """, 'parameters': ['group_by_parameters','summary_parameters','summary_function']
        }, 

        {'key': '2', 'name': 'data', 'type': 'data', 'text': " "},
        
        {'key': '3', 'name': 'map plot', 'type': 'plot', 'text': " "}, 
        
        {'key': '4', 'name': 'scatter plot', 'type': 'plot', 'text': " "}, 
        
        {'key': '5', 'name': 'barchart', 'type': 'plot', 'text': " "}, 
        
        {'key': '6', 'name': 'timeseries', 'type': 'plot', 'text': " "}, 
        
        {'key': '7', 'name': 'heatmap', 'type': 'plot', 'text': " "}, 
        
        {'key': '8', 'name': 'trend_analysis', 'type': 'plot', 'text': " "}, 
        
        {'key': '9', 'name': 'phreeqc_saturation', 'type': 'plot', 'text': " "}, 
]
    
    def __init__(self):
        global conn

        self.analysis_df = pd.DataFrame(Analyses.dic_analyses)

    def show_settings(analysis, settings_meta, settings_item):
        text = ""
        if analysis == 'summary table':
            lst = settings_meta['group_by_parameters_list']
            settings_item['group_by_parameters'] = st.multiselect('Group by', lst)
            lst = settings_meta['summarized_parameters_list']
            settings_item['summarized_parameters'] = st.multiselect('Summary parameters', lst)
            lst = settings_meta['summary_functions_list']
            settings_item['summary_functions'] = {}
            for par in settings_item['summarized_parameters']:
                settings_item['summary_functions'][par] = st.selectbox(par, lst,key=par)
        if analysis == 'time series':
            pass
        return settings_item


class Edex:
    """
    Application level class holding the metadata on the application level.
    """

    def __init__(self):
        """
        initializes the project list from a file projects.json.
        """

        with open('projects.json', 'r') as myfile:
            data=myfile.read()
        
        _df = pd.DataFrame(json.loads(data))
        self.dic_projects =  dict(zip(_df['key'], _df['title_short']))
        self.projects = _df.set_index('key')
        self.num_of_projects = len(self.projects)
        self.session_id =  get_report_ctx().session_id
        self.session = self.read_session_state()
        self._num_of_datasets = 0 
        self._curr_project = {}
        self._curr_dataset = {}
        self._curr_analysis = {}

    
    @property
    def curr_project(self):
        return self._curr_project


    @curr_project.setter
    def curr_project(self, prj):
        self._curr_project = prj


    @property
    def curr_dataset(self):
        return self._curr_dataset

    @curr_dataset.setter
    def curr_dataset(self, ds):
        self._curr_dataset = ds


    @property
    def curr_analysis(self):
        return self.curr_analysis
    

    @curr_analysis.setter
    def curr_analysis(self, prj):
        self._curr_analysis = prj
    

    @property
    def num_of_datasets(self):
        if self._num_of_datasets == 0:
            sql = qry['get_all_datasets']
            result = db.get_value(conn, sql)
            self._num_of_datasets = result
        return self._num_of_datasets
    
        
    def show_about_summary(self):
        project = self.projects.loc[cn.EDEX_HOME]
        st.subheader(project.title_long)
        text = project.description.format(self.num_of_projects, self.num_of_datasets)
        st.markdown(text, unsafe_allow_html=True)


    def read_session_state(self):
        sql = f"select count(*) as result FROM public.session_state" 
        crit = f"session_id ='{self.session_id}'"
        if db.get_value(conn, sql, crit) == 0:
            sql = f"insert into public.session_state(session_id,user_id, state_json) values('{self.session_id}', 1, '{cn.DEFAULT_PRJ_JSON}')"
            db.execute_non_query(sql,conn)
        sql = f"select state_json as result FROM public.session_state"
        result = db.get_value(conn,sql,crit)
        result=json.loads(result)
        return result 


    def save_session(self, session:object):
        self.session = session
        text = json.dumps(session)
        sql = qry['save_session'].format(text,self.session_id)
        db.execute_non_query(sql, conn)


class Project:
    def __init__(self, app):
        _key = app.session['project']
        _obj = app.projects.loc[_key]
        self.app = app
        self.key = _key
        self.num_key = tools.right(_key, 2)
        self.title_short = _obj['title_short']
        self.title_long = _obj['title_long']
        self.par_table = tools.right(_key,2) + '_parameter'

        self.description = _obj['description']
        self.datasets = pd.DataFrame(_obj['datasets'])
        self.session = app.session
        self.projects = app.projects

    def show_about_summary(self):
        st.subheader(self.title_long)
        st.markdown(self.description,unsafe_allow_html=True)
        st.markdown(f"**Datasets:**")
        if self.key != 'p00':
            for ds in self.datasets:
                st.markdown(f"* {ds['title_long']}")

    def get_dataset(self):
        """
        shows the dataset selection widget in the sidebar and returns a selected dataset
        """
        dic_ds = dict(zip( list(self.datasets['key']), list(self.datasets['title_short']) ))
        result = st.sidebar.selectbox('Select a dataset', list(dic_ds.keys()),
                                        format_func=lambda x: dic_ds[x])    
        return result   


class Dataset:
    """
    holds all information and functions for a dataset object
    """

    def __init__(self, app: Edex):
        """
        initializes the datasets instance. 
        gets the dataset record from the master-project
        """

        # key si composed of project and dataset, e.g.: 01_004
        _key = app.session['dataset']
        if _key != 'home':
            #datasets defined for this project from projects.py file
            df = app.curr_project.datasets.set_index('key')
            ds = df.loc[_key]
            self.settings = ds
            self.app = app
            self.key = _key
            self.project = app.curr_project
            self.id = int(tools.right(_key, 3))
            self.table_name = f"{_key}_data"
            self.view_name = f"v{_key}_data"
            
            self.title_short = ds['title_short']
            self.title_long = ds['title_long']
            self.description = ds['description']
            self.df_analysis = pd.DataFrame(ds['analysis'])
            self.parameter_view_sql = ds['parameter_view_sql']
            self._filter = Filter(app)
            
            self.parameters_table = self.get_parameter_table()
            self.lookup_values_df = self.get_lookup_values_df()
            self.parameters_df, self.parameters_dic, self.parameters_lookup_dic, self.parameters_quant_dic = self.get_parameters()
        self.session = app.session
    
    
    @property
    def filter(self):
        return self._filter


    @filter.setter
    def filter(self, filt):
        self._filter = filt


    def get_default_analysis_values(self, analysis_key: str) -> list:
        if str(analysis_key) == '1':
            return {'group_by_parameters': [342,],
            'summary_parameters': [333,],
            'summary_functions': ['count',]}


    def get_lookup_values_df(self):
        sql = qry['lookup_codes'].format(self.project.num_key, self.id) 
        df = db.execute_query(sql, conn)
        return df
    

    def get_lookup_dic(self, category_id: int):
        df = self.lookup_values_df.loc[self.lookup_values_df['category_id'] == category_id]
        result = dict(zip(list(df['id']), list(df['name'])))
        return result



    def get_parameters(self):
        sql = qry['get_parameters'].format(self.project.par_table, self.id)
        pars_df = db.execute_query(sql, conn)
        pars_dic = dict(zip(list(pars_df['id']), list(pars_df['label_short'])))
        pars_lookup_df = pars_df[pars_df['type_id'].isin([6,7])]
        pars_lookup_dic = dict(zip(list(pars_lookup_df['id']), list(pars_lookup_df['label_short'])))
        pars_quant_df = pars_df[pars_df['type_id'].isin([2,3])]
        pars_quant_dic = dict(zip(list(pars_quant_df['id']), list(pars_quant_df['label_short'])))
        return pars_df, pars_dic, pars_lookup_dic, pars_quant_dic

    def get_parameter_table(self) -> pd.DataFrame:
        sql = self.parameter_view_sql
        pars_df = db.execute_query(sql, conn)
        return pars_df


    def get_analyses_dic(self):
        """
        dict used to fill analysis widget for this dataset
        """
        result = zip( list(self.df_analysis['type']), list(self.df_analysis['name']) )
        return dict(result)


    def get_sel_analysis(self,key:int):
        result = self.df_analysis[self.df_analysis['type'] == key]
        return (result.loc[0].to_dict())


    def get_analysis_key(self):
        return f"{self.session['dataset']}-{self.session['analysis']}"


    def show_about_summary(self):
        st.header(self.app.curr_project.title_long)
        st.subheader(self.title_long)
        st.markdown(self.description.format(123), unsafe_allow_html=True)

        st.subheader("Parameters")
        AgGrid(self.parameters_table)


class Analysis():
    def __init__(self, app: Edex):
        self.app = app
        self.type = app.session['analysis']
        self.key = self.get_key()
        self.dataset = app.curr_dataset
        _obj = app.curr_dataset.df_analysis
        _obj = _obj.loc[_obj['type']==self.type]
        self.name = _obj['name']
        
        self.df_metadata = _obj
        self.values = {}
    

    def get_key(self):
        return f"{self.app.session['dataset']}-{self.app.session['analysis']}"


    def create_default_settings(self):
        defaults = self.dataset.get_default_analysis_values(self.type)
        default_json = json.dumps(defaults)
        sql = qry['create_user_analysis_settings'].format(default_json, self.key) 
        db.execute_non_query(sql, conn)


    def get_settings(self): 
        result = {}
        sql = qry['get_user_analysis_settings'].format(self.key)
        df = db.execute_query(sql, conn)

        if len(df) == 0:
            self.create_default_settings()
            df = db.execute_query(sql, conn)
        
        result = json.loads(df['state'][0]) 
        return result


    def save_settings(self, settings): 
        sql = qry['save_user_analysis_settings'].format(json.dumps(settings), self.key)
        db.execute_non_query(sql, conn)        


    def show_settings(self):
        """
        shows the analyisis settings, depending on the analysis type. 
        The settings are fetched via the get_settings() function, which either takes a preexisting setting for this user
        and session or generates a default records, then reads this one.
        """

        st.subheader('Analysis settings')
        self.values = self.get_settings()
        self.values['group_by_parameters'] = st.multiselect('Group parameters by', options=list(self.dataset.parameters_lookup_dic.keys()), default=self.values['group_by_parameters'],
            format_func=lambda x: self.dataset.parameters_lookup_dic[x])
        
        self.values['summary_parameters'] = st.multiselect('Summarized parameters', options=list(self.dataset.parameters_quant_dic.keys()), default=self.values['summary_parameters'],
            format_func=lambda x: self.dataset.parameters_quant_dic[x])
        
        self.values['summary_functions'] = st.multiselect('Summary functions', options=cn.STAT_FUNCTIONS_LIST, default=self.values['summary_functions'])
        self.save_settings(self.values)

    def show_result(self):
        if self.type == 1:
            self.values = self.get_settings()
            sql = "Select "
            group_by_parameters = ""
            df = self.dataset.parameters_df
            for x in self.values['group_by_parameters']:
                field_name = df.loc[df['id'] == x].iloc[0]['field_name']
                group_by_parameters += f'"{field_name}",'
            group_by_parameters = group_by_parameters.rstrip(',')
            sql += group_by_parameters + ','
            for x in self.values['summary_functions']:
                for y in self.values['summary_parameters']:
                    field_name = df.loc[df['id'] == y].iloc[0]['field_name']
                    sql += f'{x}("{field_name}") as {x}_{field_name},'
            sql = sql.rstrip(',')
            sql += f' from "{self.dataset.view_name}" group by {group_by_parameters}'
            # st.write(sql)
            df = db.execute_query(sql,conn)
            AgGrid(df)


class Filter():
    def __init__(self, app: Edex):
        self.app = app
        self.type = app.session['filter']
        self.dataset = app.curr_dataset
        self.fields = ['id', 'station_name']
    

    def create_default_settings(self):
        defaults = {"parameters":[]}
        default_json = json.dumps(defaults)
        sql = qry['create_user_filter_settings'].format(default_json, self.dataset.key) 
        db.execute_non_query(sql, conn)


    def get_settings(self): 
        result = {}
        sql = qry['get_user_filter_settings'].format(self.dataset.key)
        df = db.execute_query(sql, conn)

        if len(df) == 0:
            self.create_default_settings()
            df = db.execute_query(sql, conn)

        result = json.loads(df['state'][0]) 
        return result


    def save_settings(self, settings): 
        sql = qry['save_user_filter_settings'].format(settings, self.dataset.key)
        db.execute_non_query(sql, conn)        


    def show_settings(self):
        st.subheader('Filter')

        self.values = self.get_settings()
        self.values['parameters'] = st.multiselect('Parameters used in filter', options=list(self.dataset.parameters_dic.keys()), default=self.values['parameters'],
            format_func=lambda x: self.dataset.parameters_dic[x])
        
        idx = 0
        df = self.dataset.parameters_df
        for x in self.values['parameters']:
            par = df.loc[df['id'] == x].iloc[0]
            if par['type_id'] == 6:
                dic = self.dataset.get_lookup_dic(par['category_id'])
                self.values[x] = st.selectbox(par['label_short'], options=list(dic.keys()),
                format_func=lambda x: dic[x])
            elif par['type_id'] == 1:
                self.values[x] = st.text_input(par['label_short'], options=[])
            elif par['type_id'] == 3:
                self.values[x] = st.number_input(par['label_short'], options=[])
            
        self.save_settings(self.values)
