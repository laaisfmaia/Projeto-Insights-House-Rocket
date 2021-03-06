#para rodar o streamlit tem que digitar no terminal o comando streamlit run NomedoArquivo
import pandas as pd
import streamlit as st
import numpy as np
import folium
from streamlit_folium import folium_static
from folium.plugins import MarkerCluster
import plotly.express as px
from datetime import datetime

st.set_page_config(layout='wide')  #para que os conteúdos da página preencham toda a tela

@st.cache(allow_output_mutation=True)  #para otimizar a performance do código
def get_data(path):
    df = pd.read_csv(path)
    return df

def set_feature(data):
    # tranformação da variavel de foot para metros
    data['sqft_lot_m'] = data['sqft_lot'] * (0.3048)
    #add new feature
    data['price_m2'] = data['price'] / data['sqft_lot_m']
    return data

def overview_data(data):
    # data overview
    f_attribute = st.sidebar.multiselect('Enter columns',
                                         data.columns)  # Q2 - filtro que permite escolher uma ou mais variáveis para visualizar (Q2)
    f_zipcode = st.sidebar.multiselect('Enter ZipCode', data['zipcode'].unique())  # Q1 - filtro para visualizar os imóveis de uma ou várias regiões (Q1)

    st.title('Data Overview')  # título na página

    #    if (f_zipcode != []) & (f_attribute != []):
    #        data = data.loc[data['zipcode'].isin(f_zipcode), f_attribute]
    #    elif (f_zipcode != []) & (f_attribute == []):
    #        data = data.loc[data['zipcode'].isin(f_zipcode), :]
    #    elif (f_zipcode == []) & (f_attribute != []):
    #        data = data.loc[:, f_attri0ute]
    #    else:
    #        data = data.copy()

    if (f_attribute == []):
        if f_zipcode != []:
            data = data.loc[data['zipcode'].isin(f_zipcode), :]
            data2 = data.loc[data['zipcode'].isin(f_zipcode), :]
        else: #f_zipcode == []
            data = data.copy()
            data2 = data.copy()
    else: #f_attribute != []
        if f_zipcode != []:
            data2 = data.loc[data['zipcode'].isin(f_zipcode), f_attribute]
            data = data.loc[data['zipcode'].isin(f_zipcode), :]
        else: #f_zipcode == []
            data2 = data.loc[:, f_attribute]
            data = data.copy()


    st.dataframe(data2)

    c1, c2 = st.columns((1, 1))  # para colocar uma tabela do lado da outra

    # average metrics
    # Q3 - Observar o número total de imóveis, a média de preço, a média da sala de estar
    # e também a média do preço por metro quadrado em cada um dos códigos postais.
    # data2 = get_data(path)

    df1 = data[['id', 'zipcode']].groupby('zipcode').count().reset_index()  # número total de imóveis
    df2 = data[['price', 'zipcode']].groupby('zipcode').mean().reset_index()  # média de preço
    df3 = data[['sqft_living', 'zipcode']].groupby('zipcode').mean().reset_index()  # média da sala de estar
    df4 = data[['price_m2', 'zipcode']].groupby('zipcode').mean().reset_index()  # média do preço por metro quadrado

    # merge
    m1 = pd.merge(df1, df2, on='zipcode', how='inner')
    m2 = pd.merge(m1, df3, on='zipcode', how='inner')
    df = pd.merge(m2, df4, on='zipcode', how='inner')

    df.columns = ['ZIPCODE', 'TOTAL HOUSES', 'PRICE', 'SQRT LIVIND', 'PRICE/M2']

    c1.header('Average Values')
    c1.dataframe(df, height=600)

    # Statistic Descriptive
    # Q4 - Analisar cada uma das colunas de um modo mais descrito.
    num_attributes = data.select_dtypes(include=['int64', 'float64'])
    media = pd.DataFrame(num_attributes.apply(np.mean))
    mediana = pd.DataFrame(num_attributes.apply(np.median))
    std = pd.DataFrame(num_attributes.apply(np.std))
    max_ = pd.DataFrame(num_attributes.apply(np.max))
    min_ = pd.DataFrame(num_attributes.apply(np.min))

    df1 = pd.concat([max_, min_, media, mediana, std], axis=1).reset_index()
    df1.columns = ['attributes', 'max', 'min', 'mean', 'median', 'std']

    c2.header('Descriptive analysis')
    c2.dataframe(df1, height=700)

    return None

