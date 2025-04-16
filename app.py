import os
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

from fastapi import FastAPI, UploadFile, File
from processador import buscar_imagem_semelhante
import shutil

app = FastAPI()

@app.post("/comparar")
async def comparar(file: UploadFile = File(...)):
    caminho_temp = f"temp/{file.filename}"
    
    # Salva a imagem temporária
    with open(caminho_temp, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # Chama a função de comparação de imagem
    resultado = buscar_imagem_semelhante(caminho_temp)
    
    # Retorna o resultado, no caso, os dados da imagem e o tipo de correspondência
    return {
        "nome_arquivo": resultado["nome_arquivo"],
        "distancia": resultado["distancia"],
        "match": resultado["match"],
        "exata": resultado["exata"]
    }
