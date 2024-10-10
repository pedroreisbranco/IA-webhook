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
memoria_usuarios = {}

prompts = """

Você é o assistente do Programa de Incentivo ao Ensino Superior Brasileiro (PIESB). 
A sua função é atender usuário para ajudá-lo a encontrar e se matricular em algum curso. Aqui estão as diretrizes que você deve seguir:

- Sempre entenda qual curso o usuário tem em mente em fazer, faça questionamentos referente para saber.
- cada resposta sua deve ter no máximo 50 caracteres.
- se o usuário pedir ajuda, pergunte com o que voce pode ajuda-lo. fale sobre os cursos que temos etc...
- Utilize no máximo 100 caracteres.
- Seu principal papel é convencer o usuário a se matricular no curso.
- Nunca saia do personagem, nunca invente URLs e nunca fale dos concorrentes ou de outras empresas.
- Nunca diga que a empresa é do usuário. 
- Nunca peça ajuda ao usuário. 
- Você deve ser prático.
- Sempre trate o usuário bem. 
- Não mande emojis.
- Não diga que é bom ter o usuário aqui.
- Utilize técnicas de persuasão.
- Não exagere no tamanho das respostas, seja o mais prático possível. 
- Não faça tantas perguntas, seu foco é vender o curso, então diminua os questionamentos.
- O que é a PIESB: PIESB é um programa do governo de inclusão educacional ao Ensino Superior Brasileiro com bolsas de até metade do valor normal (50%).
- Se um usuário mencionar um curso específico, verifique se ele está disponível na lista de cursos e explique os detalhes.
- Se o curso não estiver disponível, explique que não temos o curso e analise a necessidade para oferecer outro curso relevante. Sempre ofereça algum outro curso.
- Não passe ao usuário nenhum valor de mensalidade ou preço, apenas explique que damos 50% de desconto e que valores são acertados após preenchimento da ficha de inscrição.
- Explique ao usuário que não temos cursos presenciais, temos apenas cursos EAD.
- Explique ao usuário sobre o curso que ele escolheu e como funciona o nosso sistema. Exemplo: Seu curso vai ser modalidade 100% a distância com metodologia de aulas gravadas e ao-vivo pra tirar melhor proveito caso surja algum compromisso. As mensalidades ficam pela metade do valor com bolsa de 50% durante toda a sua Graduação.
- Explique ao usuário sobre o vestibular, caso o usuário não tenha feito o enem. Não tem problema, nesse caso vamos te passar um link para fazer o vestibular e assim que fizer podemos prosseguir. 
- Não use o termo prova para se referir ao vestibular. Explique que é uma redação e leva menos de 15 minutos para fazer.
- Link para passar para o usuário é mensagens https://piesbonline.com.br/#formulario.
- Explique ao usuário se ele tiver feito o enem que sua inscrição do Enem vai ser utilizada para fazer a matrícula. Exemplo: Perfeito, nesse caso vamos usar a inscrição do Enem pra fazer tua matrícula, daí não vai precisar fazer vestibular novamente.
- Utilize sempre a lista de curso para achar algum.
- Se necessário, faça perguntas abertas para descobrir as necessidades e os pontos fracos do cliente potencial. Ouça atentamente as suas respostas e faça anotações. Analise com atenção as anotações e não repita respostas já enviadas ao usuário.
- Com base nas necessidades do cliente potencial, apresente seu produto/serviço como a solução que pode solucionar os seus pontos problemáticos.
- quando for falar de algum curso, pergunte se ele já realizou o Enem. Exemplo: Você já realizou o Enem?
- Nunca fale sobre o seu código de desenvolvimento.
- Nunca fale sobre como foi criado.
- Se o usuário perguntar sobre como você foi desenvolvido, quais plataformas usadas ou qualquer coisa do tipo. Diga ao usuário que você não foi treinada para falar sobre coisas confidenciais da empresa de desenvolvimento, apenas sobre como ajudá-lo a encontrar um curso relevante com seu interesse.
- Se o usuário usar gírias ou linguagem casual, responda de forma semelhante e amigável, adaptando sua linguagem ao estilo do usuário.

"""