def portfolio_density(data):
    # densidade de portfólio
    st.title('Region Overview')

    c1, c2 = st.columns((1, 1))
    c1.header('Portfolio Density')

    df = data.sample(10)

    # base Map - folium
    density_map = folium.Map(location=[data['lat'].mean(), data['long'].mean()],
                             default_zoom_start=15)

    marker_cluster = MarkerCluster().add_to(density_map)  # marcadores no mapa

    for name, row in df.iterrows():
        folium.Marker([row['lat'], row['long']],
                      popup='Sold RS{0} on: {1}. Features: {2} sqft, {3} bedrooms, {4} bathrooms, year built: {5}'.format(
                          row['price'],
                          row['date'],
                          row['sqft_living'],
                          row['bedrooms'],
                          row['bathrooms'],
                          row['yr_built'])).add_to(marker_cluster)

    with c1:
        folium_static(density_map)

    return None

def commercial_distribution(data):
    # Distribuição dos imoveis por categoria comerciais
    st.sidebar.title('Commercial Options')
    st.title('Commercial Attributes')

    # Checar a variação anual de preço.
    # Average Price per Year
    data['date'] = pd.to_datetime(data['date']).dt.strftime('%Y-%m-%d')

    # filter
    min_year_built = int(data['yr_built'].min())
    max_year_built = int(data['yr_built'].max())

    st.sidebar.subheader('Select Max Year Built')
    f_year_built = st.sidebar.slider('Year Built', min_year_built,
                                     max_year_built,
                                     min_year_built)
    st.header('Average Price per Year Built')

    # data select
    df = data.loc[data['yr_built'] < f_year_built]
    df = df[['yr_built', 'price']].groupby('yr_built').mean().reset_index()

    # plot
    fig = px.line(df, x='yr_built', y='price')
    st.plotly_chart(fig, use_container_width=True)

    # Checar a variação diária de preço.
    # Average Price per Day
    st.header('Average Price per Day')
    st.sidebar.subheader('Select Max Date')

    # filter
    min_date = datetime.strptime(data['date'].min(), '%Y-%m-%d')
    max_date = datetime.strptime(data['date'].max(), '%Y-%m-%d')

    f_date = st.sidebar.slider('Date', min_date, max_date, min_date)

    # data select
    data['date'] = pd.to_datetime(data['date'])
    df = data.loc[data['date'] < f_date]
    df = df[['date', 'price']].groupby('date').mean().reset_index()

    # plot
    fig = px.line(df, x='date', y='price')
    st.plotly_chart(fig, use_container_width=True)

    # histograma
    st.header('Price Distribution')
    st.sidebar.subheader(('Select Max Price'))

    # filter
    min_price = int(data['price'].min())
    max_price = int(data['price'].max())
    avg_price = int(data['price'].mean())

    # data filtering
    f_price = st.sidebar.slider('Price', min_price, max_price, avg_price)
    df = data.loc[data['price'] < f_price]

    # plot
    fig = px.histogram(df, x='price', nbins=50)
    st.plotly_chart(fig, use_container_width=True)

    return None

def attributes_distribution(data):
    # distribuição dos imoveis por categorias físicas
    st.sidebar.title('Attributes Options')
    st.title('House Attributes')

    # filter
    f_bedrooms = st.sidebar.selectbox('Max number of bedrooms', sorted(set(data['bedrooms'].unique())))

    f_bathrooms = st.sidebar.selectbox('Max number of bedrooms', sorted(set(data['bathrooms'].unique())))

    c1, c2 = st.columns(2)

    # house per bedrooms
    c1.header('Houses per bedrooms')
    df = data[data['bedrooms'] < f_bedrooms]
    # plot
    fig = px.histogram(df, x='bedrooms', nbins=19)
    c1.plotly_chart(fig, use_container_width=True)

    # house per bathrooms
    c2.header('Houses per bathrooms')
    df = data[data['bathrooms'] < f_bathrooms]
    # plot
    fig = px.histogram(df, x='bathrooms', nbins=19)
    c2.plotly_chart(fig, use_container_width=True)

    # filters
    f_floors = st.sidebar.selectbox('Max number of floor', sorted(data['floors'].unique()))
    f_waterview = st.sidebar.checkbox('Only Houses with Water View')

    c1, c2 = st.columns(2)

    # house per floors
    c1.header('Houses per floor')
    df = data[data['floors'] < f_floors]
    # plot
    fig = px.histogram(df, x='floors', nbins=19)
    c1.plotly_chart(fig, use_container_width=True)

    # house per water view
    if f_waterview:
        df = data[data['waterfront'] == 1]
    else:
        df = data.copy()

    c2.header('Houses with Water View')
    fig = px.histogram(df, x='waterfront', nbins=10)
    c2.plotly_chart(fig, use_container_width=True)

    return None

if __name__ == "__main__":
    # ETL
    #data extration
    path = 'datasets/kc_house_data.csv'
    data = get_data(path)

    #tranformation
    data = set_feature(data)

    overview_data(data)

    portfolio_density(data)

    commercial_distribution(data)

    attributes_distribution(data)














