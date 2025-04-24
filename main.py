"""
Autor: Hugo Rios Brito
Descrição: Script para buscar notícias relacionadas a corrupção e fraudes em municípios da Bahia no Google News,
processar os resultados e salvar em excel.
O script utiliza Selenium para automação do navegador, BeautifulSoup para parsing do HTML,
e pandas para exportação dos dados para Excel.
"""

import time
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime

# URL raiz do Google News
root = 'https://news.google.com'

# Lista de termos de busca relacionados a fraudes e corrupção na Bahia
search_terms = [
    "Fraude Licitação Bahia",
    "Desvio de Recursos Bahia",
    "Corrupção Prefeitura Bahia",
    "Operação Polícia Federal Bahia",
    "Lavagem de Dinheiro Bahia",
    "Superfaturamento Contratos Bahia",
    "Irregularidades Obras Bahia",
    "Auditoria TCM Bahia",
    "Investigação Ministério Público Bahia",
    "Peculato Bahia",
    "Desvio Verbas Públicas Bahia",
    "Licitação Fraudulenta Bahia",
    "Operação Antares Bahia",
    "Operação Overclean Bahia",
    "Operação Teatro Mambembe Bahia",
    "Corrupção Ativa Bahia",
    "Fraude Documental Bahia",
    "Desvio Milionário Bahia"
]

# Lista para armazenar as notícias coletadas
news = []

# Configuração das opções do Chrome para rodar em modo headless (sem interface gráfica)
chrome_options = Options()
chrome_options.add_argument("--headless")
chrome_options.add_argument("--no-sandbox")
chrome_options.add_argument("--disable-dev-shm-usage")
chrome_options.add_argument("--disable-gpu")
chrome_options.add_argument(
    "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36")

# Inicialização do driver do Chrome
driver = webdriver.Chrome(options=chrome_options)

try:
    # Loop sobre cada termo de busca
    for palavra in search_terms:
        print(f"Buscando notícias para: {palavra}")
        query_text = palavra.replace(' ', '+')
        link = f"https://news.google.com/search?q={query_text}&hl=pt-BR&gl=BR&ceid=BR%3Apt-419"
        print(f"Acessando: {link}")

        driver.get(link)

        # Espera até que os elementos de notícia estejam presentes na página
        WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "div.UW0SDc, article"))
        )

        # Realiza scroll na página para carregar mais notícias
        last_height = driver.execute_script("return document.body.scrollHeight")
        scroll_count = 0
        max_scrolls = 50  # Número máximo de scrolls para evitar loops infinitos

        while scroll_count < max_scrolls:
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")

            try:
                # Espera até que a página carregue mais conteúdo
                WebDriverWait(driver, 5).until(
                    lambda d: d.execute_script("return document.body.scrollHeight") > last_height
                )
                last_height = driver.execute_script("return document.body.scrollHeight")
            except:
                # Se não carregar mais conteúdo, sai do loop
                break

            scroll_count += 1
            time.sleep(1)  # Aguarda um segundo entre os scrolls

        # Obtém o HTML da página carregada
        html = driver.page_source
        soup = BeautifulSoup(html, 'html.parser')

        # Seleciona os elementos de notícia
        news_items = soup.select('div.UW0SDc, article')
        print(f"Notícias encontradas na página: {len(news_items)}")

        # Processa cada notícia encontrada
        for item in news_items:
            try:
                # Extrai título, conteúdo, link, fonte, imagem e data de publicação
                title = item.find('a', class_='JtKRv') or item.find('h3') or item.find('h4')
                content = item.find('div', class_='GI74Re nDgy9d') or item.find('p')
                link_item = item.find("a", href=True)
                publisher = item.find('div', class_='vr1PYe') or item.find('div', class_='wsLqz')
                img_url = item.find('img', class_='Quavad vwBmvb') or item.find('img')
                data_publicacao_tag = item.find('time', class_='hvbAAd') or item.find('time')

                # Processa a data de publicação
                datetime_string = data_publicacao_tag['datetime'] if data_publicacao_tag and data_publicacao_tag.get(
                    'datetime') else None
                data_publicacao = None
                if datetime_string:
                    try:
                        datetime_obj = datetime.strptime(datetime_string, '%Y-%m-%dT%H:%M:%SZ')
                        data_publicacao = datetime_obj.strftime('%d/%m/%Y')
                    except ValueError:
                        data_publicacao = 'Data inválida'

                # Processa a URL da imagem
                img_path = img_url['srcset'].split()[0] if img_url and img_url.get('srcset') else (
                    img_url['src'] if img_url and img_url.get('src') else 'Imagem não encontrada'
                )

                # Monta o dicionário da notícia
                item_dict = {
                    'titulo': title.text.strip() if title else 'Título não encontrado',
                    'conteudo': content.text.strip() if content else 'Conteúdo não encontrado',
                    'fonte': publisher.text.strip() if publisher else 'Fonte não encontrada',
                    'datetime': data_publicacao if data_publicacao else 'Data não encontrada',
                    'link': root + link_item['href'][1:] if link_item and link_item.get(
                        'href') else 'Link não encontrado',
                    'img_url': root + img_path if img_path != 'Imagem não encontrada' and not img_path.startswith(
                        'http') else img_path,
                    'palavra_chave': palavra,
                }

                # Evita duplicidade de notícias
                if item_dict not in news:
                    news.append(item_dict)

                    # Exibe informações da notícia no console
                    print(
                        "============================================== NOTÍCIA ===================================================")
                    print(f"TÍTULO: {item_dict['titulo']}")
                    print(f"CONTEÚDO: {item_dict['conteudo']}")
                    print(f"FONTE: {item_dict['fonte']}")
                    print(f"DATA: {item_dict['datetime']}")
                    print(f"LINK: {item_dict['link']}")
                    print(f"IMAGEM: {item_dict['img_url']}")
                    print(f"PALAVRA-CHAVE: {item_dict['palavra_chave']}\n")
                    print(
                        "============================================== DICT =====================================================")
                    print(item_dict)
                    print(
                        "=======================================================================================================")

            except Exception as e:
                print(f"Erro ao processar item: {e}")
                continue

finally:
    # Encerra o driver do navegador
    driver.quit()

print(f"Quantidade total de notícias encontradas: {len(news)}")

# Exporta os dados coletados para um arquivo Excel
dfGoogle = pd.DataFrame(news)
dfGoogle.to_excel("noticias.xlsx", index=False)
