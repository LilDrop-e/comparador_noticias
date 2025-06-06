import streamlit as st
import pandas as pd
import json
from datetime import datetime

# Função para carregar dados (adaptar para seus arquivos JSON)
@st.cache_data
def carregar_dados():
    todos_dados = []
    # Carregar G1
    try:
        with open("noticias_g1_estruturadas.json", "r", encoding="utf-8") as f:
            g1_data = json.load(f)
            todos_dados.extend(g1_data)
    except FileNotFoundError:
        st.warning("Arquivo 'noticias_g1_estruturadas.json' não encontrado. Raspe o G1 primeiro.")
    except Exception as e:
        st.error(f"Erro ao carregar notícias do G1: {e}")

    # Carregar CNN (assumindo que você adaptou o scraper para JSON também)
    try:
        with open("noticias_cnn_estruturadas.json", "r", encoding="utf-8") as f:
            cnn_data = json.load(f)
            todos_dados.extend(cnn_data)
    except FileNotFoundError:
        st.warning("Arquivo 'noticias_cnn_estruturadas.json' não encontrado. Raspe a CNN primeiro.")
    except Exception as e:
        st.error(f"Erro ao carregar notícias da CNN: {e}")

    # Carregar Folha (assumindo que você adaptou o scraper para JSON também)
    try:
        with open("noticias_folha_estruturadas.json", "r", encoding="utf-8") as f:
            folha_data = json.load(f)
            todos_dados.extend(folha_data)
    except FileNotFoundError:
        st.warning("Arquivo 'noticias_folha_estruturadas.json' não encontrado. Raspe a Folha primeiro.")
    except Exception as e:
        st.error(f"Erro ao carregar notícias da Folha: {e}")

    df = pd.DataFrame(todos_dados)
    # Garante que a coluna 'data' é do tipo datetime para filtragem
    if 'data' in df.columns:
        df['data'] = pd.to_datetime(df['data'], errors='coerce')
    return df

st.set_page_config(layout="wide")
st.title("Comparador de Notícias Web")

df_noticias = carregar_dados()

if not df_noticias.empty:
    st.sidebar.header("Filtros")

    # Filtro por site
    sites_disponiveis = df_noticias['site'].unique().tolist()
    sites_selecionados = st.sidebar.multiselect(
        "Selecione os sites:",
        options=sites_disponiveis,
        default=sites_disponiveis
    )

    # Filtro por data
    datas_disponiveis = df_noticias['data'].dropna().unique()
    if len(datas_disponiveis) > 0:
        data_min = pd.to_datetime(datas_disponiveis.min())
        data_max = pd.to_datetime(datas_disponiveis.max())
        data_input = st.sidebar.date_input(
            "Selecione a data para pesquisa:",
            value=data_max,
            min_value=data_min,
            max_value=data_max
        )
    else:
        st.sidebar.warning("Nenhuma data disponível nos dados.")
        data_input = None


    # Filtro por palavra-chave
    palavra_chave = st.sidebar.text_input("Pesquisar por palavra-chave:")

    # Aplicar filtros
    df_filtrado = df_noticias[df_noticias['site'].isin(sites_selecionados)]

    if data_input:
        df_filtrado = df_filtrado[df_filtrado['data'].dt.date == data_input]

    if palavra_chave:
        df_filtrado = df_filtrado[df_filtrado['titulo'].str.contains(palavra_chave, case=False, na=False)]

    st.subheader("Notícias Filtradas")
    if not df_filtrado.empty:
        st.dataframe(df_filtrado[['site', 'data', 'pagina', 'titulo']])

        # Contagem de ocorrências da palavra-chave por site
        if palavra_chave:
            st.subheader(f"Contagem de '{palavra_chave}' por site:")
            contagem_por_site = df_filtrado.groupby('site')['titulo'].apply(
                lambda x: x.str.contains(palavra_chave, case=False, na=False).sum()
            ).reset_index(name='Ocorrências')
            st.table(contagem_por_site)

    else:
        st.info("Nenhuma notícia encontrada com os filtros aplicados.")

else:
    st.info("Nenhum dado de notícia carregado. Execute os scripts de raspagem primeiro.")
