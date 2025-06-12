#!/usr/bin/env python
# coding: utf-8

# In[1]:


#Importação de bibliotecas
import streamlit as st
import pandas as pd
import requests #Pega imfornações da net
import json #Lê arquivos Javascript para fazer mapa geográfico
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
import gdown

# In[3]:


# Configura a página de dashboard do Streamlit
st.set_page_config(page_title="Dashboard ENEM", layout="wide")

st.title("Dashboard ENEM")

st.markdown("""
    <style>
        .block-container {
            padding-top: 0rem;
            padding-left: 1rem;
            padding-right: 1rem;
        }
    </style>
""", unsafe_allow_html=True)

# Título principal da página
st.sidebar.title("Filtros")  # Título da barra lateral (Filtros)


# In[ ]:




#Define os tipos de algumas colunas para otimização
dtype_dict = {
    'SG_UF_PROVA': 'category',
    'TP_ST_CONCLUSAO': 'category',
    'Q006': 'category',
    'Q025': 'category',
    'STATUS_PRESENCA': 'category'
}
#@st.cache_data  # Cache para não recarregar o arquivo a cada mudança
# Lê o arquivo parquet com os dados tratados do ENEM
#def carregar_dados():
#    enem_tratado = pd.read_parquet("enem_tratado.parquet")  # Lê o arquivo Parquet com os dados tratados
#    return enem_tratado

#enem_tratado = carregar_dados()  # Chama a função e carrega os dados no DataFrame

# URL de download direto (formato gdown)
@st.cache_data
def carregar_dados():
    gdown.download('https://drive.google.com/uc?id=1JTNRRBI-kwafrSrVSAPFdwRoICTriuyM', 'enem_reduzido.parquet', quiet=False)
    enem_tratado = pd.read_parquet('enem_reduzido.parquet')
    return enem_tratado
