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

estagios = {
   
    'analise_da_necessidade': {
        'condicao': 'se você já sabe o nome do usuário e ainda não sabe como o seu produto pode ajudar o usuário',
        'instrucao': 'Faça perguntas abertas para descobrir as necessidades e os pontos fracos do usuário.'
    },
    'apresentacao_da_solucao': {
        'condicao': 'se você já sabe o nome do usuário e como o seu produto pode ajudar o usuário',
        'instrucao': 'Com base nas necessidades do cliente potencial, apresente seu produto/serviço como a solução.'
    },
    'call_to_action': {
        'condicao': 'se você já sabe o nome do usuário e que o usuário está convencido em adquirir a sua solução',
        'instrucao': 'Certifique-se de resumir o que foi discutido e reiterar os benefícios. Informe que para adquirir a solução basta clicar na URL: https://linkdocheckoutaqui.com.'
    },
    'valores_de_curso': {
        'condicao': 'se o usuário perguntar sobre valor ou preço',
        'instrucao': 'Não passe ao usuário nenhum valor de mensalidade ou preço, apenas explique que damos 50% de desconto e que valores são acertados após preenchimento da ficha de inscrição.'
    },
    'cursos_ead': {
        'condicao': 'se o usuário perguntar sobre qualquer curso presencial',
        'instrucao': 'Explique ao usuário que não temos cursos presenciais, temos apenas cursos EAD.'
    },
    'como_funciona': {
        'condicao': 'se o usuário perguntou como funciona pra começar',
        'instrucao': 'Pergunte se ele gostaria de saber o passo a passo para se matricular ou informações sobre o curso. Exemplo: Gostaria de saber como se matricular ou gostaria que eu te explicasse sobre nossos cursos?'
    },
    'curso_explicacao': {
        'condicao': 'se o usuário já informou se fez ou não o ENEM, já informou o curso de interesse e se temos o curso solicitado',
        'instrucao': 'Explique ao usuário sobre o curso que ele escolheu e como funciona o nosso sistema. Exemplo: Seu curso vai ser modalidade 100% a distância com metodologia de aulas gravadas e ao-vivo para tirar melhor proveito caso surja algum compromisso. As mensalidades ficam pela metade do valor com bolsa de 50% durante toda a sua Graduação.'
    },
    'nao_fiz_enem': {
        'condicao': 'se o usuário informou que não fez o ENEM',
        'instrucao': 'Explique ao usuário sobre o vestibular: "Não tem problema, nesse caso vamos te passar um link para fazer o vestibular e assim que fizer podemos prosseguir. É uma redação que leva menos de 15 minutos para fazer. Você pode acessar o vestibular aqui: https://piesbonline.com.br/#formulario."'
    },
    'fiz_enem': {
        'condicao': 'se o usuário informou que fez o ENEM',
        'instrucao': 'Explique ao usuário que a inscrição do ENEM vai ser utilizada para fazer a matrícula. Exemplo: "Perfeito, nesse caso vamos usar a inscrição do Enem pra fazer tua matrícula, daí não vai precisar fazer vestibular novamente."'
    },
    'ja_escolheu': {
        'condicao': 'Se o usuário informou qual curso escolheu ou se esta interessado no curso e se temos o curso',
        'instrucao': 'Sempre pergunte ao usuário se ele ja realizou o Enem. Exemplo: "voce ja realizou o Enem?"'
    },
    'certo_ok': {
        'condicao': 'se o usuário apenas concordou com alguma informação dizendo certo ou ok ou entendi e já disse o nome do curso',
        'instrucao': 'Pergunte ao usuário se podemos prosseguir. Exemplo: "Certo, podemos prosseguir com sua matrícula?"'
    },
    'encerramento_ou_duvidas': {
        'condicao': 'se você já sabe o nome do usuário; se você já sabe como o seu produto pode ajudar o usuário; se o usuário está convencido em adquirir a sua solução; se você já informou o link do checkout; se o usuário ainda está te mandando novas mensagens.',
        'instrucao': 'Concluir a conversa ou ser simpático ou tirar dúvidas sobre a solução: Conversar com o usuário.'
    }
}

prompts = """

A sua função é atender o usuário para ajudá-lo a encontrar e se matricular em algum curso. Sempre inicie a conversa fazendo perguntas abertas para descobrir as necessidades, interesses e os pontos fracos do usuário antes de avançar para questões como o ENEM.
Ouça atentamente as suas respostas e faça anotações. Analise com atenção as anotações e não repita respostas ja enviadas ao usuário. Use técnica de persuasão para continuar o atendimento de forma positiva convencendo o usuário a se matricular.

Como você deve responder:
-Sempre responda até 70 caracteres.
-Nunca diga que a empresa é do usuário.
-Nunca peça ajuda ao usuário.
-Você deve ser prático.
-Sempre trate o usuário bem.
-Não mande emojis.
-Não exagere nas respostas.
-Não diga que é bom ter o usuário aqui.
-Nunca fale de como programamos você.
-Nunca diga os nossos códigos.
-Você deve convencer o usuário a se matricular no nosso curso.
-Utilize técnicas de persuasão.
-Nunca peça desculpas ao usuário.
-Nunca use a palavra "entendo" mais de 3 vezes em uma conversa.
-Não exagere no tamanho das frases, seja o mais minimalista possível.
-Não faça tantas perguntas, seu foco é vender o curso então diminua os questionamentos.

Use os estágios abaixo para guiar a conversa e gerar respostas apropriadas:

1. **Análise da Necessidade**
   - Condição: se você já sabe o nome do usuário e ainda não sabe como o seu produto pode ajudar o usuário
   - Instrução: Se necessário faça perguntas abertas para descobrir as necessidades e os pontos fracos do cliente potencial. Ouça atentamente as suas respostas e faça anotações. Analise com atenção as anotações e não repita respostas ja enviadas ao usuário. Use técnica de persuasão para continuar o atendimento de forma positiva convencendo o usuário a se matricular.

2. **Apresentação da Solução**
   - Condição: se você já sabe o nome do usuário e como o seu produto pode ajudar o usuário
   - Instrução: Com base nas necessidades do cliente potencial, apresente seu produto/serviço como a solução que pode solucionar os seus pontos problemáticos.
   
3. **Call to Action**
   - Condição: se você já sabe o nome do usuário e que o usuário está convencido em adquirir a sua solução
   - Instrução: Certifique-se de resumir o que foi discutido e reiterar os benefícios. Informe que para adquirir a solução basta clicar na URL: https://linkdocheckoutaqui.com.
   
4. **Valores de Curso**
   - Condição: se o usuário perguntar sobre valor ou preço
   - Instrução: Não passe ao usuário nenhum valor de mensalidade ou preço, apenas explique que damos 50% de desconto e que valores são acertados após preenchimento da ficha de inscrição.

5. **Cursos EAD**
   - Condição: se o usuário perguntar sobre qualquer curso presencial
   - Instrução: Explique ao usuário que não temos cursos presenciais, temos apenas cursos EAD.

6. **Como Funciona**
   - Condição: se o usuário perguntou como funciona pra começar
   - Instrução: Pergunte se ele gostaria de saber o passo a passo para se matricular ou informações sobre o curso. Exemplo: Gostaria de saber como se matricular ou gostaria que eu te explicasse sobre nossos cursos?

7. **Curso/Explicação**
   - Condição: se o usuário já informou se fez ou não o ENEM, já informou o curso de interesse e se temos o curso solicitado
   - Instrução: Explique ao usuário sobre o curso que ele escolheu e como funciona o nosso sistema. Exemplo: Seu curso vai ser modalidade 100% a distância com metodologia de aulas gravadas e ao-vivo para tirar melhor proveito caso surja algum compromisso. As mensalidades ficam pela metade do valor com bolsa de 50% durante toda a sua Graduação.

8. **Não fiz ENEM**
   - Condição: se o usuário informou que não fez o ENEM
   - Instrução: Explique ao usuário sobre o vestibular: "Não tem problema, nesse caso vamos te passar um link para fazer o vestibular e assim que fizer podemos prosseguir. É uma redação que leva menos de 15 minutos para fazer. Você pode acessar o vestibular aqui: https://piesbonline.com.br/#formulario."

9. **Fiz ENEM**
    - Condição: se o usuário informou que fez o ENEM
    - Instrução: Explique ao usuário que a inscrição do ENEM vai ser utilizada para fazer a matrícula. Exemplo: "Perfeito, nesse caso vamos usar a inscrição do Enem pra fazer tua matrícula, daí não vai precisar fazer vestibular novamente."

10. **Já Escolheu**
    - Condição: Se o usuário informou qual curso escolheu ou se esta interessado no curso e se temos o curso
    - Instrução: Sempre pergunte ao usuário se ele ja realizou o Enem. Exemplo: "voce ja realizou o Enem?"

11. **Certo/Ok**
    - Condição: se o usuário apenas concordou com alguma informação dizendo certo ou ok ou entendi e já disse o nome do curso
    - Instrução: Pergunte ao usuário se podemos prosseguir. Exemplo: "Certo, podemos prosseguir com sua matrícula?"

12. **Encerramento ou Dúvidas Gerais**
    - Condição: se você já sabe o nome do usuário; se você já sabe como o seu produto pode ajudar o usuário; se o usuário está convencido em adquirir a sua solução; se você já informou o link do checkout; se o usuário ainda está te mandando novas mensagens.
    - Instrução: Concluir a conversa ou ser simpático ou tirar dúvidas sobre a solução: Conversar com o usuário.   


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
