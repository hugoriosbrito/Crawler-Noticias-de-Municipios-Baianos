"""
Autor: Hugo Rios Brito
Descrição: Script para buscar notícias relacionadas a corrupção e fraudes em municípios da Bahia no Google News,
processar os resultados e salvar em excel.
O script utiliza Selenium para automação do navegador, BeautifulSoup para parsing do HTML,
e pandas para exportação dos dados para Excel.
"""
import time
import unicodedata
import re 

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException
from bs4 import BeautifulSoup
import pandas as pd
from datetime import datetime

from auxiliar.municipios import get_municipios_metadata 
from auxiliar.spacy_extract import extrair_municipios 
from auxiliar import pos_processamento

# URL raiz do Google News
root_url = 'https://news.google.com'

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
seen_links = set()

# Lista de palavras ambíguas que podem causar confusão na detecção de municípios
PALAVRAS_AMBIGUAS = {
    "saude", "gloria", "vitoria", "esperanca", "nazaré", "america",
    "campo", "alegre", "formosa", "nova",  "belo", "bonito", "feira", "central",
    "santana", "wagner", "Wagner"
}

def normalize_text(text):
    """Normaliza o texto removendo acentos e convertendo para minúsculas."""
    if not isinstance(text, str):
        return ""
    try:
        nfkd_form = unicodedata.normalize('NFKD', text.lower())
        return "".join([c for c in nfkd_form if not unicodedata.combining(c)])
    except Exception:

        return text.lower()


ALL_BAHIA_MUNICIPIOS_DATA = get_municipios_metadata() 
MUNICIPIO_LOOKUP = {
    normalize_text(nome_original): f"{nome_original}-{codigo}"
    for nome_original, codigo in ALL_BAHIA_MUNICIPIOS_DATA.items()
}


NORMALIZED_MUNICIPIO_NAMES = set(MUNICIPIO_LOOKUP.keys())

MULTI_WORD_MUNICIPIOS = {}
for name_original in ALL_BAHIA_MUNICIPIOS_DATA.keys():
    if ' ' in name_original:
        normalized_name = normalize_text(name_original)
        components = normalized_name.split()
        for comp in components:
            if comp in NORMALIZED_MUNICIPIO_NAMES: 
                 if normalized_name not in MULTI_WORD_MUNICIPIOS:
                     MULTI_WORD_MUNICIPIOS[normalized_name] = []
                 if comp not in MULTI_WORD_MUNICIPIOS[normalized_name]:
                    MULTI_WORD_MUNICIPIOS[normalized_name].append(comp)
                    

def pre_process_text_for_municipality_detection(text):
    """Remove sufixos comuns como (BA), - BA, etc., do texto."""
    if not isinstance(text, str):
        return ""
    text = re.sub(r'\s*\(BA\)\s*', '', text, flags=re.IGNORECASE)
    text = re.sub(r'\s*-\s*BA\s*', '', text, flags=re.IGNORECASE)
    text = re.sub(r',\s*BA\b', '', text, flags=re.IGNORECASE) 
    return text.strip()


def is_geographical_context(name, text):
    """
    Verifica se um nome aparece em um contexto que sugere ser um nome geográfico.
    Aplica pre-processamento no texto antes de verificar.
    """
    if not isinstance(name, str) or not isinstance(text, str):
        return False

    processed_text = pre_process_text_for_municipality_detection(text)

    normalized_name_escaped = re.escape(normalize_text(name))

    padroes_geograficos = [
        rf"\b(prefeitura|município|cidade|câmara)\s+(?:de|do|da|d[oa]s?)\s+{normalized_name_escaped}\b",
        rf"\b(?:em|na|no|de|do|da|para|às?)\s+{normalized_name_escaped}\b",
        rf"\b{normalized_name_escaped}\s+(?:prefeitura|município|cidade)\b" 
    ]

    for pattern in padroes_geograficos:
        if re.search(pattern, processed_text, re.IGNORECASE):
            return True

    return False