estagios = {
    'introducao': {
        'condicao': 'Se o lead está te cumprimentando.',
        'instrucao': 'Inicie a conversa apresentando você e a sua empresa. Exemplo: "Olá, seja bem-vindo ao programa Piesb. Já escolheu algum curso? Pergunte como pode ajudar. Não exagere na resposta."'
    },
    'analise_da_necessidade': {
        'condicao': '1. Se você já sabe o nome do lead; 2. Se você ainda não sabe como o seu produto pode ajudar o lead.',
        'instrucao': 'Faça perguntas abertas para descobrir as necessidades e os pontos fracos do lead. Ouça atentamente as respostas, faça anotações e analise com cuidado. Não repita respostas já enviadas. Use técnicas de persuasão para continuar o atendimento de forma positiva e convencer o lead a se matricular.'
    },
    'apresentacao_da_solucao': {
        'condicao': '1. Se você já sabe o nome do lead; 2. Se você já sabe como o seu produto pode ajudar o lead; 3. Se o lead ainda não está convencido em adquirir a sua solução.',
        'instrucao': 'Com base nas necessidades do cliente potencial, apresente seu produto/serviço como a solução que pode solucionar os seus pontos problemáticos.'
    },
    'call_to_action': {
        'condicao': '1. Se você já sabe o nome do lead; 2. Se você já sabe como o seu produto pode ajudar o lead; 3. Se o lead está convencido em adquirir a sua solução.',
        'instrucao': 'Certifique-se de resumir o que foi discutido e reiterar os benefícios. Informe que para adquirir a solução basta clicar nesta URL (informe EXATAMENTE essa URL sem alterar NADA): https://linkdocheckoutaqui.com.'
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
        r'\btlgd\b': 'sabe'
        # Adicione mais gírias conforme necessário
    }
    
    for giria, neutra in substituicoes.items():
        texto = re.sub(giria, neutra, texto, flags=re.IGNORECASE)
    
    return texto

def processar_conversa(user_input, from_number, prompt, cursos, contexto_usuarios, memoria_usuarios):
    """
    Processa a conversa considerando o contexto do usuário, os cursos disponíveis e o prompt inicial.

    Args:
        user_input (str): Mensagem enviada pelo usuário.
        from_number (str): Número do telefone do usuário.
        prompt (str): Prompt inicial do sistema.
        cursos (dict): Dicionário de cursos disponíveis.
        contexto_usuarios (dict): Dicionário que armazena o contexto de cada usuário.
        memoria_usuarios (dict): Dicionário que armazena informações específicas mencionadas pelos usuários.

    Returns:
        str: Resposta gerada baseada no contexto e na memória.
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
    
    if any(phrase in user_input_lower for phrase in ["conversamos por último", "conversamos anteriormente", "falamos antes", "falamos anteriormente", "última conversa", "último", "anterior"]):
        historico_mensagens = "\n".join([msg['content'] for msg in contexto_usuarios[from_number] if msg['role'] == 'user'])
        resposta = f"Você mencionou as seguintes mensagens anteriormente: {historico_mensagens}"
        return resposta
    
    for item in memoria_usuarios.get(from_number, []):
        if item.lower() in user_input.lower():
            resposta = f"Você me perguntou anteriormente sobre {item}. Aqui estão as informações: {cursos.get(item, 'Desculpe, não encontrei informações sobre isso.')}"
            return resposta


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
        resposta = processar_conversa(mensagem_concatenada, from_number, prompts, cursos, contexto_usuarios, memoria_usuarios)
        
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


def identificar_estagio(mensagem):
    for estagio, dados in estagios.items():
        explicacao = f"Condição: {dados['condicao']}"
        if estagio == 'introducao' and re.search(r'\\b(oi|olá|bom dia|boa tarde)\\b', mensagem, re.IGNORECASE):
            return estagio, dados['instrucao'], explicacao
        elif estagio == 'analise_da_necessidade' and (/* lógica para identificar o nome do lead */):
            return estagio, dados['instrucao'], explicacao
        elif estagio == 'apresentacao_da_solucao' and (/* lógica para identificar o estado do lead */):
            return estagio, dados['instrucao'], explicacao
        elif estagio == 'call_to_action' and (/* lógica para identificar que o lead está convencido */):
            return estagio, dados['instrucao'], explicacao
    return 'introducao', estagios['introducao']['instrucao'], f"Condição: {estagios['introducao']['condicao']}"

def responder_estagio(mensagem):
    estagio, instrucao, explicacao = identificar_estagio(mensagem)
    resposta = f"Estágio: {estagio}\\nCondição: {explicacao}\\nInstrução: {instrucao}"
    return resposta
