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
    for nome in os.listdir(diretorio):
        caminho = os.path.join(diretorio, nome)
        vetor = imagem_para_vetor(caminho)
        nomes.append(nome)
        vetores.append(vetor[0])
    index = faiss.IndexFlatL2(len(vetores[0]))
    index.add(np.array(vetores).astype('float32'))
    return index, nomes

# Carrega index e nomes
index, nomes = criar_index("db_images")

def buscar_imagem_semelhante(caminho_imagem):
    vetor = imagem_para_vetor(caminho_imagem)
    dist, idx = index.search(vetor.astype('float32'), 1)
    
    nome_arquivo = nomes[idx[0][0]]
    distancia = float(dist[0][0])

    # Definindo limites de similaridade mais flexíveis
    limite_exata = 0.3  # Aumente esse valor para permitir mais variações
    limite_similar = 0.6  # Aumente o limite de similaridade para permitir mais variações

    # Defina se é exata, semelhante ou nenhuma relação
    if distancia <= limite_exata:
        match = "exata"
    elif distancia <= limite_similar:
        match = "semelhante"
    else:
        match = "nenhuma relação"

    return {
        "nome_arquivo": nome_arquivo,
        "distancia": distancia,
        "match": match,
        "exata": (match == "exata")
    }
