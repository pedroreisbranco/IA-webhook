import os
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"
from fastapi import FastAPI, UploadFile, File
from processador import buscar_imagem_semelhante
import shutil
app = FastAPI()

@app.post("/comparar")
async def comparar(file: UploadFile = File(...)):
    caminho_temp = f"temp/{file.filename}"
    with open(caminho_temp, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    resultado = buscar_imagem_semelhante(caminho_temp)
    return {"mais_semelhante": resultado}
