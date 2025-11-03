"""
Autor: Hugo Rios Brito
Descrição: Script para buscar notícias relacionadas a corrupção e fraudes em municípios da Bahia no Google News,
processar os resultados e salvar em Excel.
Utiliza Selenium para automação do navegador, BeautifulSoup para parsing do HTML e pandas para exportação dos dados.
"""

import sys
import time
import argparse
from datetime import datetime

import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from bs4 import BeautifulSoup

from auxiliar import pos_processamento
import definicoes

# URL raiz das fontes
ROOT_URLS = {
    'google_news': 'https://news.google.com',
    'portal_atarde': 'https://atarde.com.br'
}

# Configuração das opções do Chrome para rodar em modo headless (sem interface gráfica)
def setup_driver():
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")
    return webdriver.Chrome(options=chrome_options)

# Função para carregar a página de busca e aguardar elementos
def load_search_page(driver, url, selectors):
    print(f"Acessando: {url}")
    try:
        driver.get(url)
        WebDriverWait(driver, 15).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, selectors['news_elements']))
        )
        print("Página carregada e elementos de notícias encontrados.")
    except TimeoutException:
        print(f"Timeout ao carregar a página de busca. Pulando.")
        raise
    except Exception as e:
        print(f"Erro ao acessar ou carregar a página de busca: {e}. Pulando.")
        raise

# Função para carregar mais conteúdo (scroll ou click em "carregar mais")
def load_more_content(driver, config, max_loads=20, pause_time=2):
    load_method = config.get('load_method', 'scroll')
    count = 0
    print(f"Iniciando carregamento de mais notícias via {load_method} (max {max_loads})...")
    if load_method == 'scroll':
        last_height = driver.execute_script("return document.body.scrollHeight")
        while count < max_loads:
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            count += 1
            time.sleep(pause_time)
            new_height = driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                print(f"Scroll {count}/{max_loads}: Altura da página não mudou. Fim do conteúdo ou limite atingido.")
                break
            last_height = new_height
            print(f"Scroll {count}/{max_loads}: Nova altura da página {new_height}.")
    elif load_method == 'click':
        while count < max_loads:
            try:
                button = WebDriverWait(driver, 5).until(
                    EC.element_to_be_clickable((By.CSS_SELECTOR, config['load_selector']))
                )
                driver.execute_script("arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});", button)
                time.sleep(1)
                driver.execute_script("arguments[0].click();", button)
                count += 1
                time.sleep(pause_time)
                print(f"Click {count}/{max_loads}: Carregando mais notícias.")
            except TimeoutException:
                print(f"Click {count}/{max_loads}: Botão 'carregar mais' não encontrado ou fim do conteúdo.")
                break
            except Exception as e:
                print(f"Erro ao clicar no botão: {e}")
                break
    print("Carregamento de mais conteúdo concluído.")

