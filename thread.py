from os import getenv
from dotenv import load_dotenv
from google import genai

load_dotenv()
api_key = getenv('GEMINI_API_KEY','')
client = genai.Client(api_key=api_key)

with open('personalidade.txt', 'r') as persona:
    PERSONALIDADE = persona.read()

with open('periodico_verifica.txt', 'r') as instrucoes:
    INSTRUCAO = instrucoes.read()

def checar(texto):
    if 'x.com' in texto:
        resposta = client.models.generate_content(
        model="gemini-3.1-flash-lite",
        contents=f"{PERSONALIDADE}\n\n{INSTRUCAO}\nSe a resposta for um link, abra este link e analise se o que tem dentro lhe interessa. (Ignore esta linha se você não for capaz de abrir links)\n\nUsuário: {texto}"
    )    
    else:
        resposta = client.models.generate_content(
            model="gemma-4-31b-it",
            contents=f"{PERSONALIDADE}\n\n{INSTRUCAO}\n\nUsuário: {texto}"
        )
    if resposta.text.startswith('Y'):
        resposta_final = resposta.text[2:]
        print('Verdadeiro')
        return resposta_final
    else: 
        print('Falso.')
        return '456'