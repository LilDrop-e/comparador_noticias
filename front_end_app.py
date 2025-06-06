# app.py (Código readaptado)
import streamlit as st
import pandas as pd
import json
from datetime import datetime
import re # Importar regex para extrair dados do TXT

# --- Funções de Leitura e Processamento dos Arquivos TXT ---
def carregar_e_processar_txt(nome_arquivo_txt, site_nome):
    noticias_processadas = []
    current_titulo = None
    current_secao = None
    current_data = None

    try:
        with open(nome_arquivo_txt, "r", encoding="utf-8") as f:
            for linha in f:
                linha = linha.strip()
                if not linha: # Linha vazia, indica o fim de um bloco de notícia
                    if current_titulo is not None: # Verifica se temos um título para a notícia
                        # Tratar "Data não encontrada" e formatar
                        data_formatada = None
                        if current_data and current_data != "Data não encontrada":
                            try:
                                data_formatada = datetime.strptime(current_data, '%Y-%m-%d').strftime('%Y-%m-%d')
                            except ValueError:
                                pass # Deixa como None se não conseguir parsear

                        noticias_processadas.append({
                            'titulo': current_titulo,
                            'secao': current_secao,
                            'data': data_formatada,
                            'site': site_nome
                        })
                    # Resetar para a próxima notícia
                    current_titulo = None
                    current_secao = None
                    current_data = None
                    continue

                if linha.startswith("Título:"):
                    # Remover o "" que pode aparecer
                    titulo_limpo = re.sub(r'\', '', linha[len("Título:"):].strip()).strip()
                    current_titulo = titulo_limpo
                elif linha.startswith("Seção:"):
                    current_secao = linha[len("Seção:"):].strip()
                elif linha.startswith("Data:"):
                    current_data = linha[len("Data:"):].strip()
                    # Se for a última linha de um bloco e o arquivo não terminar com linha vazia
                    # processamos aqui para garantir que a última notícia seja capturada.
                    # Mas a lógica da linha vazia já cobre a maioria dos casos.
                    # Vamos manter a lógica principal na linha vazia para evitar duplicatas.
                    pass # Apenas armazena, o processamento final acontece na linha vazia ou no final do arquivo

            # Adicionar a última notícia se o arquivo não terminar com uma linha vazia
            if current_titulo is not None:
                data_formatada = None
                if current_data and current_data != "Data não encontrada":
                    try:
                        data_formatada = datetime.strptime(current_data, '%Y-%m-%d').strftime('%Y-%m-%d')
                    except ValueError:
                        pass
                noticias_processadas.append({
                    'titulo': current_titulo,
                    'secao': current_secao,
                    'data': data_formatada,
                    'site': site_nome
                })

    except FileNotFoundError:
        st.warning(f"Arquivo '{nome_arquivo_txt}' não encontrado.")
    except Exception as e:
        st.error(f"Erro ao carregar e processar notícias de '{nome_arquivo_txt}': {e}")
    return noticias_processadas


# --- Função Principal de Carregamento de Dados para o Streamlit ---
@st.cache_data
def carregar_dados_para_streamlit():
    todos_dados = []
    
    # Carregar Folha (usando a nova função para TXT)
    folha_data = carregar_e_processar_txt("noticias_folha.txt", "Folha")
    todos_dados.extend(folha_data)

    # Você precisará adaptar seus outros scrapers para gerar arquivos TXT semelhantes
    # ou fornecer seus arquivos TXT G1 e CNN com o mesmo formato.
    # Exemplo para G1 e CNN, se os TXT forem semelhantes:
    # g1_data = carregar_e_processar_txt("noticias_g1.txt", "G1")
    # todos_dados.extend(g1_data)
    # cnn_data = carregar_e_processar_txt("noticias_cnn.txt", "CNN")
    # todos_dados.extend(cnn_data)

    df = pd.DataFrame(todos_dados)
    # Garante que a coluna 'data' é do tipo datetime para filtragem
    if 'data' in df.columns:
        df['data'] = pd.to_datetime(df['data'], errors='coerce') # 'coerce' transforma inválidos (como None) em NaT (Not a Time)
    return df

# --- Estrutura do Streamlit App ---
st.set_page_config(layout="wide")
st.title("Comparador de Notícias Web")

df_noticias = carregar_dados_para_streamlit()

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
    # Filtrar datas válidas para min/max
    datas_validas = df_noticias['data'].dropna()
    if not datas_validas.empty:
        data_min = pd.to_datetime(datas_validas.min()).date()
        data_max = pd.to_datetime(datas_validas.max()).date()
        data_input = st.sidebar.date_input(
            "Selecione a data para pesquisa:",
            value=data_max, # Padrão para a data mais recente
            min_value=data_min,
            max_value=data_max
        )
    else:
        st.sidebar.warning("Nenhuma data válida encontrada nos dados.")
        data_input = None

    # Filtro por palavra-chave
    palavra_chave = st.sidebar.text_input("Pesquisar por palavra-chave:")

    # Aplicar filtros
    df_filtrado = df_noticias[df_noticias['site'].isin(sites_selecionados)]

    if data_input:
        # Comparar apenas a parte da data (ano-mês-dia)
        df_filtrado = df_filtrado[df_filtrado['data'].dt.date == data_input]

    if palavra_chave:
        # Filtrar títulos e seções que contenham a palavra-chave
        df_filtrado = df_filtrado[
            df_filtrado['titulo'].str.contains(palavra_chave, case=False, na=False) |
            (df_filtrado['secao'].fillna('').str.contains(palavra_chave, case=False, na=False)) # Considera seções também
        ]

    st.subheader("Notícias Filtradas")
    if not df_filtrado.empty:
        # Colunas a serem exibidas: site, data, seção, título
        st.dataframe(df_filtrado[['site', 'data', 'secao', 'titulo']])

        # Contagem de ocorrências da palavra-chave por site
        if palavra_chave:
            st.subheader(f"Contagem de '{palavra_chave}' por site (em Título/Seção):")
            
            # Função para contar ocorrências em texto (título ou seção)
            def contar_palavra(texto, palavra):
                if pd.isna(texto):
                    return 0
                return len(re.findall(r'\b' + re.escape(palavra) + r'\b', texto, re.IGNORECASE))

            # Cria uma coluna temporária para o texto completo (título + seção) para contagem
            df_filtrado['texto_completo'] = df_filtrado['titulo'].fillna('') + ' ' + df_filtrado['secao'].fillna('')

            contagem_por_site = df_filtrado.groupby('site')['texto_completo'].apply(
                lambda x: x.apply(lambda text: contar_palavra(text, palavra_chave)).sum()
            ).reset_index(name='Ocorrências')

            # Opcional: Remover a coluna temporária
            df_filtrado = df_filtrado.drop(columns=['texto_completo'])

            st.table(contagem_por_site)

    else:
        st.info("Nenhuma notícia encontrada com os filtros aplicados.")

else:
    st.info("Nenhum dado de notícia carregado. Verifique se os arquivos TXT estão presentes e no formato correto.")
