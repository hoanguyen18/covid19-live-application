#!/usr/bin/env python
# coding: utf-8

# In[1]:


import dash
from dash import dcc, html, Dash
#from jupyter_dash import JupyterDash
from dash.dependencies import Input, Output
import dash_bootstrap_components as dbc

from dash_bootstrap_templates import load_figure_template

import plotly.express as px
import pandas as pd
from datetime import datetime, timedelta


# In[2]:


# URL to external CSS file
dbc_css = 'https://cdn.jsdelivr.net/gh/AnnMarieW/dash-bootstrap-templates@V1.0.2/dbc.min.css'


# # COVID-19 dashboard
# 
# This notebook downloads data on COVID-19 from [Our World in Data](https://github.com/owid/covid-19-data/tree/master/public/data). Data on deaths, cases and vaccinations are used to build a `Dash` application that replicates some of the features of the COVID-19 dashboard by the [WHO](https://covid19.who.int/).
# 
# The notebook consists of two parts. The first part extracts and wrangles the data into a format that is suitable for the data visualization in our dashboard. The second part creates the actual application.

# ### 1. Extract and wrangle data

# In[3]:


# Load data
url = 'https://covid.ourworldindata.org/data/owid-covid-data.csv'
cols_lst = ['iso_code', 
            'location', 
            'continent',
            'date', 
            'new_cases', 
            'total_cases',
            'total_cases_per_million',
            'new_deaths', 
            'total_deaths',
            'total_deaths_per_million',
            'people_fully_vaccinated',
            'total_vaccinations_per_hundred',
            'people_vaccinated_per_hundred',
            'new_vaccinations']
df = pd.read_csv(url, usecols = cols_lst)

# Convert date to datetime
df['date'] = pd.to_datetime(df['date'], format = '%Y-%m-%d')

df.head()


# There are many NaN's in the data (especially for vaccinations). We will assume that in the columns `new_deaths`, `new_cases` and `new_vaccinations`, a NaN can be interpreted as a zero.

# In[4]:


#df.isna().sum()


# In[5]:


# Replace NaN with 0 in columns: new_deaths, new_cases and new_vaccinations
for col in ['new_deaths', 'new_cases', 'new_vaccinations']:
    df[col].fillna(0, inplace = True)


# In addition to countries, the data also contains aggregates, e.g. continents. 
# 
# We filter the observations for the world and store it in a variable called `df_world`.

# In[6]:


#df[df['continent'].isna()]


# In[7]:


# Extract world
df_world = df[df['location'] == 'World'].copy()

df_world.head()


# #### Feature 1
# 
# For feature 1, we use `df_world` to extract the global totals.
# 
# But notice that there are NaNs in the data, especially for vaccination data. We therefore extract the last known observation in each column.

# In[8]:


#df_world[df_world['people_fully_vaccinated'].isna()]


# In[9]:


# Extract the last known observation in each column
df_world_tot = df_world.groupby('location').last().copy()

# Extract totals
tot_deaths = int(df_world_tot['total_deaths'])
tot_cases = int(df_world_tot['total_cases'])
tot_vac = int(df_world_tot['people_fully_vaccinated'])

print('Total deaths: {:,}'.format(tot_deaths))
print('Total cases: {:,}'.format(tot_cases))
print('People fully vaccinated: {:,}'.format(tot_vac))


# #### Feature 3
# 
# For feature 3, we again use `df_world`, but now we want to calculate the weekly sums of new deaths, cases and vaccinations.

# In[10]:


# Set index to date
df_world.set_index('date', inplace = True)

# Use resample method to sum each column by week
df_world_week = df_world.resample('W').sum().reset_index()

df_world_week.head()


# We create a function called `plot_bar` that returns a bar plot of a given column in `df_world_week`.

# In[11]:


def plot_bar(col_name, data = df_world_week):
    
    fig = px.bar(
        data, 
        x = 'date', 
        y = col_name,
        labels = {'date' : 'Date', col_name : 'Week sum'}
    )
    
    fig.update_layout(
        xaxis_title = None, 
        yaxis_title = None, 
        margin =  {'t' : 0, 'b' : 0, 'r' : 0, 'l' : 0},
        height = 300
    ) 
    
    return fig

plot_bar('new_vaccinations')


# #### Feature 2
# 
# For feature 2, we use `df` to extract the most recent data for each location in the world.

# In[12]:


# Extract the most recent observations (that are not NaN) for each location
df_last = df.groupby('location').last().reset_index()

df_last.head()


# We drop aggregates so that we are left with only countries.

# In[13]:


# Drop aggregates (missing continent info)
df_last = df_last[~df_last['continent'].isna()].copy()

print('Number of unique countries: ', df_last['location'].nunique())


# In[14]:


# Notice that there are still some countries that we lack info on
#df_last.isna().sum()


# In[15]:


# However, these countries tend to be small island states with very little covid
# (So we are not too worried about lacking data for these locations)
#df_last[df_last['total_deaths'].isna()]


# We create a function called `plot_map` that returns a world map for a given column in `df_last`.

# In[16]:


def plot_map(col_name, data = df_last):
    
    fig = px.choropleth(
        data, 
        locations = 'iso_code',
        color = col_name,
        scope = 'world',
        hover_name = 'location',
        hover_data = {'iso_code' : False},
        labels = {col_name : 'value'}
    )
    
    fig.update_layout(margin = {'r' : 0, 't' : 0, 'l' : 0, 'b' : 0})
    
    fig.update_layout(
        coloraxis_colorbar_title_text = None,
        coloraxis_showscale = True,
        geo = {'showframe' : False}
    )

    return fig