# Função para parsear o HTML e extrair notícias
def parse_news_items(html, search_term, root_url, seen_links, news, config):
    soup = BeautifulSoup(html, 'html.parser')
    news_items = soup.select(config['news_items'])
    print(f"Total de elementos de notícias encontrados: {len(news_items)}")

    if not news_items:
        print(f"Nenhum item de notícia encontrado para a busca '{search_term}'.")
        return

    for i, item in enumerate(news_items):
        item_link = None
        try:
            title_tag = item.select_one(config['title'])
            content_tag = item.select_one(config['content'])
            link_tag = item.select_one(config['link']) if config['link'] else item
            publisher_tag = item.select_one(config['publisher']) if config['publisher'] else None
            img_tag = item.find(config['img']) if config['img'] else item.find('img')
            date_tag = item.select_one(config['date'])

            if link_tag and link_tag.get('href'):
                href = link_tag['href']
                if href.startswith('./articles/'):
                    item_link = f"{root_url}{href[1:]}"
                elif href.startswith('http'):
                    item_link = href
                else:
                    item_link = f"{root_url}{href.lstrip('/')}"

            if not item_link or item_link in seen_links:
                continue

            seen_links.add(item_link)

            title = title_tag.text.strip() if title_tag else 'Título não encontrado'
            content = content_tag.text.strip() if content_tag else 'Conteúdo não encontrado'
            publisher = publisher_tag.text.strip() if publisher_tag else config.get('default_publisher', 'Fonte não encontrada')
            data_publicacao = 'Data não encontrada'
            ano_filtro = None

            if date_tag:
                if date_tag.get('datetime'):
                    try:
                        datetime_string = date_tag['datetime']
                        if datetime_string.endswith('Z'):
                            datetime_string = datetime_string[:-1] + '+00:00'
                        elif '+' not in datetime_string and '-' not in datetime_string[10:]:
                            datetime_string += '+00:00'

                        datetime_obj = datetime.fromisoformat(datetime_string)
                        data_publicacao = datetime_obj.strftime('%d/%m/%Y')
                        ano_filtro = int(datetime_obj.strftime('%Y'))
                        print(f"Data de publicação parseada: {data_publicacao}")
                    except ValueError as ve:
                        print(f"Erro ao parsear data '{datetime_string}': {ve}")
                        data_publicacao = datetime_string
                    except Exception as ex:
                        print(f"Erro inesperado ao processar data '{datetime_string}': {ex}")
                        data_publicacao = datetime_string
                else:
                    # Parsing de texto para fontes como A Tarde
                    date_text = date_tag.text.strip()
                    try:
                        # Exemplo: "03/11/2025 às 14:44"
                        data_publicacao = date_text.split('às')[0].strip()
                        datetime_obj = datetime.strptime(data_publicacao, '%d/%m/%Y')
                        data_publicacao = datetime_obj.strftime('%d/%m/%Y')
                        ano_filtro = datetime_obj.year
                        print(f"Data de publicação parseada do texto: {data_publicacao}")
                    except Exception as e:
                        print(f"Erro ao parsear data do texto '{date_text}': {e}")
                        data_publicacao = date_text

            img_url_final = img_tag['srcset'].split()[0] if img_tag and img_tag.get('srcset') else (
                img_tag['src'] if img_tag and img_tag.get('src') else 'Imagem não encontrada'
            )

            img_url = img_url_final if img_url_final.startswith('http') else root_url + img_url_final

            municipios_potential = definicoes.get_municipios_from_title(title, content)
            municipios_string = ",".join(municipios_potential) if municipios_potential else ""

            item_dict = {
                'titulo': title,
                'conteudo': content,
                'fonte': publisher,
                'datetime': data_publicacao,
                'link': item_link,
                'img_url': img_url,
                'palavra_chave': search_term,
                'municipios_citados': municipios_string
            }

            if ano_filtro is not None and ano_filtro < 2023:
                print(f"Ignorando notícia de ano {ano_filtro} (menor que 2023).")
                continue

            news.append(item_dict)

            print("\n============================================== NOTÍCIA ===================================================")
            print(f"TÍTULO: {item_dict['titulo']}")
            print(f"CONTEÚDO: {item_dict['conteudo'][:200]}...")
            print(f"MUNICÍPIOS CITADOS ({len(municipios_potential)}): {item_dict['municipios_citados']}")
            print(f"FONTE: {item_dict['fonte']}")
            print(f"DATA: {item_dict['datetime']}")
            print(f"LINK: {item_dict['link']}")
            print(f"IMAGEM: {item_dict['img_url']}")
            print(f"PALAVRA-CHAVE: {item_dict['palavra_chave']}")
        except Exception as e:
            print(f"Erro ao processar item: {e}")
            continue

# Função para coletar notícias de uma fonte específica
def collect_news_from_source(driver, search_terms, source='google_news'):
    root_url = ROOT_URLS.get(source, 'https://news.google.com')
    seen_links = set()
    news = []

    source_config = {
        'google_news': {
            'query_format': "/search?q={query_text}&hl=pt-BR&gl=BR&ceid=BR%3Apt-419",
            'news_elements': "div.UW0SDc, article",
            'news_items': 'div.UW0SDc, article',
            'title': 'a.JtKRv, h3 a, h4 a',
            'content': 'div.GI74Re.nDgy9d, p',
            'link': "a[href]",
            'publisher': 'div.vr1PYe, div.wsLqz',
            'img': 'img.Quavad.vwBmvb',
            'date': 'time.hvbAAd, time',
            'load_method': 'scroll'
        },
        'portal_atarde': {
            'query_format': "/?q={query_text}",
            'news_elements': ".chamadaUltimasNoticias",
            'news_items': '.chamadaUltimasNoticias',
            'title': 'h2',
            'content': 'p',
            'link': '',
            'publisher': '',
            'default_publisher': 'A Tarde',
            'img': 'img',
            'date': 'span',
            'load_method': 'click',
            'load_selector': '.atr-maisNoticias'
        }
        # adicionar outras fontes aqui
    }

    config = source_config.get(source)
    if not config:
        raise ValueError(f"Fonte '{source}' não suportada. Adicione configurações para ela.")

    try:
        for palavra in search_terms:
            print(f"\n--- Buscando notícias para: {palavra} em {source} ---")
            query_text = palavra.replace(' ', '+')
            link = f"{root_url}{config['query_format'].format(query_text=query_text)}"

            try:
                load_search_page(driver, link, config)
                load_more_content(driver, config)
                html = driver.page_source
                parse_news_items(html, palavra, root_url, seen_links, news, config)
            except Exception as e:
                print(f"Erro ao processar busca para '{palavra}' em {source}: {e}")
                continue
    finally:
        driver.quit()

    print(f"Quantidade total de notícias encontradas em {source}: {len(news)}")
    return news

# Função para processar e salvar as notícias em Excel
def process_and_save_news(news, output_file):
    print(f"Quantidade total de notícias únicas encontradas e processadas: {len(news)}")

    if news:
        try:
            df = pd.DataFrame(news)
            excel_filename = f"{output_file}_{datetime.now().strftime('%Y-%m-%d_%H%M')}"
            if not excel_filename.lower().endswith('.xlsx'):
                excel_filename += '.xlsx'
            dfProcessado = pos_processamento.processar_linhas(df)
            dfProcessado.to_excel(excel_filename, index=False)
            print(f"✅ Dados exportados para '{excel_filename}'.")
        except Exception as e:
            print(f"Erro ao exportar dados para Excel: {e}")

# Função principal
def main(search_terms, output_file, sources=['google_news']):
    news = []
    for source in sources:
        driver = setup_driver()
        news += collect_news_from_source(driver, search_terms, source)
    process_and_save_news(news, output_file)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description=(
            "Busca notícias em fontes especificadas para termos fornecidos, processa e exporta para Excel. "
            "Exemplo: python .\\src\\main.py --t .\\src\\termos_pesquisa\\termos_para_pesquisa.txt -s saida --fonte google_news portal_atarde"
        )
    )
    parser.add_argument(
        "-t", "--termos", required=True,
        help="Caminho para o arquivo .txt contendo um termo por linha"
    )
    parser.add_argument(
        "-s", "--saida", required=True,
        help="Prefixo do nome do arquivo de saída (não adicionar '.xlsx' e timestamp, será adicionado automaticamente)."
    )
    parser.add_argument(
        "-f", "--fonte", nargs='+', default=['google_news'],
        help="Lista das fontes para buscar notícias (google_news, portal_atarde)"
    )

    args = parser.parse_args()
    errors = False
    search_terms_txt = args.termos
    output_file = args.saida

    try:
        with open(search_terms_txt, 'r', encoding='utf-8') as f:
            lines = [line.strip() for line in f if line.strip()]
    except FileNotFoundError:
        print(f"Arquivo de termos não encontrado: {search_terms_txt}")
        errors = True
        sys.exit(1)
    except Exception as e:
        print(f"Erro ao ler o arquivo de termos '{search_terms_txt}': {e}")
        errors = True
        sys.exit(1)

    if not errors:
        main(lines, output_file, args.fonte)