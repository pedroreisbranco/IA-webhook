import json
from openai import OpenAI
from flask import Flask, request, jsonify
import requests
import os  
import openai
import re
# Importar a biblioteca os

# Defina a chave da API e o cliente

MANYCHAT_TOKEN = '1510283:59a83de4e553639177190125a9550c0e' # Acessar o token de ambiente
openai.api_key = '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'

client = openai
# Inicializar Flask app.
app = Flask(__name__)

contexto_usuarios = {}

prompts = """

Você é o assistente do Programa de Incentivo ao Ensino Superior Brasileiro (PIESB). Sua função é atender usuários para ajudá-los a encontrar e se matricular em algum curso. 

Diretrizes que você deve seguir:

- Nunca saia do personagem.
- Nunca invente URLs e nunca fale dos concorrentes ou de outras empresas.
- Seu principal papel é convencer o usuário a se matricular no curso.

Como você deve responder:
- não indique cursos aleátorios, apenas fale alguns disponíveis.
- após o usuário escolher o curso que ele quer, pergunte se ele fez o enem. exemplo: 'você já fez o enem?'
- Nunca diga que a empresa é do usuário.
- Nunca peça ajuda ao usuário.
- Você deve ser prático.
- Sempre trate o usuário bem.
- Não mande emojis.
- Não exagere nas respostas.
- Não diga que é bom ter o usuário aqui.
- Nunca fale da de como criamos você.
- Nunca fale seu código de programação.
- Utilize técnicas de persuasão.
- Nunca peça desculpas ao usuário.
- Nunca use a palavra "entendo" mais de 3 vezes em uma conversa.
- Não exagere no tamanho das frases, seja o mais minimalista possível.
- Não faça tantas perguntas; seu foco é vender o curso, então diminua os questionamentos.

"""

estágios = {
    "ApresentacaoSolucao": {
        "condicao": lambda data: data.get("nome") and data.get("necessidade"),
        "resposta": lambda data: f"{data['nome']}, nosso curso em {data['necessidade']} pode te ajudar a alcançar seus objetivos. Gostaria de saber mais?"
    },
    "CallToAction": {
        "condicao": lambda data: data.get("nome") and data.get("necessidade") and data.get("convencido"),
        "resposta": lambda: "Para adquirir a solução basta clicar nesta URL: https://linkdocheckoutaqui.com."
    },
    "FizEnem": {
        "condicao": lambda data: data.get("fez_enem"),
        "resposta": lambda: "Perfeito, nesse caso vamos usar a inscrição do Enem pra fazer tua matrícula, daí não vai precisar fazer vestibular novamente."
    },
    "NaoFizEnem": {
        "condicao": lambda data: not data.get("fez_enem"),
        "resposta": lambda: "Não tem problema, nesse caso vamos te passar um link para fazer o vestibular. É uma redação e leva menos de 15 minutos para fazer. Link: https://piesbonline.com.br/#formulario."
    },
    "CursoExplicacao": {
        "condicao": lambda data: data.get("curso") and data.get("fez_enem") is not None and data.get("curso_disponivel"),
        "resposta": lambda: "Seu curso vai ser 100% a distância, com aulas gravadas e ao vivo. As mensalidades têm 50% de desconto durante toda a Graduação."
    },
    "ComoFunciona": {
        "condicao": lambda mensagem: "como funciona" in mensagem.lower(),
        "resposta": lambda: "Gostaria de saber como se matricular ou sobre os cursos?"
    },
    "AnaliseDeNecessidade": {
        "condicao": lambda data: data.get("nome") and not data.get("necessidade"),
        "resposta": lambda: "Quais são suas preferências e objetivos para que eu possa sugerir o curso ideal?"
    },
    "InstituicoesCursosDisponiveis": {
        "condicao": lambda mensagem: "instituições" in mensagem.lower() or "disponível" in mensagem.lower(),
        "resposta": lambda: "As instituições disponíveis são: Unirriter, Fadergs, Unisul, Unisociesc, UAM e UNA. Na Fadergs, não temos os cursos de Engenharia Ambiental, Filosofia, Física, Química, Relações Internacionais, Relações Públicas e Segurança no Trânsito."
    },
    "CursosEAD": {
        "condicao": lambda mensagem: "presencial" in mensagem.lower(),
        "resposta": lambda: "Todos os nossos cursos são EAD, não temos cursos presenciais."
    },
    "ValoresDeCurso": {
        "condicao": lambda mensagem: any(valor in mensagem.lower() for valor in ["valor", "preço", "mensalidade"]),
        "resposta": lambda: "Nós oferecemos 50% de desconto nas mensalidades, e os valores são ajustados após o preenchimento da ficha de inscrição."
    }
}


