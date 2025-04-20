import os
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

import clip
import torch
from PIL import Image
import numpy as np
import faiss

device = "cpu"
model, preprocess = clip.load("ViT-B/32", device=device)

def imagem_para_vetor(img_path):
    image = preprocess(Image.open(img_path)).unsqueeze(0).to(device)
    with torch.no_grad():
        vetor = model.encode_image(image)
    return vetor.cpu().numpy()

def criar_index(diretorio):
    nomes = []
    vetores = []

    for root, _, files in os.walk(diretorio):
        for nome in files:
            caminho = os.path.join(root, nome)

            try:
                vetor = imagem_para_vetor(caminho)
                nomes.append(nome)  # Só o nome do arquivo, sem subpasta
                vetores.append(vetor[0])
            except Exception as e:
                print(f"Erro ao processar {caminho}: {e}")

    if not vetores:
        raise ValueError("Nenhuma imagem válida encontrada.")

    index = faiss.IndexFlatL2(len(vetores[0]))
    index.add(np.array(vetores).astype('float32'))
    return index, nomes

# Carrega index e nomes
index, nomes = criar_index("db_images")

def buscar_imagem_semelhante(caminho_imagem):
    vetor = imagem_para_vetor(caminho_imagem)
    dist, idx = index.search(vetor.astype('float32'), 1)

    distancia = float(dist[0][0])

    if distancia > 40:
        # Distância muito alta, nada relacionado
        return None

    nome_arquivo = nomes[idx[0][0]]

    exata = distancia <= 2
    match = "exata" if exata else "semelhante"

    return {
        "nome_arquivo": nome_arquivo,
        "distancia": distancia,
        "match": match,
        "exata": exata
    }
