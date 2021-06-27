import streamlit as st
import psycopg2
import sqlalchemy as sql
import pandas as pd
import config as cn
import tools
import db_config as dbcn
import sql_config as sql_cfg

mydb = ''


def execute_non_query(cmd: str, conn):
    mycursor = conn.cursor()
    try:
        mycursor.execute(cmd)
        conn.commit()
    except Exception as ex:
        print(ex)
        print(999)

# @st.cache(suppress_st_warning=True)
def execute_query(query, conn):
    """
    Executes a query and returns a dataframe with the results
    """
    result = pd.read_sql_query(query, conn)
    return result


# @st.cache(suppress_st_warning=True)
def get_connection():
    """Reads the connection string and sets the sql_engine attribute."""

    conn = psycopg2.connect(
    host = dbcn.DB_HOST,
    database=dbcn.DB_DATABASE,
    user=dbcn.DB_USER,
    password=dbcn.DB_PASS)

    return conn


def get_aquifer_dic(ds_id: int) -> dict:
    query = f"select id, value from code_list where dataset_id = {ds_id} and column_name = 'aquifer_type_id' order by order_key, value"
    df = execute_query(query)
    result = dict(zip(df['id'], df['value']))
    return result


def code_df_2_dict(query: str) -> dict:
    """
    Returns the station list for a given filter statement
    :param query: auery returning a dataframe with columns id, value
    :return: dict with key: id, value: value
    """

    df = execute_query(query)
    result = dict(zip(df['id'], df['value']))
    return result


def get_station_dic(ds_id: int) -> dict:
    """
    Returns the station list for a given filter statement
    :param ds_id: dataset id
    :return: station dictionary
    """

    tools.log('db.get_station_dic, start')
    query = sql_cfg.get_ds_query('station_code_list', ds_id)
    result = code_df_2_dict(query)
    tools.log('db.get_station_dic, end')
    return result


def get_parameter_dic(ds_id: int) -> dict:
    """
    Returns the parameter list for a given filter statement
    :param ds_id: dataset id
    :return: parameter dictionary
    """

    tools.log('db.get_parameter_dic, start')
    query = sql_cfg.get_gen_query('parameter_code_list').format(ds_id, '')
    result = code_df_2_dict(query)
    tools.log('db.get_parameter_dic, end')
    return result


def get_parameter_group_dic(ds_id: int) -> dict:
    """
    Returns the parameter list for a given filter statement
    :param ds_id: dataset id
    :return: parameter dictionary
    """

    tools.log('db.get_parameter_dic, start')
    query = sql_cfg.get_gen_query('parameter_group_code_list').format(ds_id, '')
    result = code_df_2_dict(query)
    tools.log('db.get_parameter_dic, end')
    return result

def get_all_codes(ds_id: int) -> dict:
    pass


def get_code_dic(ds_id: int, column_name: str) -> dict:
    """
    Returns the code list for a given filter statement
    :param ds_id: dataset id
    :return: parameter dictionary
    """

    tools.log('db.get_code_dic, start')
    query = sql_cfg.get_gen_query('code_list').format(ds_id, column_name)
    result = code_df_2_dict(query)
    tools.log('db.get_code_dic, end')
    return result


def get_code_fields_df(id: int) -> pd.DataFrame:
    """
    Returns a dataframe holding the fields used for grouping and filtering data. These fields must each have a id
    value pair

    :param id:
    :return:
    """

    tools.log('db.get_code_fields_df, start')
    query = sql_cfg.get_gen_query('filter_group_fields').format(id)
    print(query)
    df = execute_query(query).set_index('key')
    tools.log('db.get_code_fields_df, end')
    return df


def get_data_collection_dic() -> dict:
    """
    A data collction holds 1 or multiple related datasets

    :return:    dictionary of all available data collections
    """
    query = sql_cfg.get_gen_query('data_collections').format('')
    df = execute_query(query)
    result = dict(zip(df['id'], df['name_long']))

    return result

def get_dataset_dic(collection_id: int) -> dict:
    """
    A dataset holds data that will be diplayed on plots and tables

    :return:    dictionary of all available datasets
    """

    query = sql_cfg.get_gen_query('datasets').format(collection_id, '')
    df = execute_query(query)
    result = dict(zip(df['id'], df['name']))

    return result

def get_collection_info_df(id: int) -> pd.DataFrame:
    """
    data collection info is a 1 row dataframe holding all metadata on the current data collection

    :param id: id of collection
    :return: 1 row dataframe holding metadata
    """
    criteria = f'where id = {id}'
    query = sql_cfg.get_gen_query('data_collections').format(criteria)
    df = execute_query(query)
    return df


def get_dataset_info_df(id: int) -> pd.DataFrame:
    """
    Dataset info is a 1 row dataframe holding all metadata on the current dataset

    :param id: id of dataset
    :return: 1 row dataframe holding metadata
    """
    query = sql_cfg.get_gen_query('dataset').format(id)
    df = execute_query(query)
    return df


def get_distinct_values(column_name, table_name, dataset_id, criteria):
    """Returns a list of unique values from a defined code column."""

    criteria = f' WHERE {criteria} ' if criteria > '' else ''
    query = "SELECT {0} FROM {1} {2} group by {0} order by {0}".format(column_name, table_name, criteria)
    result = execute_query(query)
    result = result[column_name].tolist()
    return result

def get_value(conn, query:str, criteria: str = '') -> str:
    """
    Returns a single value.
    """

    result = ''
    try:
        criteria = f' WHERE {criteria} ' if criteria > '' else ''
        query = f"{query} {criteria}"
        result = execute_query(query, conn)['result'][0]
    except Exception as ex:
        print(ex)
    finally:
        return result

def save_db_table(table_name: str, df: pd.DataFrame):
    connect_string = f'mysql+pymysql://{dbcn.DB_USER}:{dbcn.DB_PASS}@{dbcn.DB_HOST}:{dbcn.DB_PORT}/{dbcn.DATABASE}?charset=utf8'
    sql_engine = sql.create_engine(connect_string, pool_recycle=3600)
    dbConnection = sql_engine.connect()

    try:
        frame = df.to_sql(table_name, dbConnection, if_exists='append')
    except ValueError as vx:
        print(vx)
    except Exception as ex:
        print(ex)
    else:
        print(f'Table {table_name} created successfully.')
    finally:
        dbConnection.close()


def import_bs_gwwq():
    """
    Replaces the table traffic_source with new data. Truncates first all data, then loads the all data from
    data.bs.ch in a dataframe and filters for rows with year > currentyear -2. this is to reduce the amount of data
    replaced in the target table miv.
    """
    source_file_name = 'E:/data/CH/100067_Rhein_WQ.csv'
    # cmd = "truncate table traffic_source"
    # tools.log(f'executing {cmd}')
    # execute_non_query(cmd)
    tools.log('done')
    tools.log(f'reading {source_file_name}')
    df = pd.read_csv(source_file_name, sep=';', encoding='UTF8')
    tools.log(f'{len(df)} rows read')
    # tools.log('filtering')
    # df = df[df.Year.gt(date.today().year - 2)]
    # tools.log('done')
    tools.log('saving table')
    save_db_table('bs_gwwq_source', df)
    tools.log('done')
    tools.log('appending imported rows from table traffic_source to miv')
    # mydb.cursor().callproc('daily_miv_import', [])
    tools.log('done')
    tools.log('filling time columns')
    # mydb.cursor().callproc('daily_miv_update', [])
    tools.log('done')
