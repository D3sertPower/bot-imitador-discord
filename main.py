import discord
import json
import datetime
import asyncio  # IMPORTANTE: Adicionado para rodar a checagem em background
from random import choice, randint
from discord.ext import commands
from google.genai import types
from google.genai.errors import ClientError
from google import genai
from os import getenv
from dotenv import load_dotenv
from thread import checar

load_dotenv()

api_key = getenv('GEMINI_API_KEY','')
contador = 0
discord_token = getenv('DISCORD_TOKEN','')
tokens_por_resposta = int(getenv('MAX_TOKENS',''))

# Variáveis de controle de erro (Rate Limit) inicializadas corretamente
tempo_atual = None
tempo_anterior = None

client = genai.Client(api_key=api_key)

# --- CORREÇÃO AQUI: Adicionado encoding="utf-8" para evitar o "nÃ£o" ---
with open('personalidade.txt', 'r', encoding='utf-8') as persona:
    PERSONALIDADE = persona.read()

with open("imagens.json", "r", encoding="utf-8") as json_file:
    imagens = json.load(json_file) # fiz essa porra sem vibe code tá, chupa max!!!

with open("dialogos.json", "r", encoding="utf-8") as json_arq:
    dialogos = json.load(json_arq)

models = ['gemini-3.1-flash-lite','gemini-3.5-flash','gemini-3-flash-preview','gemma-31b-it']
model = 'gemini-3.1-flash-lite'

def perguntar(texto):
    global tokens_por_resposta
    resposta = client.models.generate_content(
        model=f"{model}",
        contents=f"{PERSONALIDADE}\n\nUsuário: {texto}",
        config=types.GenerateContentConfig(
            maxOutputTokens=tokens_por_resposta
        )
    )
    if resposta.candidates[0].finish_reason=="MAX_TOKENS":
        tokens_por_resposta += 100
        respostas = ['mds cara', 'vá se lascar', 'vai se foder', 'cala boca', 'xiu', '?', '???']
        return (choice(respostas))
    if '123' in resposta.text:
        return ('https://tenor.com/view/net-epstein-gif-7773007491111019523')
    else:
        return (resposta.text)
    
intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print(f"Logado como {bot.user}")

@bot.event
async def on_message(message):
    # Correção nas globais para evitar erros em runtime
    global PERSONALIDADE, client, model, tempo_atual, tempo_anterior

    if message.author.bot:
        return
        
    if "tenor.com" in message.content or ".gif?ex" in message.content or ".png?ex" in message.content:
        id = randint(1,100000000)
        imagens[f"{id}"] = str(message.content)
        salvarImagens()
        
    if message.attachments:
        for attachment in message.attachments:
            if attachment.content_type and attachment.content_type.startswith('image/'):
                id = randint(1,100000000)
                await attachment.save(f"{id}.png")
                imagens[f"{id}"] = f"{id}.png"
                salvarImagens()

    # --- BLOCO ONDE O BOT NÃO É MENCIONADO ---
    if bot.user not in message.mentions and not message.attachments:
        
        # 1. Roda a função checar() em background enviando a mensagem atual
        chance = randint(1,6)
        if chance >= 4:
            print('Rufem os tambores.')
            resultado_da_checagem = await asyncio.to_thread(checar, message.content)
        # 2. Se retornar o texto começado com Y, responde e para a execução aqui
            if '456' not in resultado_da_checagem:
                await message.reply(resultado_da_checagem)
                return
                
        # Se a checagem deu False, o bot segue o seu fluxo original de chances:
        chance = randint(1,40)
        if chance >= 35 and chance != 40:
            imagem_sorteada = choice(list(imagens.values()))
            if ".png" in imagem_sorteada:
                await message.reply(file=discord.File(imagem_sorteada))
            else: 
                await message.reply(imagem_sorteada)
            return 
            
        if chance == 40 or chance == 1:
            dialogo_sorteado = choice(list(dialogos.values()))
            await message.reply(dialogo_sorteado)
            return

    if bot.user in message.mentions:
        # Remove a menção do bot
        texto = (
            message.content
            .replace(f"<@{bot.user.id}>", "")
            .replace(f"<@!{bot.user.id}>", "")
            .strip()
        )
        if "mude sua personalidade" in texto and message.author.guild_permissions.administrator:
            ajustado = (
                texto
                .replace("mude sua personalidade", "")
                .strip()
            )
            PERSONALIDADE = PERSONALIDADE + "\n" + "- " + ajustado
            # --- CORREÇÃO AQUI: Salvando a nova personalidade em UTF-8 ---
            with open('personalidade.txt', 'w', encoding='utf-8') as persona:
                persona.write(PERSONALIDADE)
            print("Nova personalidade salva:")
            print(PERSONALIDADE)
            await message.reply("Personalidade updated, BossMan!")
            return
            
        try:
            resposta = perguntar(texto)
            await message.reply(resposta)
            return
        except ClientError as e:
            print("Erro ao gerar resposta:", e)
            try:
                if "RATE_LIMIT_EXCEEDED" in str(e):
                    if tempo_atual:
                        tempo_anterior = tempo_atual
                    tempo_atual = (datetime.datetime.now()).timestamp() # Correção do datetime
                    
                    if not tempo_anterior or (tempo_atual - tempo_anterior < 60): 
                        model_anterior = model
                        model = models[3]
                        resposta = perguntar(texto)
                        model = model_anterior
                    else:
                        models.remove(model)
                        model = models[0]
                        resposta = perguntar(texto)
                await message.reply(resposta)
            except Exception as e_nova:
                print(e_nova)
                await message.reply('to na faculdade cara dps eu respondo')
                
    id = randint(1,9999999)
    if message.content != '' and 'gif' not in message.content and 'https' not in message.content:
        dialogos[f"{id}"] = message.content
        salvarDialogo()
    await bot.process_commands(message)

def salvarImagens():
    with open("imagens.json", "w", encoding="utf-8") as json_file:
        json.dump(imagens, json_file, indent=4)
        
def salvarDialogo():
    with open("dialogos.json", "w", encoding="utf-8") as json_arq:
        json.dump(dialogos, json_arq, indent=4)
        
bot.run(discord_token)