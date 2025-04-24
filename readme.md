
# Crawler de notícias que envolvem os Municípios Baianos

Script para coletar notícias relacionadas a corrupção, fraudes, operações policiais, etc em municípios da Bahia usando o Google News. Afim de posterior análise por parte do Tribunal de Contas dos Municípios da Bahia (TCM-BA).

## Descrição

Este script automatiza a busca de notícias no Google News sobre temas como fraude, corrupção e operações policiais em municípios da Bahia. Utiliza Selenium para automação do navegador, BeautifulSoup para extração dos dados e pandas para exportação dos resultados em Excel.

## Requisitos

- Python 3.8+
- Google Chrome instalado
- ChromeDriver compatível com sua versão do Chrome

Obs.: Se não tiver o ChromeDriver, baixe a versão correta [aqui](https://developer.chrome.com/docs/chromedriver/get-started?hl=pt-br#setup) e coloque no mesmo diretório do script ou adicione ao PATH do sistema.

Instale as dependências com:

```
pip install -r requirements.txt
```

## Como usar

1. Certifique-se de que o ChromeDriver está no PATH ou no mesmo diretório do script.
2. Execute o script principal:

```
python main.py
```

3. O script irá buscar notícias para vários termos relacionados a corrupção na Bahia e salvar os resultados em um arquivo Excel chamado `noticias.xlsx`.

## Saída

- `noticias.xlsx`: arquivo Excel contendo as notícias coletadas, com colunas como título, conteúdo, fonte, data, link, imagem e palavra-chave.


    
    Buscando notícias para: Fraude Licitação Bahia
    Acessando: https://news.google.com/search?q=Fraude+Licitação+Bahia&hl=pt-BR&gl=BR&ceid=BR%3Apt-419
    Notícias encontradas na página: 101
    ============================================== NOTÍCIA ===================================================
    TÍTULO: SJBA - Justiça Federal condena seis pessoas por organização criminosa e fraude à licitação em Cansanção/BA; um réu é absolvido
    CONTEÚDO: Conteúdo não encontrado
    FONTE: TRF1
    DATA: 23/04/2025
    LINK: https://news.google.com/read/CBMi7gFBVV95cUxNaWZUQlk1T2ttTlNfR1ZtQ3BIb1phdEFNLXVtM3haUzkwSkZJbkctWE00UUtZbVlQT2ZTOVhpb3RvcHJSYWhKWnRDN2MtR296RDdTOWZkMS0yU3Y3UUlGTzhwRkNINnc0QWNzOHNFNW80NEhqWHU2U29sM0cwd3lHZ1ZPZ1RxYTlmTExISkdiWFlpcVh4aFQ5Z3VEcWNuZUdEQVpGdE5wZk9NdjhDclN1a2I2X3hJQnUxSk1xUUNvb2tBZzJmQk56Y3dIOTlHSC1sajd2eHhlQ2VRVDhPM3Q4Z1VDWU50S1BncmFHdmRR?hl=pt-BR&gl=BR&ceid=BR%3Apt-419
    IMAGEM: https://news.google.com/api/attachments/CC8iL0NnNHdaMjlLYWprMVdrbElRV3R5VFJEQ0FSaUVBaWdCTWdrRlFJaW5KYWFoNkFJ=-w200-h112-p-df-rw
    PALAVRA-CHAVE: Fraude Licitação Bahia
    
    ============================================== DICT =====================================================
    {'titulo': 'SJBA - Justiça Federal condena seis pessoas por organização criminosa e fraude à licitação em Cansanção/BA; um réu é absolvido', 'conteudo': 'Conteúdo não encontrado', 'fonte': 'TRF1', 'datetime': '23/04/2025', 'link': 'https://news.google.com/read/CBMi7gFBVV95cUxNaWZUQlk1T2ttTlNfR1ZtQ3BIb1phdEFNLXVtM3haUzkwSkZJbkctWE00UUtZbVlQT2ZTOVhpb3RvcHJSYWhKWnRDN2MtR296RDdTOWZkMS0yU3Y3UUlGTzhwRkNINnc0QWNzOHNFNW80NEhqWHU2U29sM0cwd3lHZ1ZPZ1RxYTlmTExISkdiWFlpcVh4aFQ5Z3VEcWNuZUdEQVpGdE5wZk9NdjhDclN1a2I2X3hJQnUxSk1xUUNvb2tBZzJmQk56Y3dIOTlHSC1sajd2eHhlQ2VRVDhPM3Q4Z1VDWU50S1BncmFHdmRR?hl=pt-BR&gl=BR&ceid=BR%3Apt-419', 'img_url': 'https://news.google.com/api/attachments/CC8iL0NnNHdaMjlLYWprMVdrbElRV3R5VFJEQ0FSaUVBaWdCTWdrRlFJaW5KYWFoNkFJ=-w200-h112-p-df-rw', 'palavra_chave': 'Fraude Licitação Bahia'}
    =======================================================================================================

## Observações

- O script roda o Chrome em modo headless (sem interface gráfica).
- O processo pode demorar alguns minutos, dependendo da quantidade de termos e notícias encontradas.
- Evite executar múltiplas vezes em sequência para não ser bloqueado pelo Google News.

## Autor

Hugo Rios Brito

