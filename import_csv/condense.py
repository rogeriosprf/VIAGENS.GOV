import os
import pandas as pd

# ==================== CONFIGURAÇÕES ====================
base_path = '/home/roger/Projetos/Viagens/Tratados'
pastas = ['Pagamento', 'Trecho', 'Passagem', 'Viagem']

resumo_linhas = []

print("Gerando resumo agrupado por ano e mês...\n")

for pasta in pastas:
    caminho_pasta = os.path.join(base_path, pasta)
    if not os.path.exists(caminho_pasta):
        print(f"Pasta não encontrada: {caminho_pasta}")
        continue
    
    print(f"Processando pasta: {pasta}")
    
    for arquivo in sorted(os.listdir(caminho_pasta)):
        if not arquivo.lower().endswith('.csv'):
            continue
        
        caminho_arquivo = os.path.join(caminho_pasta, arquivo)
        
        # Extrai ano
        try:
            ano = int(arquivo.split('_')[0])
        except:
            print(f"  Pulando {arquivo} - ano inválido")
            continue
        
        print(f"  Lendo {arquivo} ({ano})...")
        
        # Lê o CSV (tudo string para evitar erros)
        df = pd.read_csv(
            caminho_arquivo,
            sep=';',
            encoding='latin-1',
            dtype=str,
            low_memory=False
        )
        
        total_linhas = len(df)
        
        # Identifica colunas de data e valor
        colunas_data = [c for c in df.columns if 'data' in c.lower()]
        colunas_valor = [c for c in df.columns if 'valor' in c.lower()]
        
        # Converte datas
        df_mes = pd.DataFrame({'Mes': 'Todos', 'Linhas': total_linhas, 'Valor_Total': 0}, index=[0])
        
        if colunas_data:
            # Usa a primeira coluna de data encontrada
            col_data = colunas_data[0]
            df[col_data] = pd.to_datetime(df[col_data], format='%d/%m/%Y', errors='coerce')
            df = df.dropna(subset=[col_data])  # remove datas inválidas
            df['Mes'] = df[col_data].dt.month
            
            df_mes = df.groupby('Mes').size().reset_index(name='Linhas')
            df_mes['Mes'] = df_mes['Mes'].astype(int)
        
        # Soma valores
        valor_total_mes = 0
        if colunas_valor:
            col_valor = colunas_valor[0]
            df[col_valor] = pd.to_numeric(df[col_valor].str.replace('.', '').str.replace(',', '.'), errors='coerce')
            if colunas_data:
                valor_por_mes = df.groupby('Mes')[col_valor].sum().reset_index()
                df_mes = df_mes.merge(valor_por_mes, on='Mes', how='left')
                df_mes = df_mes.rename(columns={col_valor: 'Valor_Total'})
                df_mes['Valor_Total'] = df_mes['Valor_Total'].fillna(0)
            else:
                valor_total_mes = df[col_valor].sum(skipna=True)
        
        df_mes['Pasta'] = pasta
        df_mes['Ano'] = ano
        df_mes['Valor_Total'] = df_mes.get('Valor_Total', valor_total_mes)
        
        resumo_linhas.extend(df_mes.to_dict('records'))
        
        print(f"    {total_linhas:,} linhas processadas")

# ==================== GERA O CSV FINAL ====================
df_resumo = pd.DataFrame(resumo_linhas)
df_resumo = df_resumo[['Pasta', 'Ano', 'Mes', 'Linhas', 'Valor_Total']]
df_resumo = df_resumo.sort_values(['Pasta', 'Ano', 'Mes'])

df_resumo.to_csv('resumo_por_ano_mes.csv', index=False, sep=';', encoding='utf-8-sig')

print("\nResumo gerado com sucesso!")
print("Arquivo: resumo_por_ano_mes.csv")
print("\nPrévia dos primeiros registros:")
print(df_resumo.head(20).to_string(index=False))