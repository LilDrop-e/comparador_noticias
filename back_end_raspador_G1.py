import requests
from bs4 import BeautifulSoup
import time
from datetime import datetime

def raspar_g1_com_detalhes(paginas=5):
    base_url = "https://g1.globo.com/ultimas-noticias/"
    noticias_detalhadas = []

    for pagina in range(1, paginas + 1):
        print(f"Raspando página {pagina} do G1...")
        url = f"{base_url}index/feed/pagina-{pagina}.ghtml"
        resposta = requests.get(url)

        if resposta.status_code != 200:
            print(f"Erro ao acessar página {pagina} do G1. Status: {resposta.status_code}")
            continue

        sopa = BeautifulSoup(resposta.text, 'html.parser')
        links_noticias = sopa.find_all('a', class_='feed-post-link')

        for link_noticia in links_noticias:
            titulo_texto = link_noticia.get_text(strip=True)
            url_noticia = link_noticia['href']

            # Evita duplicatas básicas antes de ir para a notícia individual
            if any(n['titulo'] == titulo_texto for n in noticias_detalhadas):
                continue

            data_publicacao = "Data não encontrada" # Valor padrão

            try:
                # Acessa a página individual da notícia para pegar a data
                resposta_noticia = requests.get(url_noticia, timeout=5)
                if resposta_noticia.status_code == 200:
                    sopa_noticia = BeautifulSoup(resposta_noticia.text, 'html.parser')
                    # Tentativa 1: Buscar por meta tag 'article:published_time'
                    meta_data = sopa_noticia.find('meta', property='article:published_time')
                    if meta_data and 'content' in meta_data.attrs:
                        data_publicacao = datetime.fromisoformat(meta_data['content'].replace('Z', '+00:00')).strftime('%Y-%m-%d')
                    else:
                        # Tentativa 2: Buscar em tags de tempo ou span com classes específicas
                        # (Essa parte pode variar e exigir ajuste fino para outros sites ou mudanças no G1)
                        data_tag = sopa_noticia.find('time', itemprop='datePublished')
                        if data_tag:
                            data_publicacao = data_tag.get_text(strip=True)
                            # Tentar parsear para formato YYYY-MM-DD se a string for completa
                            try:
                                data_publicacao = datetime.strptime(data_publicacao, '%d/%m/%Y %Hh%M').strftime('%Y-%m-%d')
                            except ValueError:
                                pass # Deixa como está se não conseguir parsear
                        else:
                            # Tentar encontrar a data no breadcrumb ou em um div com class de publicação
                            data_div = sopa_noticia.find('div', class_='content-publication-data__updated')
                            if data_div:
                                data_span = data_div.find('p', class_='content-publication-data__text')
                                if data_span:
                                    texto_data = data_span.get_text(strip=True)
                                    # Exemplo: "Atualizado em 05/06/2025 10h00"
                                    match = re.search(r'\d{2}/\d{2}/\d{4}', texto_data)
                                    if match:
                                        data_publicacao = datetime.strptime(match.group(0), '%d/%m/%Y').strftime('%Y-%m-%d')


                else:
                    print(f"Erro ao acessar notícia individual: {url_noticia}. Status: {resposta_noticia.status_code}")
            except requests.exceptions.RequestException as e:
                print(f"Erro de requisição para {url_noticia}: {e}")
            except Exception as e:
                print(f"Erro ao processar notícia {url_noticia}: {e}")


            noticias_detalhadas.append({
                'titulo': titulo_texto,
                'data': data_publicacao,
                'pagina': pagina,
                'site': 'G1'
            })
            time.sleep(0.5) # Pequeno delay para não sobrecarregar o servidor

        time.sleep(1) # Delay entre as páginas

    return noticias_detalhadas

def salvar_noticias_estruturadas(lista_noticias, nome_arquivo="noticias_g1_estruturadas.json"):
    import json
    with open(nome_arquivo, "w", encoding="utf-8") as arquivo:
        json.dump(lista_noticias, arquivo, ensure_ascii=False, indent=4)
    print(f"\n✅ Arquivo '{nome_arquivo}' salvo com {len(lista_noticias)} notícias detalhadas.")

if __name__ == "__main__":
    noticias_g1_detalhadas = raspar_g1_com_detalhes(paginas=2) # Comece com poucas páginas para testar
    salvar_noticias_estruturadas(noticias_g1_detalhadas)