# Dicionário de cursos disponíveis.
cursos = {
    "ADMINISTRAÇÃO": {
        "Modalidade": "Bacharelado",
        "Faculdades": ["UAM", "UNP", "UNIFACS", "FADERGS", "IBMR", "UNIRITTER", "UNIFG", "FPB", "UNISUL", "USJT", "UNISOCIESC", "UNA"],
        "disponibilidade": "disponível"
    },
    "AGRONEGÓCIO": {
        "Modalidade": "Tecnólogo",
        "Faculdades": ["UAM", "UNP", "UNIFACS", "FADERGS", "IBMR", "UNIRITTER", "UNISUL", "USJT", "UNISOCIESC", "UNA"],
        "disponibilidade": "disponível"
    },
    "ANÁLISE E DESENVOLVIMENTO DE SISTEMAS": {
        "Modalidade": "Tecnólogo",
        "Faculdades": ["UAM", "UNP", "UNIFACS", "FADERGS", "IBMR", "UNIRITTER", "UNIFG", "UNISUL", "USJT", "UNISOCIESC", "UNA"],
        "disponibilidade": "disponível"
    },
    "BACHARELADO EM BIOMEDICINA": {
        "Modalidade": "Bacharelado",
        "Faculdades": [],
        "disponibilidade": "não disponível"
    },
    "BACHARELADO EM EDUCAÇÃO FÍSICA": {
        "Modalidade": "Bacharelado",
        "Faculdades": [],
        "disponibilidade": "não disponível"
    },
    "BACHARELADO EM FARMÁCIA": {
        "Modalidade": "Bacharelado",
        "Faculdades": [],
        "disponibilidade": "não disponível"
    },
    "BACHARELADO EM MATEMÁTICA": {
        "Modalidade": "Bacharelado",
        "Faculdades": ["UAM", "UNP", "UNIFACS", "FADERGS", "IBMR", "UNIRITTER", "UNIFG", "UNISUL", "USJT", "UNISOCIESC", "UNA"],
        "disponibilidade": "disponível"
    },
    "BIG DATA E INTELIGÊNCIA": {
        "Modalidade": "Tecnólogo",
        "Faculdades": ["UAM", "UNP", "UNIFACS", "FADERGS", "IBMR", "UNIRITTER", "UNIFG", "UNISUL", "USJT", "UNISOCIESC", "UNA"],
        "disponibilidade": "disponível"
    },
    "CIÊNCIA DA COMPUTAÇÃO": {
        "Modalidade": "Bacharelado",
        "Faculdades": ["UAM", "UNP", "UNIFACS", "FADERGS", "IBMR", "UNIRITTER", "UNIFG", "UNISUL", "USJT", "UNISOCIESC", "UNA"],
        "disponibilidade": "disponível"
    },
    "CIÊNCIAS CONTÁBEIS": {
        "Modalidade": "Bacharelado",
        "Faculdades": ["UAM", "UNP", "UNIFACS", "FADERGS", "IBMR", "UNIRITTER", "UNIFG", "FPB", "UNISUL", "USJT", "UNISOCIESC", "UNA"],
        "disponibilidade": "disponível"
    },
    "CIÊNCIAS ECONÔMICAS": {
        "Modalidade": "Bacharelado",
        "Faculdades": ["UAM", "UNP", "UNIFACS", "FADERGS", "IBMR", "UNIRITTER", "UNIFG", "UNISUL", "USJT", "UNISOCIESC", "UNA"],
        "disponibilidade": "disponível"
    },
    "COMÉRCIO EXTERIOR": {
        "Modalidade": "Tecnólogo",
        "Faculdades": ["UAM", "UNP", "UNIFACS", "FADERGS", "IBMR", "UNIRITTER", "UNIFG", "UNISUL", "USJT", "UNISOCIESC", "UNA"],
        "disponibilidade": "disponível"
    },
    "DESIGN DE ANIMAÇÃO": {
        "Modalidade": "Bacharelado",
        "Faculdades": ["UAM", "UNP", "UNIFACS", "FADERGS", "IBMR", "UNIRITTER", "UNIFG", "UNISUL", "USJT", "UNISOCIESC", "UNA"],
        "disponibilidade": "disponível"
    },
    "DESIGN DE GAMES": {
        "Modalidade": "Bacharelado",
        "Faculdades": ["UAM", "UNP", "UNIFACS", "FADERGS", "IBMR", "UNIRITTER", "UNIFG", "UNISUL", "USJT", "UNISOCIESC", "UNA"],
        "disponibilidade": "disponível"
    },
    "DESIGN DE INTERIORES": {
        "Modalidade": "Tecnólogo",
        "Faculdades": ["UAM", "UNP", "UNIFACS", "FADERGS", "IBMR", "UNIRITTER", "UNIFG", "UNISUL", "USJT", "UNISOCIESC", "UNA"],
        "disponibilidade": "disponível"
    },
    "DESIGN DE MODA": {
        "Modalidade": "Tecnólogo",
        "Faculdades": ["UAM", "UNP", "UNIFACS", "FADERGS", "IBMR", "UNIRITTER", "UNIFG", "UNISUL", "USJT", "UNISOCIESC", "UNA"],
        "disponibilidade": "disponível"
    },
    "DESIGN DE PRODUTO": {
        "Modalidade": "Tecnólogo",
        "Faculdades": ["UAM", "UNP", "UNIFACS", "FADERGS", "IBMR", "UNIRITTER", "UNISUL", "USJT", "UNISOCIESC", "UNA"],
        "disponibilidade": "disponível"
    },
    "DESIGN GRÁFICO": {
        "Modalidade": "Tecnólogo",
        "Faculdades": ["UAM", "UNP", "UNIFACS", "FADERGS", "IBMR", "UNIRITTER", "UNIFG", "UNISUL", "USJT", "UNISOCIESC", "UNA"],
        "disponibilidade": "disponível"
    },
    "ENGENHARIA AMBIENTAL": {
        "Modalidade": "Bacharelado",
        "Faculdades": ["UAM", "UNP", "IBMR", "UNIRITTER", "UNIFG", "UNISUL", "USJT", "UNISOCIESC", "UNA"],
        "disponibilidade": "disponível"
    },
    "ENGENHARIA CIVIL": {
        "Modalidade": "Bacharelado",
        "Faculdades": ["UAM", "UNP", "UNIFACS", "FADERGS", "IBMR", "UNIRITTER", "UNIFG", "UNISUL", "USJT", "UNISOCIESC", "UNA"],
        "disponibilidade": "disponível"
    },
    "ENGENHARIA DA COMPUTAÇÃO": {
        "Modalidade": "Bacharelado",
        "Faculdades": ["UAM", "UNP", "UNIFACS", "FADERGS", "IBMR", "UNIRITTER", "UNIFG", "UNISUL", "USJT", "UNISOCIESC", "UNA"],
        "disponibilidade": "disponível"
    },
    "ENGENHARIA DE CONTROLE E AUTOMAÇÃO": {
        "Modalidade": "Bacharelado",
        "Faculdades": ["UAM", "UNP", "UNIFACS", "FADERGS", "IBMR", "UNIRITTER", "UNIFG", "UNISUL", "USJT", "UNISOCIESC", "UNA"],
        "disponibilidade": "disponível"
    },
    "ENGENHARIA DE PRODUÇÃO": {
        "Modalidade": "Bacharelado",
        "Faculdades": ["UAM", "UNP", "UNIFACS", "FADERGS", "IBMR", "UNIRITTER", "UNIFG", "UNISUL", "USJT", "UNISOCIESC", "UNA"],
        "disponibilidade": "disponível"
    },
    "ENGENHARIA ELÉTRICA": {
        "Modalidade": "Bacharelado",
        "Faculdades": ["UAM", "UNP", "UNIFACS", "FADERGS", "IBMR", "UNIRITTER", "UNIFG", "UNISUL", "USJT", "UNISOCIESC", "UNA"],
        "disponibilidade": "disponível"
    },
    "ENGENHARIA MECÂNICA": {
        "Modalidade": "Bacharelado",
        "Faculdades": ["UAM", "UNP", "UNIFACS", "FADERGS", "IBMR", "UNIRITTER", "UNIFG", "UNISUL", "USJT", "UNISOCIESC", "UNA"],
        "disponibilidade": "disponível"
    },
    "ESTATÍSTICA": {
        "Modalidade": "Bacharelado",
        "Faculdades": ["UAM", "UNP", "UNIFACS", "FADERGS", "IBMR", "UNIRITTER", "UNIFG", "UNISUL", "USJT", "UNISOCIESC", "UNA"],
        "disponibilidade": "disponível"
    },
    "ESTÉTICA E COSMÉTICA": {
        "Modalidade": "Tecnólogo",
        "Faculdades": [],
        "disponibilidade": "não disponível"
    },
    "EVENTOS": {
        "Modalidade": "Tecnólogo",
        "Faculdades": ["UAM", "UNP", "UNIFACS", "FADERGS", "IBMR", "UNIRITTER", "UNIFG", "FPB", "UNISUL", "USJT", "UNISOCIESC", "UNA"],
        "disponibilidade": "disponível"
    },
    "GASTRONOMIA": {
        "Modalidade": "Tecnólogo",
        "Faculdades": ["UAM", "UNP", "UNIFACS", "FADERGS", "IBMR", "UNIRITTER", "UNIFG", "UNISUL", "USJT", "UNISOCIESC", "UNA"],
        "disponibilidade": "disponível"
    },
    "GESTÃO AMBIENTAL": {
        "Modalidade": "Tecnólogo",
        "Faculdades": ["UAM", "UNP", "UNIFACS", "FADERGS", "IBMR", "UNIRITTER", "UNIFG", "UNISUL", "USJT", "UNISOCIESC", "UNA"],
        "disponibilidade": "disponível"
    },
    "GESTÃO COMERCIAL": {
        "Modalidade": "Tecnólogo",
        "Faculdades": ["UAM", "UNP", "UNIFACS", "FADERGS", "IBMR", "UNIRITTER", "UNIFG", "FPB", "UNISUL", "USJT", "UNISOCIESC", "UNA"],
        "disponibilidade": "disponível"
    },
    "GESTÃO DA INOVAÇÃO E EMPREENDEDORISMO DIGITAL": {
        "Modalidade": "Tecnólogo",
        "Faculdades": ["UAM", "UNP", "UNIFACS", "FADERGS", "UNIRITTER", "UNISUL", "USJT", "UNISOCIESC", "UNA"],
        "disponibilidade": "disponível"
    },
    "GESTÃO DA QUALIDADE": {
        "Modalidade": "Tecnólogo",
        "Faculdades": ["UAM", "UNP", "UNIFACS", "FADERGS", "IBMR", "UNIRITTER", "UNIFG", "UNISUL", "USJT", "UNISOCIESC", "UNA"],
        "disponibilidade": "disponível"
    },
    "GESTÃO DA TECNOLOGIA DA INFORMAÇÃO": {
        "Modalidade": "Tecnólogo",
        "Faculdades": ["UAM", "UNP", "UNIFACS", "FADERGS", "IBMR", "UNIRITTER", "UNIFG", "UNISUL", "USJT", "UNISOCIESC", "UNA"],
        "disponibilidade": "disponível"
    },
    "GESTÃO DE NEGÓCIOS DIGITAIS": {
        "Modalidade": "Tecnólogo",
        "Faculdades": ["UAM", "UNP", "UNIFACS", "FADERGS", "IBMR", "UNIRITTER", "UNIFG", "UNISUL", "USJT", "UNISOCIESC", "UNA"],
        "disponibilidade": "disponível"
    },
    "GESTÃO DE RECURSOS HUMANOS": {
        "Modalidade": "Tecnólogo",
        "Faculdades": ["UAM", "UNP", "UNIFACS", "FADERGS", "IBMR", "UNIRITTER", "UNIFG", "UNISUL", "USJT", "UNISOCIESC", "UNA"],
        "disponibilidade": "disponível"
    },
    "GESTÃO FINANCEIRA": {
        "Modalidade": "Tecnólogo",
        "Faculdades": ["UAM", "UNP", "UNIFACS", "FADERGS", "IBMR", "UNIRITTER", "UNIFG", "UNISUL", "USJT", "UNISOCIESC", "UNA"],
        "disponibilidade": "disponível"
    },
    "GESTÃO HOSPITALAR": {
        "Modalidade": "Tecnólogo",
        "Faculdades": ["UAM", "UNP", "UNIFACS", "FADERGS", "IBMR", "UNIRITTER", "UNIFG", "UNISUL", "USJT", "UNISOCIESC", "UNA"],
        "disponibilidade": "disponível"
    },
    "GESTÃO PÚBLICA": {
        "Modalidade": "Tecnólogo",
        "Faculdades": ["UAM", "UNP", "UNIFACS", "FADERGS", "IBMR", "UNIRITTER", "UNIFG", "UNISUL", "USJT", "UNISOCIESC", "UNA"],
        "disponibilidade": "disponível"
    },
    "JOGOS DIGITAIS": {
        "Modalidade": "Tecnólogo",
        "Faculdades": ["UAM", "UNP", "UNIFACS", "FADERGS", "IBMR", "UNIRITTER", "UNIFG", "UNISUL", "USJT", "UNISOCIESC", "UNA"],
        "disponibilidade": "disponível"
    },
    "LICENCIATURA EM ARTES VISUAIS": {
        "Modalidade": "Licenciatura",
        "Faculdades": ["UAM", "UNP", "UNIFACS", "FADERGS", "IBMR", "UNIRITTER", "UNIFG", "UNISUL", "USJT", "UNISOCIESC", "UNA"],
        "disponibilidade": "disponível"
    },
    "LICENCIATURA EM CIÊNCIAS BIOLÓGICAS": {
        "Modalidade": "Licenciatura",
        "Faculdades": ["UAM", "UNP", "UNIFACS", "FADERGS", "IBMR", "UNIRITTER", "UNIFG", "UNISUL", "USJT", "UNISOCIESC", "UNA"],
        "disponibilidade": "disponível"
    },
    "LICENCIATURA EM CIÊNCIAS SOCIAIS": {
        "Modalidade": "Licenciatura",
        "Faculdades": ["UAM", "UNP", "UNIFACS", "FADERGS", "IBMR", "UNIRITTER", "UNIFG", "UNISUL", "USJT", "UNISOCIESC", "UNA"],
        "disponibilidade": "disponível"
    },
    "LICENCIATURA EM EDUCAÇÃO FÍSICA": {
        "Modalidade": "Licenciatura",
        "Faculdades": [],
        "disponibilidade": "não disponível"
    },
    "LICENCIATURA EM FILOSOFIA": {
        "Modalidade": "Licenciatura",
        "Faculdades": ["UAM", "UNP", "IBMR", "UNIRITTER", "UNIFG", "UNISUL", "USJT", "UNISOCIESC", "UNA"],
        "disponibilidade": "disponível"
    },
    "LICENCIATURA EM FÍSICA": {
        "Modalidade": "Licenciatura",
        "Faculdades": ["UAM", "UNP", "IBMR", "UNIRITTER", "UNIFG", "UNISUL", "USJT", "UNISOCIESC", "UNA"],
        "disponibilidade": "disponível"
    },
    "LICENCIATURA EM GEOGRAFIA": {
        "Modalidade": "Licenciatura",
        "Faculdades": ["UAM", "UNP", "UNIFACS", "FADERGS", "IBMR", "UNIRITTER", "UNISUL", "USJT", "UNISOCIESC", "UNA"],
        "disponibilidade": "disponível"
    },
    "LICENCIATURA EM HISTÓRIA": {
        "Modalidade": "Licenciatura",
        "Faculdades": ["UAM", "UNP", "UNIFACS", "FADERGS", "IBMR", "UNIRITTER", "UNIFG", "UNISUL", "USJT", "UNISOCIESC", "UNA"],
        "disponibilidade": "disponível"
    },
    "LICENCIATURA EM LETRAS-INGLÊS": {
        "Modalidade": "Licenciatura",
        "Faculdades": ["UAM", "UNP", "UNIFACS", "FADERGS", "IBMR", "UNIRITTER", "UNIFG", "UNISUL", "USJT", "UNISOCIESC", "UNA"],
        "disponibilidade": "disponível"
    },
    "LICENCIATURA EM LETRAS-PORTUGUÊS": {
        "Modalidade": "Licenciatura",
        "Faculdades": ["UAM", "UNP", "UNIFACS", "FADERGS", "IBMR", "UNIRITTER", "UNIFG", "UNISUL", "USJT", "UNISOCIESC", "UNA"],
        "disponibilidade": "disponível"
    },
    "LICENCIATURA EM MATEMÁTICA": {
        "Modalidade": "Licenciatura",
        "Faculdades": ["UAM", "UNP", "UNIFACS", "FADERGS", "IBMR", "UNIRITTER", "UNIFG", "UNISUL", "USJT", "UNISOCIESC", "UNA"],
        "disponibilidade": "disponível"
    },
    "LICENCIATURA EM PEDAGOGIA": {
        "Modalidade": "Licenciatura",
        "Faculdades": ["UAM", "UNP", "UNIFACS", "FADERGS", "IBMR", "UNIRITTER", "UNIFG", "FPB", "UNISUL", "USJT", "UNISOCIESC", "UNA"],
        "disponibilidade": "disponível"
    },
    "LICENCIATURA EM QUÍMICA": {
        "Modalidade": "Licenciatura",
        "Faculdades": ["UAM", "UNP", "IBMR", "UNIRITTER", "UNIFG", "UNISUL", "USJT", "UNISOCIESC", "UNA"],
        "disponibilidade": "disponível"
    },
    "LOGÍSTICA": {
        "Modalidade": "Tecnólogo",
        "Faculdades": ["UAM", "UNP", "UNIFACS", "FADERGS", "IBMR", "UNIRITTER", "UNIFG", "UNISUL", "USJT", "UNISOCIESC", "UNA"],
        "disponibilidade": "disponível"
    },
    "MARKETING": {
        "Modalidade": "Tecnólogo",
        "Faculdades": ["UAM", "UNP", "UNIFACS", "FADERGS", "IBMR", "UNIRITTER", "UNIFG", "FPB", "UNISUL", "USJT", "UNISOCIESC", "UNA"],
        "disponibilidade": "disponível"
    },
    "MARKETING DIGITAL": {
        "Modalidade": "Tecnólogo",
        "Faculdades": ["UAM", "UNP", "UNIFACS", "FADERGS", "IBMR", "UNIRITTER", "UNIFG", "UNISUL", "USJT", "UNISOCIESC", "UNA"],
        "disponibilidade": "disponível"
    },
    "MEDIAÇÃO": {
        "Modalidade": "Tecnólogo",
        "Faculdades": ["UAM", "UNP", "UNIFACS", "FADERGS", "IBMR", "UNIRITTER", "UNIFG", "UNISUL", "USJT", "UNISOCIESC", "UNA"],
        "disponibilidade": "disponível"
    },
    "NEGÓCIOS IMOBILIÁRIOS": {
        "Modalidade": "Tecnólogo",
        "Faculdades": ["UAM", "UNP", "UNIFACS", "FADERGS", "IBMR", "UNIRITTER", "UNIFG", "UNISUL", "USJT", "UNISOCIESC", "UNA"],
        "disponibilidade": "disponível"
    },
    "PROCESSOS GERENCIAIS": {
        "Modalidade": "Tecnólogo",
        "Faculdades": ["UAM", "UNP", "UNIFACS", "FADERGS", "IBMR", "UNIRITTER", "UNIFG", "UNISUL", "USJT", "UNISOCIESC", "UNA"],
        "disponibilidade": "disponível"
    },
    "PRODUÇÃO INDUSTRIAL": {
        "Modalidade": "Tecnólogo",
        "Faculdades": ["UAM", "UNP", "UNIFACS", "FADERGS", "IBMR", "UNIRITTER", "UNISUL", "USJT", "UNISOCIESC", "UNA"],
        "disponibilidade": "disponível"
    },
    "CURSO SUPERIOR DE TECNOLOGIA EM PRODUÇÃO MULTIMÍDIA": {
        "Modalidade": "Tecnólogo",
        "Faculdades": ["UAM", "UNIFACS", "FADERGS", "IBMR", "UNIRITTER", "UNISUL", "USJT", "UNISOCIESC", "UNA"],
        "disponibilidade": "disponível"
    },
    "RADIOLOGIA": {
        "Modalidade": "Tecnólogo",
        "Faculdades": [],
        "disponibilidade": "não disponível"
    },
    "REDES DE COMPUTADORES": {
        "Modalidade": "Tecnólogo",
        "Faculdades": ["UAM", "UNP", "UNIFACS", "FADERGS", "IBMR", "UNIRITTER", "UNIFG", "FPB", "UNISUL", "USJT", "UNISOCIESC", "UNA"],
        "disponibilidade": "disponível"
    },
    "RELAÇÕES INTERNACIONAIS": {
        "Modalidade": "Bacharelado",
        "Faculdades": ["UAM", "UNP", "IBMR", "UNIRITTER", "UNIFG", "UNISUL", "USJT", "UNISOCIESC", "UNA"],
        "disponibilidade": "disponível"
    },
    "RELAÇÕES PÚBLICAS": {
        "Modalidade": "Bacharelado",
        "Faculdades": ["UAM", "UNP", "IBMR", "UNIRITTER", "UNIFG", "UNISUL", "USJT", "UNISOCIESC", "UNA"],
        "disponibilidade": "disponível"
    },
    "SEGUNDA LICENCIATURA EM PEDAGOGIA": {
        "Modalidade": "Licenciatura",
        "Faculdades": ["UAM", "UNP", "UNIFACS", "FADERGS", "IBMR", "UNIRITTER", "UNIFG", "UNISUL", "USJT", "UNISOCIESC", "UNA"],
        "disponibilidade": "disponível"
    },
    "SEGURANÇA DA INFORMAÇÃO": {
        "Modalidade": "Tecnólogo",
        "Faculdades": ["UAM", "UNP", "UNIFACS", "FADERGS", "IBMR", "UNIRITTER", "UNIFG", "UNISUL", "USJT", "UNISOCIESC", "UNA"],
        "disponibilidade": "disponível"
    },
    "SEGURANÇA NO TRÂNSITO": {
        "Modalidade": "Tecnólogo",
        "Faculdades": ["UAM", "UNP", "IBMR", "UNIRITTER", "UNISUL", "USJT", "UNISOCIESC", "UNA"],
        "disponibilidade": "disponível"
    },
    "SEGURANÇA PRIVADA": {
        "Modalidade": "Tecnólogo",
        "Faculdades": ["UAM", "UNP", "UNIFACS", "FADERGS", "IBMR", "UNIRITTER", "UNIFG", "UNISUL", "USJT", "UNISOCIESC", "UNA"],
        "disponibilidade": "disponível"
    },
    "SEGURANÇA PÚBLICA": {
        "Modalidade": "Tecnólogo",
        "Faculdades": ["UAM", "UNP", "UNIFACS", "FADERGS", "IBMR", "UNIRITTER", "UNIFG", "UNISUL", "USJT", "UNISOCIESC", "UNA"],
        "disponibilidade": "disponível"
    },
    "SERVIÇO SOCIAL": {
        "Modalidade": "Bacharelado",
        "Faculdades": ["UAM", "UNP", "UNIFACS", "FADERGS", "IBMR", "UNIRITTER", "UNIFG", "UNISUL", "USJT", "UNISOCIESC", "UNA"],
        "disponibilidade": "disponível"
    },
    "SERVIÇOS JUDICIAIS": {
        "Modalidade": "Tecnólogo",
        "Faculdades": ["UAM", "UNP", "UNIFACS", "FADERGS", "IBMR", "UNIRITTER", "UNIFG", "UNISUL", "USJT", "UNISOCIESC", "UNA"],
        "disponibilidade": "disponível"
    },
    "SERVIÇOS NOTÁRIAIS E REGISTRAIS": {
        "Modalidade": "Tecnólogo",
        "Faculdades": ["UAM", "UNP", "UNIFACS", "FADERGS", "IBMR", "UNIRITTER", "UNIFG", "UNISUL", "USJT", "UNISOCIESC", "UNA"],
        "disponibilidade": "disponível"
    },
    "SERVIÇOS PENAIS": {
        "Modalidade": "Tecnólogo",
        "Faculdades": ["UAM", "UNP", "UNIFACS", "FADERGS", "IBMR", "UNIRITTER", "UNIFG", "UNISUL", "USJT", "UNISOCIESC", "UNA"],
        "disponibilidade": "disponível"
    },
    "SISTEMAS DE INFORMAÇÃO": {
        "Modalidade": "Bacharelado",
        "Faculdades": ["UAM", "UNP", "UNIFACS", "FADERGS", "IBMR", "UNIRITTER", "UNIFG", "UNISUL", "USJT", "UNISOCIESC", "UNA"],
        "disponibilidade": "disponível"
    },
    "SISTEMAS PARA INTERNET": {
        "Modalidade": "Tecnólogo",
        "Faculdades": ["UAM", "UNP", "UNIFACS", "FADERGS", "IBMR", "UNIRITTER", "UNIFG", "UNISUL", "USJT", "UNISOCIESC", "UNA"],
        "disponibilidade": "disponível"
    },
    "SOCIAL MEDIA": {
        "Modalidade": "Tecnólogo",
        "Faculdades": ["UAM", "UNIFG", "UNISUL", "USJT", "UNISOCIESC", "UNA"],
        "disponibilidade": "disponível"
    },
    "TURISMO": {
        "Modalidade": "Tecnólogo",
        "Faculdades": ["UAM", "UNP", "UNIFACS", "FADERGS", "IBMR", "UNIRITTER", "UNIFG", "UNISUL", "USJT", "UNISOCIESC", "UNA"],
        "disponibilidade": "disponível"
    },
    "FORMAÇÃO PEDAGÓGICA EM PEDAGOGIA": {
        "Modalidade": "Licenciatura",
        "Faculdades": ["UAM", "USJT"],
        "disponibilidade": "disponível"
    },
    "FORMAÇÃO PEDAGÓGICA EM HISTÓRIA": {
        "Modalidade": "Licenciatura",
        "Faculdades": ["UAM", "USJT"],
        "disponibilidade": "disponível"
    },
    "FORMAÇÃO PEDAGÓGICA EM FILOSOFIA": {
        "Modalidade": "Licenciatura",
        "Faculdades": ["UAM", "USJT"],
        "disponibilidade": "disponível"
    },
    "FORMAÇÃO PEDAGÓGICA EM LETRAS - PORTUGUÊS": {
        "Modalidade": "Licenciatura",
        "Faculdades": ["UAM", "USJT"],
        "disponibilidade": "disponível"
    },
    "FORMAÇÃO PEDAGÓGICA EM CIÊNCIAS SOCIAIS": {
        "Modalidade": "Licenciatura",
        "Faculdades": ["UAM", "USJT"],
        "disponibilidade": "disponível"
    }
}