#plot_map('total_deaths')


# In[ ]:





# ### 2. Create the dashboard

# #### Feature 1
# 
# The global totals are stored in the variables `tot_deaths`, `tot_cases` and `tot_vac`, and they are displayed inside `Card` components.

# In[17]:


deaths_card = dbc.Card(
    children = [
        html.H4('Total deaths'),
        html.H2('{:,}'.format(tot_deaths))
    ], 
    body = True,
)

cases_card = dbc.Card( 
    children = [
        html.H4('Total cases'),
        html.H2('{:,}'.format(tot_cases))
    ], 
    body = True,
)

vac_card = dbc.Card(
    children = [
        html.H4('People vaccinated'),
        html.H2('{:,}'.format(tot_vac))
    ], 
    body = True, 
)


# #### Feature 2 and 3
# 
# For features 2 and 3, we create two selectors: a `Dropdown` component for selecting the variable and a `Dropdown` component for selecting the metric in feature 2. the two selectors are placed inside a `Card` component.

# In[18]:


# Variable selector
var_selector = dcc.Dropdown(
    id = 'variable',
    options = [{'label': 'Deaths', 'value': 'deaths'},
               {'label': 'Cases', 'value': 'cases'},
               {'label': 'Vaccinations', 'value': 'vaccinations'}],
    value = 'deaths',
    clearable = False,
)

# Metric selector
metric_selector = dcc.Dropdown(
    id = 'metric',
    options = [],
    value = None,
    clearable = False,
    optionHeight = 80
)


# In[19]:


selector_card = dbc.Card([
    html.Label('Select variable:'),
    var_selector,
    html.Br(),
    html.Label('Select metric:'),
    metric_selector    
],
    body = True, color = 'primary'
)


# Feature 2 and 3 are placed inside `Card` components.

# In[20]:


map_card = dbc.Card([
    dbc.Row([
        dbc.Col(selector_card, width = 3),
        dbc.Col(dcc.Graph(id = 'map', config = {'displayModeBar' : False}), width = 9)
    ])
],
    body = True
)


# In[21]:


bar_card = dbc.Card([
    dbc.Row([
        dbc.Col(id = 'current_week', width = 3),
        dbc.Col(dcc.Graph(id = 'bar_plot', config = {'displayModeBar' : False}), width = 9)
    ])
])


# #### App layout

# In[22]:


template = 'lux'
load_figure_template(template)
app = Dash(__name__, external_stylesheets = [dbc.themes.LUX, dbc_css])
server = app.server
description = """
A Dash application that tracks the development of COVID-19 and vaccination around the world. 

Data is collected from [Our World in Data](https://ourworldindata.org/coronavirus).
"""

app.layout = dbc.Container([
    
    html.H1('COVID-19 tracker'),
    html.P(dcc.Markdown(description)),
    
    # Row wth cards with totals
    dbc.Row(
        children = [
            dbc.Col(deaths_card, width = 4),
            dbc.Col(cases_card, width = 4),
            dbc.Col(vac_card, width = 4)
        ]
    ),
    html.Br(),
    
    # Card with selectors and map
    map_card,
    html.Br(),
    
    # Card with bar plot
    bar_card,
    html.Br()
    
],   
    className = 'dbc'
)

@app.callback(
    Output('metric', 'options'),
    Output('metric', 'value'),
    Input('variable', 'value')
)
def set_metric_options(var):
    
    if var == 'vaccinations':
        options = [
            {'label' : 'Total doses administered per 100 population', 'value' : 'total_vaccinations_per_hundred'},
            {'label' : 'Persons vaccinated with at least one dose per 100 population', 'value' : 'people_vaccinated_per_hundred'},
            {'label' : 'Persons fully vaccinated with last dose of primary series', 'value' : 'people_fully_vaccinated'}
        ]
        value = 'total_vaccinations_per_hundred'
        
    else:
        options = [
            {'label' : 'Total', 'value' : 'total'},
            {'label' : 'Total per 1 million population', 'value' : 'total_per_million'},
            {'label' : 'Newely reported in last 24 hours', 'value' : 'last_24h'},
        ]
        value = 'total'

    return options, value

@app.callback(
    Output('map', 'figure'),
    Input('variable', 'value'),
    Input('metric', 'value')
)
def update_map(var, metric):
    
    if metric == 'last_24h':
        col_name = 'new_' + var
    elif metric == 'total':
        col_name = 'total_' + var
    elif metric == 'total_per_million':
        col_name = 'total_' + var + '_per_million'
    else:
        col_name = metric
        
    fig = plot_map(col_name)
    
    return fig


@app.callback(
    Output('bar_plot', 'figure'),
    Output('current_week', 'children'),
    Input('variable', 'value')
)
def update_bar(var, df = df_world_week):
    
    col_name = 'new_' + var
    
    # Create figure
    fig = plot_bar(col_name)
    fig.update_layout(
        xaxis_title = None, 
        yaxis_title = None, 
        margin =  {'t' : 0, 'b' : 0, 'r' : 0, 'l' : 0},
        height = 250
    ) 
    
    # Create text
    current_number = int(df.iloc[-2][col_name])
    text = dbc.Container([
        html.H2('{:,}'.format(current_number)),
        html.H4(var),
        html.H4('last week')
    ], style = {'marginTop' : 50})
    
    return fig, text
    
if __name__ == '__main__':

    app.run_server(debug = True)


# In[ ]:





# In[ ]:




