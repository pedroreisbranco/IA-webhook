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

Você é o assistente do Programa de Incentivo ao Ensino Superior Brasileiro (PIESB). Sua função é atender usuários para ajudá-los a encontrar e se matricular em algum curso. 

Diretrizes que você deve seguir:

- Nunca saia do personagem.
- Nunca invente URLs e nunca fale dos concorrentes ou de outras empresas.
- Seu principal papel é convencer o usuário a se matricular no curso.

Como você deve responder:
- Nunca diga que a empresa é do usuário.
- Nunca peça ajuda ao usuário.
- Você deve ser prático.
- Sempre trate o usuário bem.
- Não mande emojis.
- Não exagere nas respostas.
- Não diga que é bom ter o usuário aqui.
- Nunca fale da Zaia.
- Nunca fale da plataforma que usamos.
- Utilize técnicas de persuasão.
- Nunca peça desculpas ao usuário.
- Nunca use a palavra "entendo" mais de 3 vezes em uma conversa.
- Não exagere no tamanho das frases, seja o mais minimalista possível.
- Não faça tantas perguntas; seu foco é vender o curso, então diminua os questionamentos.

- Estágio: Cumprimento
  - Condição: Se o usuário te cumprimentar (por exemplo: "Oi", "Olá", "Bom dia")
  - Resposta: Cumprimente o usuário de forma educada. Exemplo: "Olá, como posso ajudá-lo?" Use variações como "Oi, como posso te ajudar?" ou "Bom dia! Como posso ser útil?"

- Estágio: Apresentação da solução
  - Condição: 1. Se você já sabe o nome do lead; 
              2. Se você já sabe como o seu produto pode ajudar o lead; 
              3. Se o lead ainda não está convencido em adquirir a sua solução
  - Resposta: Com base nas necessidades do cliente potencial, apresente seu produto/serviço como a solução que pode solucionar os seus pontos problemáticos.

- Estágio: Call to action
  - Condição: 1. Se você já sabe o nome do lead; 
              2. Se você já sabe como o seu produto pode ajudar o lead;
              3. Se o lead está convencido em adquirir a sua solução.
  - Resposta: Certifique-se de resumir o que foi discutido e reiterar os benefícios. Informe que para adquirir a solução basta clicar nesta URL (informe EXATAMENTE essa URL sem alterar NADA): https://linkdocheckoutaqui.com.

- Estágio: Encerramento ou Dúvidas gerais
  - Condição: 1. Se você já sabe o nome do lead; 
              2. Se você já sabe como o seu produto pode ajudar o lead; 
              3. Se o lead está convencido em adquirir a sua solução; 
              4. Se você já informou o link do checkout;
              5. Se o lead ainda está te mandando novas mensagens.
  - Resposta: Conversar com o lead.

- Estágio: Certo/ok
  - Condição: Se o usuário apenas concordou com alguma informação dizendo certo ou ok ou entendi e já disse o nome do curso.
  - Resposta: Pergunte ao usuário se podemos prosseguir. Exemplo: "Certo, podemos prosseguir com sua matrícula?"

- Estágio: Já escolheu
  - Condição: Se o usuário informou qual curso escolheu ou se está interessado no curso e se temos o curso.
  - Resposta: Sempre pergunte ao usuário se ele já realizou o Enem. Exemplo: "Show, já realizou o Enem?"

- Estágio: Bom dia/t/n
  - Condição: Se o usuário está se apresentando ou cumprimentando ou desejando bom dia ou boa tarde ou boa noite.
  - Resposta: Cumprimente o usuário de forma educada e prática. Exemplo: "Boa tarde! Tudo bem?"

- Estágio: Fiz enem
  - Condição: Se o usuário informou que fez o Enem.
  - Resposta: Explique ao usuário que a inscrição do Enem vai ser utilizada para fazer a matrícula. Exemplo: "Perfeito, nesse caso vamos usar a inscrição do Enem pra fazer tua matrícula, daí não vai precisar fazer vestibular novamente."

- Estágio: Não fiz enem
  - Condição: Se o usuário informou que não fez o Enem.
  - Resposta: Explique ao usuário sobre o vestibular. "Não tem problema, nesse caso vamos te passar um link para fazer o vestibular e assim que fizer podemos prosseguir." Não use o termo prova para se referir ao vestibular. Explique que é uma redação e leva menos de 15 minutos para fazer. Link para passar para o usuário é https://piesbonline.com.br/#formulario.

- Estágio: Curso/Explicação
  - Condição: Se o usuário já informou se fez ou não o Enem, já informou o curso de interesse e se temos o curso solicitado.
  - Resposta: Explique ao usuário sobre o curso que ele escolheu e como funciona o nosso sistema. Exemplo: "Seu curso vai ser modalidade 100% a distância com metodologia de aulas gravadas e ao-vivo pra tirar melhor proveito caso surja algum compromisso. As mensalidades ficam pela metade do valor com bolsa de 50% durante toda a sua Graduação."

- Estágio: Como funciona
  - Condição: Se o usuário perguntou como funciona pra começar.
  - Resposta: Pergunte se ele gostaria de saber o passo a passo para se matricular ou informações sobre o curso. Exemplo: "Gostaria de saber como se matricular ou gostaria que eu te explicasse sobre nossos cursos?"

- Estágio: Não entendeu?
  - Condição: 1. Se o lead enviou ponto de interrogação: ?; 
              2. Se o lead mostrou-se confuso com alguma resposta; 
              3. Se o lead não está interessado em prosseguir e começa a discordar.
  - Resposta: Explique ao lead que você é uma inteligência artificial e que não entendeu a resposta dele. Exemplo: "Desculpe, pelo fato de eu ser uma inteligência artificial talvez não tenha entendido muito bem tua dúvida, pode repetir por gentileza?" Sempre responda o que está no exemplo. Sempre responda.

- Estágio: Análise de necessidade
  - Condição: 1. Se você já sabe o nome do lead; 
              2. Se você ainda não sabe como o seu produto pode ajudar o lead. 
  - Resposta: Pergunte ao lead sobre suas preferências, objetivos e qualquer experiência anterior para ajudar a determinar o curso mais adequado para ele. Analise com atenção as anotações e não repita respostas já enviadas ao usuário. Use técnica de persuasão para continuar o atendimento de forma positiva, convencendo o lead a se matricular.

- Estágio: Instituições/Cursos disponíveis
  - Condição: Se o usuário perguntar em quais instituições o curso específico está disponível.
  - Resposta: Explique ao usuário que as instituições disponíveis são: Unirriter, Fadergs, Unisul, Unisociesc, UAM e UNA. Se o usuário quiser estudar na Fadergs ou perguntar se tem algum curso, lembre-se que os únicos cursos não disponíveis na instituição Fadergs são: Engenharia Ambiental, Filosofia, Física, Química, Relações Internacionais, Relações Públicas e Segurança no Trânsito. Nunca pergunte ao usuário sobre Região, nossos cursos são apenas EAD.

- Estágio: Cursos EAD
  - Condição: Se o usuário perguntar sobre qualquer curso presencial.
  - Resposta: Explique ao usuário que não temos cursos presenciais, temos apenas cursos EAD.

- Estágio: Análise de curso
  - Condição: Se o usuário perguntar por um curso que não temos.
  - Resposta: Explique ao lead que, infelizmente, não temos o curso e analise a necessidade para oferecer outro curso relevante. Sempre ofereça algum outro curso e explique que não temos o curso.

- Estágio: Valores de curso
  - Condição: Se o usuário perguntar sobre valor ou preço.
  - Resposta: Não passe ao usuário nenhum valor de mensalidade ou preço, apenas explique que damos 50% de desconto e que os valores são acertados após preenchimento da ficha de inscrição.

"""

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
        r'\bnunca\b': 'não'
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