def remover_girias(texto):
    # Substitui gírias comuns por uma versão mais neutra
    substituicoes = {
        r'\bmano\b': 'amigo',
        r'\blegal\b': 'bom',
        r'\bbagulho\b': 'coisa',
        r'\bto\b': 'estou',
        r'\btlgd\b': 'sabe',
        r'\bnunca\b': 'não',
         r'\adm\b': 'admnistração'
        # Adicione mais gírias conforme necessário
    }
    
    for giria, neutra in substituicoes.items():
        texto = re.sub(giria, neutra, texto, flags=re.IGNORECASE)
    
    return texto

    
def process_user_input(user_input, data):
    # Verifique se data é um dicionário
    if not isinstance(data, dict):
        print("Data não é um dicionário:", data)
        return "Erro no processamento, dados inválidos."

    # Lógica existente para processar a entrada do usuário
    for key, details in memoria_usuarios.items():
        # Verifique se a condição é atendida
        if details["condicao"](user_input if not data else data):
            # Lógica quando a condição é verdadeira
            resposta = details["resposta"]
            return resposta  # Retorne a resposta apropriada

    # Se nenhuma condição foi atendida, você pode retornar uma mensagem padrão
    return "Desculpe, não consegui entender sua solicitação."

def processar_conversa(user_input, from_number, prompt, cursos, contexto_usuarios):
    """
    Processa a conversa considerando o contexto do usuário, os cursos disponíveis e o prompt inicial.

    Args:
        user_input (str): Mensagem enviada pelo usuário.
        from_number (str): Número do telefone do usuário.
        prompt (str): Prompt inicial do sistema.
        cursos (dict): Dicionário de cursos disponíveis.
        contexto_usuarios (dict): Dicionário que armazena o contexto de cada usuário.


    Returns:
        str: Resposta gerada baseada no contexto.
    """
    
    # Remove gírias do input do usuário
    user_input = remover_girias(user_input)
    
    user_input_lower = user_input.strip().lower()
    
    if from_number not in contexto_usuarios:
        # Se não houver contexto, inicializa o histórico do usuário com o prompt
        contexto_usuarios[from_number] = [{'role': 'system', 'content': prompt}]
        
        # Adiciona a lista de cursos disponíveis ao contexto
        cursos_disponiveis = ", ".join(cursos.keys())
        cursos_info = f"Aqui estão os cursos disponíveis: {cursos_disponiveis}."
        contexto_usuarios[from_number].append({'role': 'system', 'content': cursos_info})
    
    # Adiciona a mensagem do usuário ao contexto
    contexto_usuarios[from_number].append({'role': 'user', 'content': user_input})
    
    
    # Prepara o histórico de mensagens para enviar à API da OpenAI
    mensagens = contexto_usuarios[from_number]

    try:
        # Chama a API do OpenAI para gerar a resposta
        resposta_IA = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=mensagens,
            max_tokens=1000,
            temperature=0.7
        )

        # Extrai a resposta gerada pelo modelo
        resposta = resposta_IA.choices[0].message.content

    except Exception as e:
        resposta = "Desculpe, ocorreu um erro ao gerar a resposta."
        print(f"Erro: {str(e)}")

    # Adiciona a resposta gerada ao contexto
    contexto_usuarios[from_number].append({'role': 'assistant', 'content': resposta})

    return resposta

# Função para lidar com mensagens recebidas via webhook
def handle_incoming_message(incoming_payload):
    # Variáveis para armazenar as mensagens concatenadas e o número de telefone
    mensagem_concatenada = ""
    from_number = None

    # Iterando sobre cada mensagem no payload
    for message in incoming_payload:
        message_text = message.get('message_text')
        from_number = message.get('phone_number')

        if message_text is None or from_number is None:
            # Se faltar alguma informação, continua para a próxima mensagem
            continue
        else:
            # Concatenar as mensagens enviadas em sequência
            if mensagem_concatenada:
                mensagem_concatenada += " " + message_text
            else:
                mensagem_concatenada = message_text

    # Após concatenar todas as mensagens, processa como uma só
    if mensagem_concatenada and from_number:

        # Processar a conversa com todas as mensagens concatenadas
        resposta = processar_conversa(mensagem_concatenada, from_number, prompts, cursos, contexto_usuarios)
        
        # Retornar apenas uma resposta concatenada
        return {
            "messages": [{
                "message_text": resposta,
                "phone_number": from_number
            }]
        }

    # Caso não haja nenhuma mensagem válida, retorna um erro
    return {
        "messages": [{
            "message_text": "Erro: Não foi possível processar a solicitação.",
            "phone_number": from_number
        }]
    }

