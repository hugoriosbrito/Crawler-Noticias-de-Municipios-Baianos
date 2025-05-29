import pandas as pd

def processar_linhas(df):
    """
    Função para realizar o pós-processamento dos dados, separando os municipios que estão na mesma linha em municipios_citados, repetindo a noticia abaixo após separação e separando os IDs dos municipios em outra coluna.

    Args:
        df (pd.DataFrame): DataFrame contendo os dados a serem processados.

    Returns:
        pd.DataFrame: DataFrame após o pós-processamento.
    """
    
    novas_linhas = []
    
    for index, row in df.iterrows():
        if isinstance(row['municipios_citados'], str) and ',' in row['municipios_citados']:
            municipios = [m.strip() for m in row['municipios_citados'].split(',')]
            
            for municipio in municipios:
                nova_linha = row.copy()
                nova_linha['municipios_citados'] = municipio
                novas_linhas.append(nova_linha)
        else:
            novas_linhas.append(row)

    df_processado = pd.DataFrame(novas_linhas)
    
    df_processado['id_municipios'] = None

    for index, row in df_processado.iterrows():
        if isinstance(row['municipios_citados'], str) and '-' in row['municipios_citados']:
            partes = row['municipios_citados'].split('-')
            df_processado.at[index, 'municipios_citados'] = partes[0].strip()
            df_processado.at[index, 'id_municipios'] = partes[1].strip()

    df_processado.reset_index(drop=True, inplace=True)

    return df_processado