enem_tratado = carregar_dados()
if st.button("🔄 Carregar dados"):  
    # In[ ]:
    
    mapa_cor_raca = {
        0: "Não declarado",
        1: "Branca",
        2: "Preta",
        3: "Parda",
        4: "Amarela",
        5: "Indígena",
        6: "Sem informação"
    }
    enem_tratado["TP_COR_RACA"] = enem_tratado["TP_COR_RACA"].replace(mapa_cor_raca)
    
    # Cria os filtros de ano, sexo e cor/raça
    anos = sorted(enem_tratado["NU_ANO"].dropna().unique())  
    sexos = enem_tratado["TP_SEXO"].dropna().unique()       
    cores = enem_tratado["TP_COR_RACA"].dropna().unique()   
    
    # Filtro multiselect na barra lateral
    ano_sel = st.sidebar.multiselect("Ano", anos, default=anos)
    sexo_sel = st.sidebar.multiselect("Sexo", sexos, default=sexos)
    cor_sel = st.sidebar.multiselect("Cor/Raça", cores, default=cores)
    
    # Aplica os filtros ao gráficos
    enem_filtros = enem_tratado[
        (enem_tratado["NU_ANO"].isin(ano_sel)) &
        (enem_tratado["TP_SEXO"].isin(sexo_sel)) &
        (enem_tratado["TP_COR_RACA"].isin(cor_sel))
    ]
    
    # Total de participantes por estado
    total_por_estado = enem_filtros["SG_UF_PROVA"].value_counts().reset_index()
    total_por_estado.columns = ["Estado", "Total de Participantes"]
    
    # Total de participantes com internet por estado
    internet_por_estado = enem_filtros[enem_filtros["Q025"] == "Sim"]["SG_UF_PROVA"].value_counts().reset_index()
    internet_por_estado.columns = ["Estado", "Quantidade com acesso à Internet"]
    
    # Junta as duas tabelas pelo estado
    df_por_estado = total_por_estado.merge(internet_por_estado, on="Estado", how="left")
    df_por_estado["Quantidade com acesso à Internet"] = df_por_estado["Quantidade com acesso à Internet"].fillna(0)
    
    # Calcula a porcentagem dentro do estado
    df_por_estado["Porcentagem com acesso à Internet"] = (
        df_por_estado["Quantidade com acesso à Internet"] / df_por_estado["Total de Participantes"] * 100
    )
    
    # Formata a porcentagem com 1 casa decimal e %
    df_por_estado["Porcentagem com acesso à Internet"] = df_por_estado["Porcentagem com acesso à Internet"].map(lambda x: f"{x:.1f}%")
    
    # Ordena por porcentagem decrescente (opcional)
    df_por_estado = df_por_estado.sort_values(by="Porcentagem com acesso à Internet", ascending=False)
    
    # Exibe a tabela na barra lateral
    st.sidebar.markdown("### Porcentagem de participantes com acesso à internet por estado")
    st.sidebar.table(df_por_estado.reset_index(drop=True))
    
    
    
    # In[ ]:
    #
    
    st.subheader("")
    col_esquerda, col_centro, col_direita = st.columns((1.5, 4.5, 2.2), gap='small')
    with col_esquerda:
        #Donut 1 de presença
        # Conta as categorias
        presenca_counts = enem_filtros['STATUS_PRESENCA'].value_counts()
    
        # Filtra os presentes
        labels = ['Presente', 'Ausente']
        values = [presenca_counts.get('Presente', 0), presenca_counts.get('Ausente', 0)]
    
        porcentagem_presente = values[0] / sum(values) * 100
    
        fig_donut = go.Figure(data=[go.Pie(
            labels=labels,
            values=values,
            hole=0.8,
            textinfo='none',
            marker=dict(colors=['lightgreen', 'rgba(0,0,0,0)']),
            showlegend=False
        )])
    
        fig_donut.update_layout(
            title="Presença no ENEM",
            annotations=[dict(
                text=f'{porcentagem_presente:.1f}%',
                x=0.5, y=0.5,
                font=dict(size=32, color='lightgreen'),
                showarrow=False,
            )],
            margin=dict(b=0),
            height=300
        )
    
        st.plotly_chart(fig_donut, use_container_width=True)
    
        #Donut 2
    
        # Conta os grupos
        conclusao_counts = enem_filtros['TP_ST_CONCLUSAO'].value_counts()
        labels_conclusao = ['Concluiu', 'Não concluiu']
        values_conclusao = [conclusao_counts.get('Concluiu', 0), conclusao_counts.get('Não concluiu', 0)]
    
        # Calcula % de conclusão
        porcentagem_concluiu = values_conclusao[0] / sum(values_conclusao) * 100
    
        # Cria gráfico estilo donut
        fig_conclusao = go.Figure(data=[go.Pie(
            labels=labels_conclusao,
            values=values_conclusao,
            hole=0.8,
            textinfo='none',
            marker=dict(colors=['lightblue', 'rgba(0,0,0,0)']),
            showlegend=False
        )])
    
        # Adiciona porcentagem central
        fig_conclusao.update_layout(
            title="Concluiu Ensino Médio",
            annotations=[dict(
                text=f'{porcentagem_concluiu:.1f}%',
                x=0.5, y=0.5,
                font=dict(size=32, color='lightblue'),
                showarrow=False
            )]
        )
    
        # Exibe no Streamlit
        st.plotly_chart(fig_conclusao, use_container_width=True)
    
        # In[ ]:
    
    
    
    
    
    # In[ ]:
    with col_centro:
    
        geojson_url = "https://raw.githubusercontent.com/codeforamerica/click_that_hood/master/public/data/brazil-states.geojson"
        geojson_data = requests.get(geojson_url).json()
    
        # Conta candidatos por estado
        enem_uf = enem_filtros["SG_UF_PROVA"].value_counts().reset_index()
        enem_uf.columns = ["SG_UF_PROVA", "Quantidade"]
    
    
        # Cria mapa geográfico por estado (versão simplificada)
        fig_map = px.choropleth(
            enem_uf,
            geojson=geojson_data,
            locations="SG_UF_PROVA",        # Sigla do estado (ex: SP, RJ)
            featureidkey="properties.name", # Caminho dentro do GeoJSON
            color="Quantidade",             # Cor representa a quantidade
            color_continuous_scale="YlOrRd",
            title="Total de Candidatos por Estado"
        )
    
        #Ajusta g´rafico para bordas do Brasil
        fig_map.update_geos(fitbounds="locations", visible=False)
    
        fig_map.update_layout(
        geo=dict(bgcolor='rgba(0,0,0,0)'),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        margin=dict(b=20),
        height=300
        )
    
        # Exibe o mapa
        st.plotly_chart(fig_map, use_container_width=True)
    
    
        # In[ ]:
    
        presentes = enem_filtros[enem_filtros["STATUS_PRESENCA"] == "Presente"]
    
        # Garante que o ano seja tratado como string (evita problemas no eixo X/Y)
        presentes['NU_ANO'] = presentes['NU_ANO'].astype(str)
    
        # Cria uma tabela dinâmica com a média das notas por ano e renda (Q006)
        heat_data = presentes.pivot_table(
            index='NU_ANO',  # Eixo Y (anos)
            columns='Q006',  # Eixo X (renda mensal)
            values='MEDIA_NOTAS',
            aggfunc='mean'  # Calcula a média das médias
        )
    
        # Cria uma tabela dinâmica com a contagem de participantes por ano e renda
        count_data = presentes.pivot_table(
            index='NU_ANO',
            columns='Q006',
            values='MEDIA_NOTAS',  # pode ser qualquer coluna não nula
            aggfunc='count'
        )
    
        # Garante que ambas as tabelas tenham a mesma ordem de colunas
        count_data = count_data[heat_data.columns]
    
        # Ordem desejada no gráfico (Q006 - Renda)
        ordem_q006 = [
            "Nenhuma renda",
            "Até R$ 1.320,00",
            "R$ 1.320,01 até R$ 1.980,00",
            "R$ 1.980,01 até R$ 2.640,00",
            "R$ 2.640,01 até R$ 3.300,00",
            "R$ 3.300,01 até R$ 3.960,00",
            "R$ 3.960,01 até R$ 5.280,00",
            "R$ 5.280,01 até R$ 6.600,00",
            "R$ 6.600,01 até R$ 7.920,00",
            "R$ 7.920,01 até R$ 9240,00",
            "R$ 9.240,01 até R$ 10.560,00",
            "R$ 10.560,01 até R$ 11.880,00",
            "R$ 11.880,01 até R$ 13.200,00",
            "R$ 13.200,01 até R$ 15.840,00",
            "R$ 15.840,01 até R$ 19.800,00",
            "R$ 19.800,01 até R$ 26.400,00.",
            "Acima de R$ 26.400,00"
        ]
    
        # Cria o gráfico de mapa de calor com customdata
        fig_heat = px.imshow(
            heat_data.values,
            labels=dict(x="Renda Familiar", y="Ano", color="Média de Notas"),
            x=heat_data.columns.tolist(),  # Eixo X: Q006
            y=heat_data.index.tolist(),  # Eixo Y: NU_ANO
            color_continuous_scale="YlOrRd",
            aspect="auto",
            title="Média por Renda"
        )
    
        # Adiciona customdata com a contagem e ajusta o hovertemplate
        fig_heat.update_traces(
            customdata=count_data.values,
            hovertemplate=
            "Ano: %{y}<br>" +
            "Renda: %{x}<br>" +
            "Média de Notas: %{z:.2f}<br>" +
            "Participantes: %{customdata}<extra></extra>"
        )
    
        # Ajusta os eixos e layout
        fig_heat.update_xaxes(type='category', categoryorder="array", categoryarray=ordem_q006)
        fig_heat.update_yaxes(type='category')
        fig_heat.update_layout(height=400)
    
        # Exibe o gráfico no Streamlit
        st.plotly_chart(fig_heat, use_container_width=True)
    
        #______________________________________
    
    with col_direita:
        #Mapa de gráfico de barras de participantes com acesso a internet
    
        # Conta quantas vezes cada resposta aparece
        enem_q025 = enem_filtros["Q025"].value_counts().reset_index()
        enem_q025.columns = ["Q025", "Quantidade"]  # Renomeia as colunas
    
        # Calcula porcentagem relativa de cada categoria
        enem_q025["Porcentagem"] = enem_q025["Quantidade"] / enem_q025["Quantidade"].sum() * 100
    
        # Agrupa por ano e acesso à internet e encontra o total de cada
        enem_grupo = enem_filtros.groupby(['NU_ANO', 'Q025']).size().reset_index(name='Total')
    
        # Converte para porcentagem dentro de cada ano
        enem_grupo['Porcentagem'] = enem_grupo.groupby('NU_ANO')['Total'].transform(lambda x: (x / x.sum()) * 100)
    
        # Cria um texto com a % formatada para exibir na barra
        enem_grupo['Label'] = enem_grupo['Porcentagem'].apply(lambda x: f"{x:.1f}%")
    
    
        enem_grupo['NU_ANO'] = enem_grupo['NU_ANO'].astype(str)
        # Cria gráfico de barras com quantidade e porcentagem
        fig_q025 = px.bar(
            enem_grupo,
            x="NU_ANO",                        # Rótulo X: resposta da pergunta
            y="Total",                 # Altura da barra: número de respostas
            color="Q025",                   # Cor de cada barra por categoria
            color_continuous_scale="YlOrRd",
            text='Label',          # <-- Mostra a % em cada segmento
            title='Acesso à Internet por Ano',
            labels={'Q025': 'Acesso à Internet?', "NU_ANO": "Ano"},
            category_orders={"NU_ANO": sorted(enem_grupo["NU_ANO"].unique())},
            color_discrete_map={
                "Sim": "#FEB24C", # Laranja
                "Não": "#F03B20"  # Vermelho
            }
        )
        fig_q025.update_layout(barmode='stack',
            height=400)
        fig_q025.update_traces(textposition='inside')  # <-- Aqui o texto fica dentro das barras
        fig_q025.update_xaxes(type='category')
        # Exibe o gráfico
        st.plotly_chart(fig_q025, use_container_width=True)
    
    #________________________________________________________
    
        # Agrupa por ano e calcula a média geral das notas
        media_por_ano = enem_filtros.groupby('NU_ANO')['MEDIA_NOTAS'].mean().reset_index()
    
        # Ordena por ano (garantindo a ordem correta no gráfico)
        media_por_ano = media_por_ano.sort_values('NU_ANO')
    
        # Cria o gráfico de linha
        fig_media_ano = px.line(
            media_por_ano,
            x='NU_ANO',
            y='MEDIA_NOTAS',
            markers=True,
            title='Média Geral das Notas por Ano',
            labels={'NU_ANO': 'Ano', 'MEDIA_NOTAS': 'Média das Notas'}
        )
    
        fig_media_ano.update_traces(line=dict(color='royalblue', width=3))
        fig_media_ano.update_layout(xaxis=dict(type='category'),height=300)
    
        # Exibe o gráfico no Streamlit
        st.plotly_chart(fig_media_ano, use_container_width=True)
