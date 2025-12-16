import os
import pandas as pd
from datetime import datetime

# Caminho base da pasta principal
base_path = '/home/roger/Projetos/Viagens/Tratados'

# Lista de encodings comuns (mantemos para segurança)
ENCODINGS = ['utf-8', 'latin-1', 'windows-1252', 'iso-8859-1', 'cp1252']

# Função para inferir tipo SQL Server (ajustada para ser mais precisa)
def infer_sql_type(series):
    # Remove valores nulos para análise mais precisa
    non_null = series.dropna()
    if len(non_null) == 0:
        return 'VARCHAR(255)'  # coluna vazia, fallback seguro
    
    dtype = non_null.dtype
    
    if pd.api.types.is_integer_dtype(dtype):
        return 'INT'
    elif pd.api.types.is_float_dtype(dtype):
        # Verifica se tem casas decimais reais
        if (non_null % 1 != 0).any():
            return 'DECIMAL(18,4)'  # ajuste conforme necessidade (pode mudar para 18,2 se for dinheiro)
        else:
            return 'INT'
    elif pd.api.types.is_bool_dtype(dtype):
        return 'BIT'
    elif pd.api.types.is_datetime64_any_dtype(dtype):
        return 'DATETIME2'
    else:
        # String/object: calcula tamanho máximo real
        max_len = non_null.astype(str).str.len().max()
        max_len = int(max_len) if not pd.isna(max_len) else 50
        max_len = max(max_len + 10, 50)  # margem mínima de 50
        if max_len > 4000:
            return 'VARCHAR(MAX)'  # SQL Server permite isso para colunas muito longas
        elif max_len > 1000:
            return f'VARCHAR(2000)'
        else:
            return f'NVARCHAR({max_len})'  # Use NVARCHAR para suportar acentos e caracteres especiais

# Função para ler CSV com separador ; e formato brasileiro
def analyze_csv(file_path):
    df = None
    used_encoding = None
    
    for enc in ENCODINGS:
        try:
            df = pd.read_csv(
                file_path,
                sep=';',              # separador ponto e vírgula
                decimal=',',          # decimal com vírgula
                thousands='.',        # milhar com ponto
                encoding=enc,
                low_memory=False,
                on_bad_lines='warn'   # avisa linhas problemáticas mas continua
            )
            used_encoding = enc
            print(f"{os.path.basename(file_path)} lido com sucesso (encoding: {enc})")
            break
        except UnicodeDecodeError:
            continue
        except Exception as e:
            print(f"Erro com encoding {enc} em {file_path}: {e}")
            continue
    
    if df is None:
        raise ValueError(f"Não foi possível ler o arquivo {file_path} com os encodings tentados.")

    report = {
        'file_name': os.path.basename(file_path),
        'encoding_used': used_encoding,
        'num_rows': len(df),
        'num_columns': len(df.columns),
        'columns': []
    }
    
    for col in df.columns:
        cleaned_name = col.strip()  # remove espaços no início/fim
        col_info = {
            'name': cleaned_name,
            'sql_type': infer_sql_type(df[col]),
            'sample_values': df[col].head(3).tolist()
        }
        report['columns'].append(col_info)
    
    return report

# === Processamento das pastas ===
reports = []

print("Iniciando análise dos CSVs...\n")

for subdir in os.listdir(base_path):
    subdir_path = os.path.join(base_path, subdir)
    if os.path.isdir(subdir_path):
        print(f"Entrando na pasta: {subdir}")
        for file in os.listdir(subdir_path):
            if file.lower().endswith('.csv'):
                file_path = os.path.join(subdir_path, file)
                try:
                    report = analyze_csv(file_path)
                    report['subdir'] = subdir
                    reports.append(report)
                except Exception as e:
                    print(f"Falha ao processar {file_path}: {e}")

# === Geração do relatório ===
output_file = 'relatorio_csv_completo.txt'
with open(output_file, 'w', encoding='utf-8') as f:
    f.write(f"RELATÓRIO DE ANÁLISE DE CSVs - GERADO EM {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}\n")
    f.write(f"Caminho base: {base_path}\n")
    f.write("="*80 + "\n\n")
    
    for rep in reports:
        f.write(f"Pasta: {rep['subdir']}\n")
        f.write(f"Arquivo: {rep['file_name']}\n")
        f.write(f"Encoding usado: {rep['encoding_used']}\n")
        f.write(f"Linhas: {rep['num_rows']:,} | Colunas: {rep['num_columns']}\n\n")
        f.write("Colunas analisadas:\n")
        for col in rep['columns']:
            samples = [str(s) if pd.notna(s) else 'NULL' for s in col['sample_values']]
            f.write(f"  • {col['name']:<40} → {col['sql_type']:<20} | Amostras: {samples}\n")
        f.write("\n" + "-"*80 + "\n\n")

print(f"\nAnálise concluída!")
print(f"Relatório salvo em: {os.path.abspath(output_file)}")
print(f"Total de arquivos processados: {len(reports)}")