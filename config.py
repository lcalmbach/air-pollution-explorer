ABOUT_APP_TEXT = """This app has been developed by [Lukas Calmbach](mailto:lcalmbach@gmail.com) using 
        [Python](https://www.python.org/), [Streamlit](https://streamlit.io/) and [Altair]
        (https://altair-viz.github.io/). All sourcecode is published on [github](https://github.com/lcalmbach/ede).
        """
IMG = {'main':'./static/images/app_welcome.jpg',
        '1': './static/images/pwqmn_about.png'
}
APP_WELCOME_TEXT = """edEx allows exploring and discovering environmental data. The application is mainly aimed at the analysis of surface and groundwater quality, however most options are useful for other media as well. Data from different sources my be combined in a project, for example water quality, stream flow and temperature. All available project are listed below. Select a project at the bottom of the list and click the `Open` button.
"""
LOGO_REFERENCE: str = 'https://github.com/lcalmbach/ede/blob/main/static/images/flask.png?raw=true'
USER_MANUAL_LINK: str = 'https://ede.readthedocs.io/en/latest/'
HELP_ICON: str = 'https://img.icons8.com/offices/30/000000/help.png'

EDEX_HOME = 'p00'
default_plot_width = 600
default_plot_height = 400

LATITUDE_COLUMN = 'latitude'
LONGITUDE_COLUMN = 'longitude'
MAP_LEGEND_SYMBOL_SIZE: int = 10
MAPBOX_STYLE: str = "mapbox://styles/mapbox/light-v10"
GRADIENT: str = 'blue-green'
TOOLTIP_FONTSIZE = 'x-small'
TOOLTIP_BACKCOLOR = 'white'
TOOLTIP_FORECOLOR = 'black'

DBT_VARCHAR = 1
DBT_NON_DECIMAL = 2
DBT_DECIMAL = 3
DBT_BOOLEAN = 4
DBT_DATE = 5
DBT_LOOKUP = 6
DBT_SYSLOOKUP = 7

STAT_FUNCTIONS_LIST = ['sum','count','avg','min','max','std']