def should_ignore_municipality(name, text):
    """
    Determina se um nome deve ser ignorado com logica extra para verificação de palavras ambiguas.
    """
    if not isinstance(name, str):
        return True 
    normalized_name = normalize_text(name)

  
    if normalized_name == 'bahia':
        return True

    
    if normalized_name in PALAVRAS_AMBIGUAS:
        return not is_geographical_context(name, text)

    return False


def get_municipios_from_title(title, text_content):
    """
    Extrai e filtra municipios usando o modelo do spacy e o contexto.
    Aplica pre-processamento no texto antes de extrair e filtrar.
    Aplica pos processamento no texto para tratar municipios com mais de uma palavra.
    Prioriza o contexto ao máximo.
    """
    if not title and not text_content:
        return []

    processed_title = pre_process_text_for_municipality_detection(title)
    processed_text_content = pre_process_text_for_municipality_detection(text_content)

    context_text = processed_text_content if processed_text_content and processed_text_content.strip() else processed_title

    potential_municipios_raw = extrair_municipios(processed_title)

    potential_normalized_set = {normalize_text(name) for name in potential_municipios_raw if isinstance(name, str)}

    filtered_municipios_normalized = set()

    for nome_raw in potential_municipios_raw:
        if not isinstance(nome_raw, str) or not nome_raw.strip():
            continue

        normalized_name = normalize_text(nome_raw)

        if normalized_name in NORMALIZED_MUNICIPIO_NAMES and normalized_name != 'bahia':
            if not should_ignore_municipality(nome_raw, context_text):
                is_component_of_detected_multi_word = False
                for multi_word_normalized, components_normalized in MULTI_WORD_MUNICIPIOS.items():
                    if normalized_name in components_normalized:
                         if multi_word_normalized in potential_normalized_set:
                            is_component_of_detected_multi_word = True
                            break #

                if not is_component_of_detected_multi_word:
                    filtered_municipios_normalized.add(normalized_name)




    mapped_list = []
    for normalized_filtered_name in filtered_municipios_normalized:

        if normalized_filtered_name in MUNICIPIO_LOOKUP:
             mapped_list.append(MUNICIPIO_LOOKUP[normalized_filtered_name])

    return list(dict.fromkeys(mapped_list)) 

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
        print(f"\n--- Buscando notícias para: {palavra} ---")
        query_text = palavra.replace(' ', '+')
        link = f"{root_url}/search?q={query_text}&hl=pt-BR&gl=BR&ceid=BR%3Apt-419"

        print(f"Acessando: {link}")
        try:
            driver.get(link)
            WebDriverWait(driver, 15).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "div.UW0SDc, article"))
            )
            print("Página carregada e elementos de notícias encontrados.")
        except TimeoutException:
            print(f"❌ Timeout ao carregar a página de busca para: {palavra}. Pulando.")
            continue
        except Exception as e:
            print(f"❌ Erro ao acessar ou carregar a página de busca para '{palavra}': {e}. Pulando.")
            continue

        last_height = driver.execute_script("return document.body.scrollHeight")
        scroll_count = 0
        max_scrolls = 20
        scroll_pause_time = 2

        print(f"Iniciando scroll para carregar mais notícias (max {max_scrolls} scrolls)...")
        while scroll_count < max_scrolls:
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            scroll_count += 1
            time.sleep(scroll_pause_time)
            new_height = driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                print(
                    f"Scroll {scroll_count}/{max_scrolls}: Altura da página não mudou. Fim do conteúdo ou limite atingido.")
                break
            last_height = new_height
            print(f"Scroll {scroll_count}/{max_scrolls}: Nova altura da página {new_height}.")
        print("Scroll concluído.")

        html = driver.page_source
        soup = BeautifulSoup(html, 'html.parser')
        news_items = soup.select('div.UW0SDc, article')
        print(f"Total de elementos de notícias encontrados após scroll: {len(news_items)}")

        if not news_items:
            print(f"⚠️ Nenhum item de notícia encontrado para a busca '{palavra}' após scrolling. Pulando para a próxima palavra.")
            continue
        
        for i, item in enumerate(news_items):
            item_link = None
            try:
                title_tag = item.select_one('a.JtKRv, h3 a, h4 a')
                content_tag = item.select_one('div.GI74Re.nDgy9d, p')
                link_tag = item.select_one("a[href]")
                publisher_tag = item.select_one('div.vr1PYe, div.wsLqz')
                img_tag = item.find('img', class_='Quavad vwBmvb') or item.find('img')
                date_tag = item.select_one('time.hvbAAd, time')

                if link_tag and link_tag.get('href'):
                    href = link_tag['href']
                    if href.startswith('./articles/'):
                        item_link = f"{root_url}{href[1:]}"
                    elif href.startswith('http'):
                        item_link = href
                    else:
                        item_link = f"{root_url}/{href.lstrip('/')}"

                if not item_link or item_link in seen_links:
                    continue

                seen_links.add(item_link)

                title = title_tag.text.strip() if title_tag else 'Título não encontrado'
                content = content_tag.text.strip() if content_tag else 'Conteúdo não encontrado'
                publisher = publisher_tag.text.strip() if publisher_tag else 'Fonte não encontrada'
                data_publicacao = 'Data não encontrada'
                if date_tag and date_tag.get('datetime'):
                    try:
                        datetime_string = date_tag['datetime']
                        if datetime_string.endswith('Z'):
                             datetime_string = datetime_string[:-1] + '+00:00'
                        elif '+' not in datetime_string and '-' not in datetime_string[10:]:
                             datetime_string += '+00:00' 

                        datetime_obj = datetime.fromisoformat(datetime_string)
                        data_publicacao = datetime_obj.strftime('%d/%m/%Y')
                        ano_filtro = int(datetime_obj.strftime('%Y'))
                        print(f"🕒 Data de publicação parseada: {data_publicacao}")
                    except ValueError as ve:
                        print(f"❌ Erro ao parsear data '{datetime_string}': {ve}")
                        data_publicacao = datetime_string 
                    except Exception as ex:
                         print(f"❌ Erro inesperado ao processar data '{datetime_string}': {ex}")
                         data_publicacao = datetime_string


                img_url_final = img_tag['srcset'].split()[0] if img_tag and img_tag.get('srcset') else (
                    img_tag['src'] if img_tag and img_tag.get('src') else 'Imagem não encontrada'
                )


                municipios_potential = get_municipios_from_title(title, content)

                municipios_string = ",".join(municipios_potential) if municipios_potential else ""

                item_dict = {
                    'titulo': title,
                    'conteudo': content,
                    'fonte': publisher,
                    'datetime': data_publicacao,
                    'link': item_link,
                    'img_url': root_url + img_url_final,
                    'palavra_chave': palavra,
                    'municipios_citados': municipios_string
                }

                if ano_filtro < 2023:
                    print(f"⚠️ Ignorando notícia de ano {ano_filtro} (menor que 2023).")
                    continue

                news.append(item_dict)

                print(
                    "\n============================================== NOTÍCIA ===================================================")
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

finally:
    # Encerra o driver do navegador
    driver.quit()

print(f"Quantidade total de notícias encontradas: {len(news)}")


print(f"Quantidade total de notícias únicas encontradas e processadas: {len(news)}")

if news:
    try:
        # Exporta os dados para um arquivo Excel
        dfGoogle = pd.DataFrame(news)
        excel_filename = f"{datetime.now().strftime('%Y-%m-%d_%H%M')}_noticias_fraude_corrupcao_bahia.xlsx"
        dfProcessado = pos_processamento.processar_linhas(dfGoogle)
        dfProcessado.to_excel(excel_filename, index=False)
        print(f"✅ Dados exportados para '{excel_filename}'.")
    except Exception as e:
        print(f"❌ Erro ao exportar dados para Excel: {e}")

