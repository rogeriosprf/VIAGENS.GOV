import os
import pandas as pd
import pyodbc
from datetime import date

# ==================== CONEXÃO ====================
conn_str = (
    'DRIVER={ODBC Driver 18 for SQL Server};'
    'SERVER=localhost;'
    'DATABASE=GOVBR;'
    'UID=sa;'
    'PWD=StrongP@ssw0rd;'
    'TrustServerCertificate=yes;'
)

print("Conectando ao SQL Server...")
conn = pyodbc.connect(conn_str, autocommit=False)
cursor = conn.cursor()
cursor.fast_executemany = True

# ==================== CONFIGURAÇÕES ====================
pasta_viagem = '/home/roger/Projetos/Viagens/Tratados/Viagem'
schema_tabela = 'Viagens.Viagem'
batch_size = 10000

insert_sql = f"""
INSERT INTO {schema_tabela} (
    IdViagem, NumeroPropostaPCDP, Situacao, ViagemUrgente, JustificativaUrgencia,
    CodigoOrgaoSuperior, NomeOrgaoSuperior, CodigoOrgaoSolicitante, NomeOrgaoSolicitante,
    CpfViajante, NomeViajante, Cargo, Funcao, DescricaoFuncao,
    DataInicio, DataFim, Destinos, Motivo,
    ValorDiarias, ValorPassagens, ValorDevolucao, ValorOutrosGastos, Ano
) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
"""

total_geral = 0

for arquivo in sorted(os.listdir(pasta_viagem)):
    if not arquivo.endswith('.csv'):
        continue

    caminho = os.path.join(pasta_viagem, arquivo)
    
    try:
        ano = int(arquivo.split('_')[0])
    except:
        print(f"Pulando {arquivo} - não consegui extrair o ano")
        continue

    print(f"\nProcessando {arquivo} ({ano})...")

    df = pd.read_csv(
        caminho,
        sep=';',
        encoding='latin-1',
        decimal=',',
        thousands='.',
        dtype=str,
        low_memory=False
    )

    print(f"  Linhas lidas: {len(df):,}")

    # Rename - DICIONÁRIO EXATO
    rename_map = {
        'Identificador do processo de viagem': 'IdViagem',
        'Número da Proposta (PCDP)': 'NumeroPropostaPCDP',
        'Situação': 'Situacao',
        'Viagem Urgente': 'ViagemUrgente',
        'Justificativa Urgência Viagem': 'JustificativaUrgencia',
        'Código do órgão superior': 'CodigoOrgaoSuperior',
        'Nome do órgão superior': 'NomeOrgaoSuperior',
        'Código órgão solicitante': 'CodigoOrgaoSolicitante',
        'Nome órgão solicitante': 'NomeOrgaoSolicitante',
        'CPF viajante': 'CpfViajante',
        'Nome': 'NomeViajante',
        'Cargo': 'Cargo',
        'Função': 'Funcao',
        'Descrição Função': 'DescricaoFuncao',
        'Período - Data de início': 'DataInicio',
        'Período - Data de fim': 'DataFim',
        'Destinos': 'Destinos',
        'Motivo': 'Motivo',
        'Valor diárias': 'ValorDiarias',
        'Valor passagens': 'ValorPassagens',
        'Valor devolução': 'ValorDevolucao',
        'Valor outros gastos': 'ValorOutrosGastos'
    }
    df = df.rename(columns=rename_map)

    df['Ano'] = ano

    # Conversões
    df['IdViagem'] = pd.to_numeric(df['IdViagem'], errors='coerce')
    df['CodigoOrgaoSuperior'] = pd.to_numeric(df['CodigoOrgaoSuperior'], errors='coerce')
    df['CodigoOrgaoSolicitante'] = pd.to_numeric(df['CodigoOrgaoSolicitante'], errors='coerce')

    df['DataInicio'] = pd.to_datetime(df['DataInicio'], format='%d/%m/%Y', errors='coerce').dt.date
    df['DataFim'] = pd.to_datetime(df['DataFim'], format='%d/%m/%Y', errors='coerce').dt.date

    for col in ['ValorDiarias', 'ValorPassagens', 'ValorDevolucao', 'ValorOutrosGastos']:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col].str.replace('.', '').str.replace(',', '.'), errors='coerce')

    # Limpeza
    antes = len(df)
    df = df.dropna(subset=['IdViagem'])
    df['IdViagem'] = df['IdViagem'].astype('int64')
    print(f"  Linhas após limpeza: {len(df):,} (removidas {antes - len(df):,})")

    colunas_ordenadas = [
        'IdViagem', 'NumeroPropostaPCDP', 'Situacao', 'ViagemUrgente', 'JustificativaUrgencia',
        'CodigoOrgaoSuperior', 'NomeOrgaoSuperior', 'CodigoOrgaoSolicitante', 'NomeOrgaoSolicitante',
        'CpfViajante', 'NomeViajante', 'Cargo', 'Funcao', 'DescricaoFuncao',
        'DataInicio', 'DataFim', 'Destinos', 'Motivo',
        'ValorDiarias', 'ValorPassagens', 'ValorDevolucao', 'ValorOutrosGastos', 'Ano'
    ]

    valores = df[colunas_ordenadas].values.tolist()

    # Envio em lotes
    total_arquivo = 0
    for i in range(0, len(valores), batch_size):
        batch = valores[i:i + batch_size]
        try:
            cursor.executemany(insert_sql, batch)
            conn.commit()
            total_arquivo += len(batch)
            print(f"    Enviadas {total_arquivo:,} linhas deste arquivo...")
        except Exception as e:
            print(f"    Erro no batch {i//batch_size + 1}: {e}")
            conn.rollback()

    total_geral += total_arquivo
    print(f"{arquivo} concluído! {total_arquivo:,} linhas inseridas.")

    del df, valores

print(f"\nIMPORTAÇÃO DA PASTA VIAGEM FINALIZADA!")
print(f"Total de linhas inseridas: {total_geral:,}")
cursor.close()
conn.close()