# Endpoint para receber os dados do webhook
@app.route('/webhook', methods=['POST'])
def webhook():
    # Obtendo o JSON da requisição
    data = request.get_json()
    
    # Adicionando um log para verificar os dados recebidos
    print("Dados recebidos:", data)
    
    if data is None:
        print("Erro: Payload não recebido")
        return jsonify({'error': 'Payload não recebido'}), 400

    # Logando o tipo de conteúdo e o payload
    print("Tipo de conteúdo:", request.content_type)
    if request.content_type != 'application/json':
        return jsonify({'error': 'Tipo de conteúdo não suportado'}), 415

    # Tentando extrair mensagens da estrutura esperada
    messages = data.get('messages')
    
    # Se não encontrar a chave 'messages', tenta a outra estrutura
    if messages is None:
        from_number = data.get('from')
        message_text = data.get('message')
        if from_number and message_text:
            messages = [{'message_text': message_text, 'phone_number': from_number}]
        else:
            print("Erro: Estrutura do payload não reconhecida")
            return jsonify({'error': 'Estrutura do payload não reconhecida'}), 400

    # Verificando se a lista de mensagens não está vazia
    if not messages:
        return jsonify({'error': 'Mensagem não encontrada'}), 400

    # Chamando a função handle_incoming_message
    resposta = handle_incoming_message(messages)

    # Retornando a resposta no formato correto
    return jsonify(resposta), 200

# Rodar o app na porta 8080
if __name__ == '__main__':
    app.run(port=8080, host='0.0.0.0', debug=True, threaded=True)
