import zipfile
import shutil
from pathlib import Path
import tempfile

# Pastas
RAW_DIR = Path("/home/roger/Projetos/Viagens/Raw")
TRATADOS_DIR = Path("/home/roger/Projetos/Viagens/Tratados")

# Mapeamento dos CSVs para as subpastas
SUBPASTAS = {
    "Pagamento": "Pagamento",
    "Passagem": "Passagem",
    "Trecho": "Trecho",
    "Viagem": "Viagem"
}

# Loop pelos arquivos zip
for zip_path in RAW_DIR.glob("*_20251130_Viagens.zip"):
    print(f"Processando {zip_path.name}...")
    
    # Cria uma pasta temporária para extrair
    with tempfile.TemporaryDirectory() as tmpdirname:
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(tmpdirname)
        
        tmp_path = Path(tmpdirname)
        
        # Mover cada CSV para a pasta correspondente
        for tipo, pasta in SUBPASTAS.items():
            for csv_file in tmp_path.glob(f"*{tipo}.csv"):
                destino = TRATADOS_DIR / pasta / csv_file.name
                shutil.move(str(csv_file), destino)

print("Todos os arquivos foram organizados!")
