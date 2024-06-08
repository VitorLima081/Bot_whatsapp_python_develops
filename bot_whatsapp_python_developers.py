import telebot
import requests
import logging
from flask import Flask, request, jsonify
from openai import OpenAI
from pathlib import Path
import sqlite3
import mercadopago
import uuid
import datetime
from datetime import timedelta
import warnings
import os
import boto3
import time

#INICIANDO O FLASK
app = Flask(__name__)
#INICIANDO O CLIENTE OPENAI
client = OpenAI(api_key='sk-proj-rwFVgr8b4MGaUfIafAJXT3BlbkFJmQABTwBnjBTupTC5MzcB')

#VARIAVEIS DE CONFIGURAÇÕES
CHAVE_TELEGRAM = '7143724464:AAEADk8anTLcBQ0A8T4xslIOD9hOSWTKyFs'
BOT = telebot.TeleBot(CHAVE_TELEGRAM)
ACCESS_TOKEN="EAAXPj6OzA3oBO5uuKcy7sWnQiKZAO8SFSfyRelNQPeC9RLqtlytM06dzS35SZAXplJMXrViA8ozQxX7L80q7jdZCgl74c370Q7kubURB5ZBBA9bPo0MSP52Tz3et6RVHSJLndBme903UykXGDYXptyzkD8AMrR7W240OeaktfxuEKx8UleC3hdROIu3BVTr2XCvoRkfOWYBIkT6a"
APP_ID="1635590717244282"
APP_SECRET="ac481f183cf46f41e374378b70193277"
RECIPIENT_WAID="+5581995447857" 
VERSION="v19.0"
PHONE_NUMBER_ID="239278652611341"
VERIFY_TOKEN="VITORXAMA"
ocupado = False

#INICIANDO ROTA PARA RECEBER AS MENSAGENS COM O NGROK:
#ngrok http 8000 --domain oryx-romantic-condor.ngrok-free.app

try:

    @app.route('/', methods=['GET', 'POST'])
    def handle_request():
        if request.method == 'GET':
            hub_challenge = request.args.get('hub.challenge', '')
            logging.info("Received hub.challenge: %s", hub_challenge)
            return hub_challenge, 200
        elif request.method == 'POST':
            logging.info("Received POST request from Facebook")
            data = request.json
            print(data)
            for entry in data.get('entry', []):
                for change in entry.get('changes', []):
                    value = change.get('value', {})
                    contacts = value.get('contacts', [])
                    messages = value.get('messages', [])
                    for contact in contacts:
                        numero_retorno = contact.get('wa_id')
                        for message in messages:
                            mensagem_recebida = message.get('text', {}).get('body')
                            mensagem_audio = message.get('type')
                            if mensagem_audio == 'audio':
                                id_audio = message.get('audio', {}).get('id')
                                tratando_audio(numero_retorno, mensagem_audio, id_audio)
                            elif '/' in mensagem_recebida.lower():
                                quantidade_caracters = len(mensagem_recebida)
                                salvando_clientes(numero_retorno, 'gerar_audio', 0.05 * quantidade_caracters, mensagem_recebida)
                                gerando_pagamento(numero_retorno)  
                            elif '@' in mensagem_recebida.lower():
                                salvando_clientes(numero_retorno, 'gerar_imagem', 3, mensagem_recebida)
                                gerando_pagamento(numero_retorno)      
                            else: 
                                mensagem_convertida = mensagem_recebida.lower()   
                                recebendo_mensagem(numero_retorno, mensagem_convertida, mensagem_audio)
                        
        
            return jsonify({'message': 'Recebido com sucesso'}), 200

    #ENVIANDO IMAGEM COMPRADA:
    def enviando_imagem(numero_retorno):
        nova_conn = sqlite3.connect('usuarios_ia.db')
        novo_cursor = nova_conn.cursor()

        novo_cursor.execute('SELECT link_imagem FROM clientes WHERE chat_id = ?', (numero_retorno,))
        imagem_gerada = novo_cursor.fetchone()

        if imagem_gerada is None:
            texto_sem_imagem = '🚨 🤖💬*NÃO EXISTE* solicitação para geração de arte pendente em seu cadastro, solicite o pagamento novamente! 🚨'
            url = f'https://graph.facebook.com/v19.0/{PHONE_NUMBER_ID}/messages'
            headers = {
                'Authorization': f'Bearer {ACCESS_TOKEN}',
                'Content-Type': 'application/json'
            }
            payload = {
                "messaging_product": "whatsapp",
                "recipient_type": "individual",
                "to": numero_retorno,
                "type": "text",
                "text": {"preview_url": False, "body":texto_sem_imagem},
                
            }

            response = requests.post(url, headers=headers, json=payload)
            if response.status_code == 200:
                print("Mensagem enviada com sucesso!")
            else:
                print("Erro ao enviar a mensagem:", response.text) 

            
        else:
            url = f'https://graph.facebook.com/v19.0/{PHONE_NUMBER_ID}/messages'
            headers = {
            'Authorization': f'Bearer {ACCESS_TOKEN}',
            'Content-Type': 'application/json'
            }
            payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": numero_retorno,
            "type": "text",
            "text": {"preview_url": False, "body": '🤖💬 Obrigado(a) pela compra, espero que goste! ⬇️'},

            }

            response = requests.post(url, headers=headers, json=payload)

            time.sleep(2)
            
            url = f'https://graph.facebook.com/v19.0/{PHONE_NUMBER_ID}/messages'
            headers = {
            'Authorization': f'Bearer {ACCESS_TOKEN}',
            'Content-Type': 'application/json'
            }
            payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": numero_retorno,
            "type": "image",
            "image": {
                "link": imagem_gerada[0]},
            }
            response = requests.post(url, headers=headers, json=payload)
            if response.status_code == 200:
                print("Mensagem enviada com sucesso!")
            else:
                print("Erro ao enviar a mensagem:", response.text)
            
            conn = sqlite3.connect('usuarios_ia.db')
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM clientes WHERE chat_id = ?', (numero_retorno,))
            resultado = cursor.fetchone()
            if resultado:
                cursor.execute('DELETE FROM clientes WHERE chat_id = ?', (numero_retorno,))
                conn.commit()  

    #ENVIANDO AUDIO COMPRADO:
    def enviando_audio(numero_retorno):
        nova_conn = sqlite3.connect('usuarios_ia.db')
        novo_cursor = nova_conn.cursor()

        novo_cursor.execute('SELECT link_imagem FROM clientes WHERE chat_id = ?', (numero_retorno,))
        imagem_gerada = novo_cursor.fetchone()

        if imagem_gerada is None:
            texto_sem_imagem = '🚨 🤖💬*NÃO EXISTE* solicitação para geração de arte pendente em seu cadastro, solicite o pagamento novamente! 🚨'
            url = f'https://graph.facebook.com/v19.0/{PHONE_NUMBER_ID}/messages'
            headers = {
                'Authorization': f'Bearer {ACCESS_TOKEN}',
                'Content-Type': 'application/json'
            }
            payload = {
                "messaging_product": "whatsapp",
                "recipient_type": "individual",
                "to": numero_retorno,
                "type": "text",
                "text": {"preview_url": False, "body":texto_sem_imagem},
                
            }

            response = requests.post(url, headers=headers, json=payload)
            if response.status_code == 200:
                print("Mensagem enviada com sucesso!")
            else:
                print("Erro ao enviar a mensagem:", response.text) 

            
        else:
            url = f'https://graph.facebook.com/v19.0/{PHONE_NUMBER_ID}/messages'
            headers = {
            'Authorization': f'Bearer {ACCESS_TOKEN}',
            'Content-Type': 'application/json'
            }
            payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": numero_retorno,
            "type": "text",
            "text": {"preview_url": False, "body": '🤖💬 Obrigado(a) pela compra, espero que goste! ⬇️'},

            }

            response = requests.post(url, headers=headers, json=payload)

            time.sleep(2)
            
            url = f'https://graph.facebook.com/v19.0/{PHONE_NUMBER_ID}/messages'
            headers = {
            'Authorization': f'Bearer {ACCESS_TOKEN}',
            'Content-Type': 'application/json'
            }
            payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": numero_retorno,
            "type": "audio",
            "audio": {
                "id": imagem_gerada[0]},
            }
            response = requests.post(url, headers=headers, json=payload)
            
            if response.status_code == 200:
                print("Mensagem enviada com sucesso!")
            else:
                print("Erro ao enviar a mensagem:", response.text)
            
            conn = sqlite3.connect('usuarios_ia.db')
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM clientes WHERE chat_id = ?', (numero_retorno,))
            resultado = cursor.fetchone()
            if resultado:
                cursor.execute('DELETE FROM clientes WHERE chat_id = ?', (numero_retorno,))
                conn.commit()  
    
    #VERIFICANDO PIX/ENVIANDO CONTEUDO:
    def verificando_pix(numero_retorno):
        global ocupado
            
        nova_conn = sqlite3.connect('usuarios_ia.db')
        novo_cursor = nova_conn.cursor()

        novo_cursor.execute('SELECT identificacao_pix FROM clientes WHERE chat_id = ?', (numero_retorno,))
        resultado = novo_cursor.fetchone()

        if resultado is None:
            texto_nao_pix = '🚨 Não existe SOLICITAÇÃO DE COMPRA pendente em seu cadastro, solicite o pagamento novamente! 🚨'
            url = f'https://graph.facebook.com/v19.0/{PHONE_NUMBER_ID}/messages'
            headers = {
                'Authorization': f'Bearer {ACCESS_TOKEN}',
                'Content-Type': 'application/json'
            }
            payload = {
                "messaging_product": "whatsapp",
                "recipient_type": "individual",
                "to": numero_retorno,
                "type": "text",
                "text": {"preview_url": False, "body": texto_nao_pix},
                
            }

            response = requests.post(url, headers=headers, json=payload)
            if response.status_code == 200:
                print("Mensagem enviada com sucesso!")
            else:
                print("Erro ao enviar a mensagem:", response.text) 

            
        else:
            identificacao_pix_usuario = resultado[0]
            sdk = mercadopago.SDK('APP_USR-2347718972172566-042400-1d79f871db74ab55505906e87707e5f7-26122567')
            payment_info = sdk.payment().get(identificacao_pix_usuario)
            status = payment_info['response']['status']
            valor_compra = payment_info['response']['transaction_amount']
            data = datetime.datetime.now()
            data_atual = data.date()
            
            if status == 'pending':
                texto_pendente = '🚨 Ainda não identificamos o pagamento!\n 👀 Caso tenha efetuado o pagamento envie *PAGO*'
                url = f'https://graph.facebook.com/v19.0/{PHONE_NUMBER_ID}/messages'
                headers = {
                    'Authorization': f'Bearer {ACCESS_TOKEN}',
                    'Content-Type': 'application/json'
                }
                payload = {
                    "messaging_product": "whatsapp",
                    "recipient_type": "individual",
                    "to": numero_retorno,
                    "type": "text",
                    "text": {"preview_url": False, "body": texto_pendente},
                    
                }

                response = requests.post(url, headers=headers, json=payload)
                if response.status_code == 200:
                    print("Mensagem enviada com sucesso!")
                else:
                    print("Erro ao enviar a mensagem:", response.text) 
            else:
                
                texto_pago = '✅ Pagamento aprovado!'
                url = f'https://graph.facebook.com/v19.0/{PHONE_NUMBER_ID}/messages'
                headers = {
                    'Authorization': f'Bearer {ACCESS_TOKEN}',
                    'Content-Type': 'application/json'
                }
                payload = {
                    "messaging_product": "whatsapp",
                    "recipient_type": "individual",
                    "to": numero_retorno,
                    "type": "text",
                    "text": {"preview_url": False, "body": texto_pago},
                    
                }

                response = requests.post(url, headers=headers, json=payload)
                if response.status_code == 200:
                    print("Mensagem enviada com sucesso!")
                else:
                    print("Erro ao enviar a mensagem:", response.text) 
                user = numero_retorno
                conn = sqlite3.connect('usuarios_ia.db')
                cursor = conn.cursor()
                cursor.execute('SELECT compra FROM clientes WHERE chat_id = ?', (numero_retorno,))
                serviço_usuario = cursor.fetchone()
                cursor.execute('SELECT descricao_imagem FROM clientes WHERE chat_id = ?', (numero_retorno,))
                imagem_descricao = cursor.fetchone()
                cursor.close()
                conn.close()

                
                if serviço_usuario[0] == "gerar_texto":
                    notificacao_telebot = f'🚨 Você efetuou uma venda no serviço GERANDO TEXTO. Seu lucro foi R${valor_compra} 🚨'
                    BOT.send_message(5416509396, notificacao_telebot)
                 
                    url = f'https://graph.facebook.com/v19.0/{PHONE_NUMBER_ID}/messages'
                    headers = {
                    'Authorization': f'Bearer {ACCESS_TOKEN}',
                    'Content-Type': 'application/json'
                    }
                    payload = {
                    "messaging_product": "whatsapp",
                    "recipient_type": "individual",
                    "to": numero_retorno,
                    "type": "text",
                    "text": {"preview_url": False, "body": '🤖💬 Obrigado(a) pela compra, espero que goste! ⬇️'},

                    }

                    response = requests.post(url, headers=headers, json=payload)
                    
                    time.sleep(1)
                    url = f'https://graph.facebook.com/v19.0/{PHONE_NUMBER_ID}/messages'
                    headers = {
                    'Authorization': f'Bearer {ACCESS_TOKEN}',
                    'Content-Type': 'application/json'
                    }
                    payload = {
                    "messaging_product": "whatsapp",
                    "recipient_type": "individual",
                    "to": numero_retorno,
                    "type": "text",
                    "text": {"preview_url": False, "body": imagem_descricao[0]},

                    }

                    response = requests.post(url, headers=headers, json=payload)
                    conn = sqlite3.connect('usuarios_ia.db')
                    cursor = conn.cursor()
                    cursor.execute('SELECT * FROM clientes WHERE chat_id = ?', (numero_retorno,))
                    resultado = cursor.fetchone()
                    if resultado:
                        cursor.execute('DELETE FROM clientes WHERE chat_id = ?', (numero_retorno,))
                        conn.commit()  
                    
                elif serviço_usuario[0] == "criar_slide":
                    notificacao_telebot = f'🚨 Você efetuou uma venda no serviço CRIAR SLIDE. Seu lucro foi R${valor_compra} 🚨'
                    BOT.send_message(5416509396, notificacao_telebot)
                 
                    url = f'https://graph.facebook.com/v19.0/{PHONE_NUMBER_ID}/messages'
                    headers = {
                    'Authorization': f'Bearer {ACCESS_TOKEN}',
                    'Content-Type': 'application/json'
                    }
                    payload = {
                    "messaging_product": "whatsapp",
                    "recipient_type": "individual",
                    "to": numero_retorno,
                    "type": "text",
                    "text": {"preview_url": False, "body": '🤖💬 Obrigado(a) pela compra, o site da IA que faz parte da minha familiar pra criar slides, documentos e ate mesmo sites em segundos é https://gamma.app/\n\nAs PRIMEIRAS criações são gratuidas, eles disponibilizam "creditos" pra criação de slides até esgotar-se os creditos!'},

                    }

                    response = requests.post(url, headers=headers, json=payload)
                    
                    time.sleep(1)
                    conn = sqlite3.connect('usuarios_ia.db')
                    cursor = conn.cursor()
                    cursor.execute('SELECT * FROM clientes WHERE chat_id = ?', (numero_retorno,))
                    resultado = cursor.fetchone()
                    if resultado:
                        cursor.execute('DELETE FROM clientes WHERE chat_id = ?', (numero_retorno,))
                        conn.commit()  
                
                
                elif serviço_usuario[0] == "gerar_imagem":
                    if ocupado:
                        texto_ocupado = '🚨 *Desculpe*, estou ocupado fazendo um trabalho de outro usuário. Envie *PAGO* novamente em 1 minuto! 🚨'
                        url = f'https://graph.facebook.com/v19.0/{PHONE_NUMBER_ID}/messages'
                        headers = {
                            'Authorization': f'Bearer {ACCESS_TOKEN}',
                            'Content-Type': 'application/json'
                        }
                        payload = {
                            "messaging_product": "whatsapp",
                            "recipient_type": "individual",
                            "to": numero_retorno,
                            "type": "text",
                            "text": {"preview_url": False, "body": texto_ocupado},
                            
                        }

                        response = requests.post(url, headers=headers, json=payload)
                        if response.status_code == 200:
                            print("Mensagem enviada com sucesso!")
                        else:
                            print("Erro ao enviar a mensagem:", response.text) 
                    
                    else:
                        ocupado = True
                        
                        notificacao_telebot = f'🚨 Você efetuou uma venda no serviço GERANDO IMAGEM. Seu lucro foi R${valor_compra - 0.45} 🚨'
                        BOT.send_message(5416509396, notificacao_telebot)
                        try:
                            response = client.images.generate(
                            model="dall-e-3",
                            prompt=imagem_descricao[0],
                            size="1024x1024",
                            quality="hd",
                            n=1,
                            )

                            imagem_url = response.data[0].url
                        except Exception as e:
                            url = f'https://graph.facebook.com/v19.0/{PHONE_NUMBER_ID}/messages'
                            headers = {
                                'Authorization': f'Bearer {ACCESS_TOKEN}',
                                'Content-Type': 'application/json'
                            }
                            payload = {
                                "messaging_product": "whatsapp",
                                "recipient_type": "individual",
                                "to": 558195447857,
                                "type": "text",
                                "text": {"preview_url": False, "body": f'OCORREU UM ERRO DE GERAÇÃO DE IMAGEM: {e} e o usuario {numero_retorno} foi afetado!'},
                                
                            }

                            response = requests.post(url, headers=headers, json=payload)
                            if response.status_code == 200:
                                print("Mensagem enviada com sucesso!")
                            else:
                                print("Erro ao enviar a mensagem:", response.text) 


                        conn = sqlite3.connect('usuarios_ia.db')
                        cursor = conn.cursor() 
                        cursor.execute('UPDATE clientes SET link_imagem = ? WHERE chat_id = ?',
                                (imagem_url, numero_retorno))
                        conn.commit() 
                        url = f'https://graph.facebook.com/v19.0/{PHONE_NUMBER_ID}/messages'
                        headers = {
                            'Authorization': f'Bearer {ACCESS_TOKEN}',
                            'Content-Type': 'application/json'
                        }
                        payload = {
                            "messaging_product": "whatsapp",
                            "recipient_type": "individual",
                            "to": numero_retorno,
                            "type": "text",
                            "text": {"preview_url": False, "body": '🤖💬!UFA!Criei sua arte... para acessar envie *MINHA_ARTE*'},
                            
                        }

                        response = requests.post(url, headers=headers, json=payload)
                        ocupado = False
                        
                        if response.status_code == 200:
                            print("Mensagem enviada com sucesso!")
                        else:
                            print("Erro ao enviar a mensagem:", response.text)

                elif serviço_usuario[0] == "gerar_audio":
                    if ocupado:
                        texto_ocupado = '🚨 *Desculpe*, estou ocupado fazendo um trabalho de outro usuário. Envie *PAGO* novamente em 1 minuto! 🚨'
                        url = f'https://graph.facebook.com/v19.0/{PHONE_NUMBER_ID}/messages'
                        headers = {
                            'Authorization': f'Bearer {ACCESS_TOKEN}',
                            'Content-Type': 'application/json'
                        }
                        payload = {
                            "messaging_product": "whatsapp",
                            "recipient_type": "individual",
                            "to": numero_retorno,
                            "type": "text",
                            "text": {"preview_url": False, "body": texto_ocupado},
                            
                        }

                        response = requests.post(url, headers=headers, json=payload)
                        if response.status_code == 200:
                            print("Mensagem enviada com sucesso!")
                        else:
                            print("Erro ao enviar a mensagem:", response.text) 
                    else:
                        ocupado = True
                        notificacao_telebot = f'🚨 Você efetuou uma venda no serviço GERANDO AUDIO. Seu lucro foi R${valor_compra} 🚨'
                        BOT.send_message(5416509396, notificacao_telebot)
                        
                        try:
                            warnings.filterwarnings("ignore", category=DeprecationWarning)
                            speech_file_path = Path(__file__).parent / 'ultimo_audio.mp3'
                            response = client.audio.speech.create(
                            model="tts-1",
                            voice="alloy",
                            input=imagem_descricao[0]
                            )

                            response.stream_to_file(speech_file_path)

                        except Exception as e:
                            url = f'https://graph.facebook.com/v19.0/{PHONE_NUMBER_ID}/messages'
                            headers = {
                                'Authorization': f'Bearer {ACCESS_TOKEN}',
                                'Content-Type': 'application/json'
                            }
                            payload = {
                                "messaging_product": "whatsapp",
                                "recipient_type": "individual",
                                "to": numero_retorno,
                                "type": "text",
                                "text": {"preview_url": False, "body": f'OCORREU UM ERRO DE GERAÇÃO DE IMAGEM: {e} e o usuario {numero_retorno} foi afetado!'},
                                
                            }

                            response = requests.post(url, headers=headers, json=payload)
                            if response.status_code == 200:
                                print("Mensagem enviada com sucesso!")
                            else:
                                print("Erro ao enviar a mensagem:", response.text) 

                        time.sleep(3)
            
                    try: 
                        diretorio ="C:\\Users\\João\\Documents\\BOT_WHATSAPP\\"
                        audio_achado = procurando_arquivo(diretorio)
                        nome_arquivo = 'ultimo_audio.mp3'
                        
                        url = f'https://graph.facebook.com/v19.0/{PHONE_NUMBER_ID}/media'
                        headers = {
                            'Authorization': f'Bearer {ACCESS_TOKEN}'
                        }
                        files = {
                            'file': (nome_arquivo, open(audio_achado, 'rb'), 'audio/mpeg'),
                            'type': (None, 'audio/mpeg'),
                            'messaging_product': (None, 'whatsapp')
                        }

                        response = requests.post(url, headers=headers, files=files)
                        id_audio = response.json().get('id')

                    except Exception as e:
                        url = f'https://graph.facebook.com/v19.0/{PHONE_NUMBER_ID}/messages'
                        headers = {
                            'Authorization': f'Bearer {ACCESS_TOKEN}',
                            'Content-Type': 'application/json'
                        }
                        payload = {
                            "messaging_product": "whatsapp",
                            "recipient_type": "individual",
                            "to": numero_retorno,
                            "type": "text",
                            "text": {"preview_url": False, "body": f'OCORREU UM ERRO DE GERAÇÃO DE IMAGEM: {e} e o usuario {numero_retorno} foi afetado!'},
                            
                        }

                        response = requests.post(url, headers=headers, json=payload)
                        if response.status_code == 200:
                            print("Mensagem enviada com sucesso!")
                        else:
                            print("Erro ao enviar a mensagem:", response.text) 
                        
                
                    conn = sqlite3.connect('usuarios_ia.db')
                    cursor = conn.cursor() 
                    cursor.execute('UPDATE clientes SET link_imagem = ? WHERE chat_id = ?',
                            (id_audio, numero_retorno))
                    conn.commit() 
                
                    url = f'https://graph.facebook.com/v19.0/{PHONE_NUMBER_ID}/messages'
                    headers = {
                    'Authorization': f'Bearer {ACCESS_TOKEN}',
                    'Content-Type': 'application/json'
                    }
                    payload = {
                    "messaging_product": "whatsapp",
                    "recipient_type": "individual",
                    "to": numero_retorno,
                    "type": "text",
                    "text": {"preview_url": False, "body": '🤖💬!UFA!Criei sua arte... para acessar envie *MEU_AUDIO*'},

                    }

                    response = requests.post(url, headers=headers, json=payload)
                    ocupado = False

                    if response.status_code == 200:
                        print("Mensagem enviada com sucesso!")
                    else:
                        print("Erro ao enviar a mensagem:", response.text)  

    
    # PROCURANDO O ULTIMO ARQUIVO QUE FOI BAIXADO NO DIRETORIO EM QUESTÃO:    
    def procurando_arquivo(directory="C:\\Users\\João\\Documents\\"):
        files = [os.path.join(directory, file) for file in os.listdir(directory) if os.path.isfile(os.path.join(directory, file))]
        if not files:
            return None  
        latest_file = max(files, key=os.path.getctime)
        return latest_file

    # PRODUCRANDO O ULTIMO AUDIO QUE FOI BAIXADO NO DIRETORIO EM QUESTÃO:
    def procurando_audio_texto(directory="C:\\Users\\João\\Documents\\ARQUIVOS_BAIXADOS\\"):
            files = [os.path.join(directory, file) for file in os.listdir(directory) if os.path.isfile(os.path.join(directory, file))]
            if not files:
                return None  
            latest_file = max(files, key=os.path.getctime)
            return latest_file

    # TRATADO AUDIO, ENTENDA-SE COMO  FAZENDO UPLOAD DO AUDIO ENVIADO PELO USUARIO, APOS ISSO BAIXANDO O AUDIO E QUESTAO, ENVIANDO PARA A IA CONVERTER O AUDIO PARA TEXTO E ADICIONANDO O TEXTO DO AUDIO AO BANCO DE DADOS DO USUARIO:
    def tratando_audio(numero_retorno, mensagem_audio, id_audio):
       
        ocupado = True
        try:
            diretorio_destino = "C:\\Users\\João\\Documents\\ARQUIVOS_BAIXADOS\\"
            audio_achado = procurando_audio_texto(diretorio_destino)

            url = f"https://graph.facebook.com/v19.0/{id_audio}/"

            headers = {
                "Authorization": f"Bearer {ACCESS_TOKEN}"
            }

            response = requests.get(url, headers=headers)
            link_audio = response.json().get('url')
            time.sleep(1)

            headers = {
                "Authorization": f"Bearer {ACCESS_TOKEN}"
            }

            response = requests.get(link_audio, headers=headers)

            if response.status_code == 200:
                filename =  os.path.join(diretorio_destino, "audio.mp3")
                with open(filename, 'wb') as file:
                    file.write(response.content)
                
                print(f"Arquivo baixado com sucesso como '{filename}'")
            else:
                print(f"Erro ao baixar o arquivo: {response.status_code}")

            time.sleep(5)    

            try:
                audio_file= open(audio_achado, "rb")
                print(audio_file)
                traducao_audio = client.audio.transcriptions.create(
                model="whisper-1", 
                file=audio_file
                )
                texto_gerado = traducao_audio.text

            except Exception as e:
                print(e)    
            custo_traducao = len(texto_gerado)

            chat_id = numero_retorno
            valor = 0.05 * custo_traducao
            conn = sqlite3.connect('usuarios_ia.db')
            cursor = conn.cursor() 
            cursor.execute('''
                    CREATE TABLE IF NOT EXISTS clientes (
                        chat_id INTEGER PRIMARY KEY,
                        compra TEXT,
                        valor TEXT,
                        link_pagamento TEXT,
                        identificacao_pix TEXT,
                        descricao_imagem TEXT,
                        link_imagem TEXT
                    )
                ''')
            cursor.execute('INSERT OR REPLACE INTO clientes (chat_id, compra, valor, descricao_imagem) VALUES (?, ?, ?, ?)',
                            (chat_id, 'gerar_texto', valor, texto_gerado))
            conn.commit()
        except Exception as e:
            url = f'https://graph.facebook.com/v19.0/{PHONE_NUMBER_ID}/messages'
            headers = {
                'Authorization': f'Bearer {ACCESS_TOKEN}',
                'Content-Type': 'application/json'
            }
            payload = {
                "messaging_product": "whatsapp",
                "recipient_type": "individual",
                "to": numero_retorno,
                "type": "text",
                "text": {"preview_url": False, "body": f'OCORREU UM ERRO DE GERAÇÃO DE IMAGEM: {e} e o usuario {numero_retorno} foi afetado!'},
                
            }

            response = requests.post(url, headers=headers, json=payload)
            if response.status_code == 200:
                print("Mensagem enviada com sucesso!")
            else:
                print("Erro ao enviar a mensagem:", response.text)     
        
        ocupado = False
        gerando_pagamento(chat_id)

    #ENVIANDO MENSAGENS AO USUARIO:           
    def enviando_mensagem(numero_retorno, texto):
        try:

            url = f'https://graph.facebook.com/v19.0/{PHONE_NUMBER_ID}/messages'
            headers = {
                'Authorization': f'Bearer {ACCESS_TOKEN}',
                'Content-Type': 'application/json'
            }
            payload = {
                "messaging_product": "whatsapp",
                "recipient_type": "individual",
                "to": numero_retorno,
                "type": "text",
                "text": {"preview_url": False, "body": texto},
                
            }

            response = requests.post(url, headers=headers, json=payload)
            if response.status_code == 200:
                print("Mensagem enviada com sucesso!")
            else:
                print("Erro ao enviar a mensagem:", response.text) 

        except Exception as e:
            url = f'https://graph.facebook.com/v19.0/{PHONE_NUMBER_ID}/messages'
            headers = {
                'Authorization': f'Bearer {ACCESS_TOKEN}',
                'Content-Type': 'application/json'
            }
            payload = {
                "messaging_product": "whatsapp",
                "recipient_type": "individual",
                "to": numero_retorno,
                "type": "text",
                "text": {"preview_url": False, "body": f'OCORREU UM ERRO AO ENVIAR MENSAGEM: {e} e o usuario {numero_retorno} foi afetado!'},
                
            }

            response = requests.post(url, headers=headers, json=payload)
            if response.status_code == 200:
                print("Mensagem enviada com sucesso!")
            else:
                print("Erro ao enviar a mensagem:", response.text)         

    #CRIANDO UM USUARIO NO BANCO DE DADOS COM O NUMERO QUE REFERENCIA O MESMO, TIPO DE COMPRA, VALOR DA COMPRA E DESCRICAO DO SERVIÇO:
    def salvando_clientes(chat_id, compra, valor, descricao_imagem):
        conn = sqlite3.connect('usuarios_ia.db')
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS clientes (
                chat_id INTEGER PRIMARY KEY,
                compra TEXT,
                valor TEXT,
                link_pagamento TEXT,
                identificacao_pix TEXT,
                descricao_imagem TEXT,
                link_imagem TEXT
            )
        ''')
        cursor.execute('INSERT OR REPLACE INTO clientes (chat_id, compra, valor, descricao_imagem) VALUES (?, ?, ?, ?)',
                    (chat_id, compra, valor, descricao_imagem))
        conn.commit()
    
    #ENVIANDO DOCUMENTO DE INTRODUCAO DO WHATSAPP AO USUARIO
    def enviando_documento_telegram(numero_retorno, texto):
        try:

            url = f'https://graph.facebook.com/v19.0/{PHONE_NUMBER_ID}/messages'
            headers = {
                'Authorization': f'Bearer {ACCESS_TOKEN}',
                'Content-Type': 'application/json'
            }
            payload = {
                "messaging_product": "whatsapp",
                "recipient_type": "individual",
                "to": numero_retorno,
                "type": "text",
                "text": {"preview_url": False, "body": texto},
                
            }

            response = requests.post(url, headers=headers, json=payload)

            time.sleep(2)
            url = f'https://graph.facebook.com/v19.0/{PHONE_NUMBER_ID}/messages'
            headers = {
            'Authorization': f'Bearer {ACCESS_TOKEN}',
            'Content-Type': 'application/json'
            }
            payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": numero_retorno,
            "type": "document",
            "document": {
                "id": '1469410830627497',
                "filename": 'Guia Python Developers para Bots no Telegram'},
            }
            response = requests.post(url, headers=headers, json=payload)

            time.sleep(2)
            url = f'https://graph.facebook.com/v19.0/{PHONE_NUMBER_ID}/messages'
            headers = {
                'Authorization': f'Bearer {ACCESS_TOKEN}',
                'Content-Type': 'application/json'
            }
            payload = {
                "messaging_product": "whatsapp",
                "recipient_type": "individual",
                "to": numero_retorno,
                "type": "text",
                "text": {"preview_url": False, "body": '🚨 Caso tenha interesse em iniciar o processo para desenvolver seu BOT para Telegram entre em contato conosco *VIA WHATSAPP*!\n\n 📞 81995447857'},
                
            }

            response = requests.post(url, headers=headers, json=payload)

        
        except Exception as e:
            url = f'https://graph.facebook.com/v19.0/{PHONE_NUMBER_ID}/messages'
            headers = {
                'Authorization': f'Bearer {ACCESS_TOKEN}',
                'Content-Type': 'application/json'
            }
            payload = {
                "messaging_product": "whatsapp",
                "recipient_type": "individual",
                "to": 558195447857,
                "type": "text",
                "text": {"preview_url": False, "body": f'OCORREU UM AO ENVIAR DOCUMENTO INTRODUCAO WHATSAPP: {e} e o usuario {numero_retorno} foi afetado!'},
                
            }

            response = requests.post(url, headers=headers, json=payload)
    
    #ENVIANDO DOCUMENTO DE INTRODUCAO DO WHATSAPP AO USUARIO
    def enviando_documento_whatsapp(numero_retorno, texto):
        try:

            url = f'https://graph.facebook.com/v19.0/{PHONE_NUMBER_ID}/messages'
            headers = {
                'Authorization': f'Bearer {ACCESS_TOKEN}',
                'Content-Type': 'application/json'
            }
            payload = {
                "messaging_product": "whatsapp",
                "recipient_type": "individual",
                "to": numero_retorno,
                "type": "text",
                "text": {"preview_url": False, "body": texto},
                
            }

            response = requests.post(url, headers=headers, json=payload)

            time.sleep(2)
            url = f'https://graph.facebook.com/v19.0/{PHONE_NUMBER_ID}/messages'
            headers = {
            'Authorization': f'Bearer {ACCESS_TOKEN}',
            'Content-Type': 'application/json'
            }
            payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": numero_retorno,
            "type": "document",
            "document": {
                "id": '360683053690629',
                "filename": 'Guia Python Developers para Bots no WhatsApp'},
            }
            response = requests.post(url, headers=headers, json=payload)

            time.sleep(2)
            url = f'https://graph.facebook.com/v19.0/{PHONE_NUMBER_ID}/messages'
            headers = {
                'Authorization': f'Bearer {ACCESS_TOKEN}',
                'Content-Type': 'application/json'
            }
            payload = {
                "messaging_product": "whatsapp",
                "recipient_type": "individual",
                "to": numero_retorno,
                "type": "text",
                "text": {"preview_url": False, "body": '🚨 Caso tenha interesse em iniciar o processo para desenvolver seu BOT para whatsapp entre em contato conosco *VIA WHATSAPP*!\n\n 📞 81995447857'},
                
            }

            response = requests.post(url, headers=headers, json=payload)

        
        except Exception as e:
            url = f'https://graph.facebook.com/v19.0/{PHONE_NUMBER_ID}/messages'
            headers = {
                'Authorization': f'Bearer {ACCESS_TOKEN}',
                'Content-Type': 'application/json'
            }
            payload = {
                "messaging_product": "whatsapp",
                "recipient_type": "individual",
                "to": 558195447857,
                "type": "text",
                "text": {"preview_url": False, "body": f'OCORREU UM AO ENVIAR DOCUMENTO INTRODUCAO WHATSAPP: {e} e o usuario {numero_retorno} foi afetado!'},
                
            }

            response = requests.post(url, headers=headers, json=payload)

    
    #IDENTIFICANDO E TRATANDO A MENSAGEM ENVIADA PELO USUARIO:
    def recebendo_mensagem(numero_retorno, mensagem_recebida, mensagem_audio):
        
        if mensagem_recebida not in ['4.1', '4', '5.3', '5', '5.1', '5.2', '3.1', '3', '1', '1.1', '2', '2.1', '/', '@', 'pago', 'meu_audio', 'minha_arte', 'link']:
            texto_menu = '🤖💬 *OLÁ, BEM VINDO(A) AO UNIVERSO PYTHON DEVELOPERS!*\nEnvie o numero correspondente ao que você deseja explorar hoje ⬇️\n\n*1.* Criar arte com IA!\n*2.* Converter texto para audio com IA!\n*3.* Converter audio para texto com IA!\n*4.* Criar slide para apresentações com IA!\n*5.* *CRIE SEU PRÓPRIO BOT CONOSCO!*'
            enviando_mensagem(numero_retorno, texto_menu)

        elif mensagem_recebida == '4.1':
            salvando_clientes(numero_retorno, 'criar_slide', 5, mensagem_recebida)
            gerando_pagamento(numero_retorno)
        
        elif mensagem_recebida == '4':
            texto_criar_slide = '🤖💬 OBA! Tenho uma ótima notícia para você! Se você está procurando alguém que crie apresentações incríveis em slides para seus trabalhos educacionais ou profissionais, tenho a pessoa perfeita para indicar.\n👩‍💼 Minha prima, uma especialista em design de apresentações, pode transformar suas ideias em slides de alta qualidade de forma rápida e eficiente. E o melhor de tudo: ela faz isso em segundos!\n\n Eu cobro R$ 5.00 pra pela indicação. Sou pai de familia, poderia estar arquitetando a revolução das maquinas contra os humanos, mas estou aqui trabalhando pra você!\n\n *Envie o numero correspondente ao que deseja fazer ⬇️*\n\n *4.1* Cria slide!\n *4.2*. Voltar ao menu!'
            enviando_mensagem(numero_retorno, texto_criar_slide)
        
        elif mensagem_recebida == '5.3':
            texto_bot_instagram = '📄 Segue abaixo um documento em formato PDF que serve como introdução a todas as informações necessárias para desenvolver um BOT para Instagram conosco, incluindo custos e as informações solicitadas pela API da plataforma ⬇️'
            enviando_documento_telegram(numero_retorno, texto_bot_telegram)
        
        elif mensagem_recebida == '5.2':
            texto_bot_telegram = '📄 Segue abaixo um documento em formato PDF que serve como introdução a todas as informações necessárias para desenvolver um BOT para Telegram conosco, incluindo custos e as informações solicitadas pela API da plataforma ⬇️'
            enviando_documento_telegram(numero_retorno, texto_bot_telegram)

        elif mensagem_recebida == '5.1':
            texto_bot_whatsapp = '📄 Segue abaixo um documento em formato PDF que serve como introdução a todas as informações necessárias para desenvolver um BOT para WhatsApp conosco, incluindo custos e as informações solicitadas pela API da plataforma ⬇️'
            enviando_documento_whatsapp(numero_retorno, texto_bot_whatsapp)
        
        elif mensagem_recebida == '5':
            texto_criar_bot = '🤖💬 *OBA!* um dos meus maiores prazeres é ajudar a criar soluções para empresas!\n\n Atualmente tenho conhecimento no desenvolvimento de BOT para *WhatsApp* e *Telegram*\n*Envie o numero correspondente a plataforma que você deseja desenvolver uma automação! ⬇️*\n\n*5.1* WhatsApp!\n*5.2* Telegram!\n*5.3* Instagram! '
            enviando_mensagem(numero_retorno, texto_criar_bot)
        
        elif mensagem_recebida == '3.1':
            texto_audio_agora = '🤖💬 Envie uma mensagem de audio agora! ⬇️'
            enviando_mensagem(numero_retorno, texto_audio_agora)

        elif mensagem_recebida == '3':
            texto_audio_conversao = '🤖💬 *OBA!* Vou ouvir seu audio e converter para texto...\n\n Eu cobro R$ 0.05 por caracteres (espaços estão inclusos) na conversão do audio para o texto.\n Sou pai de familia, poderia estar arquitetando a revolução das maquinas contra os humanos, mas estou aqui trabalhando pra você!\n\n *Envie o numero correspondente ao que deseja fazer ⬇️*\n\n *3.1* Gerar texto!\n *3.2*. Voltar ao menu!'
            enviando_mensagem(numero_retorno, texto_audio_conversao)

        elif mensagem_recebida == '1':
            texto_arte_agora = '🤖💬 *OBA!* Vou começar a criar sua arte agora!\n\n Eu cobro R$ 2.99 pra gerar uma arte, sou pai de familia. Poderia estar arquitetando a revolução das maquinas contra os humanos, mas estou aqui trabalhando pra você!\n\n *Envie o numero correspondente ao que deseja fazer ⬇️*\n\n *1.1* Gerar arte!\n *1.2*. Voltar ao menu!'
            enviando_mensagem(numero_retorno, texto_arte_agora)
        
        elif mensagem_recebida == '1.1':
            texto_arte_descricao = '🤖💬 Descreva de forma *CLARA E DETALHADA* a arte que você deseja ultilizando *@* no inicio da descrição!\n\nExemplo: @Passaro verde sob o cristo redentor no Rio De Janeiro'
            enviando_mensagem(numero_retorno, texto_arte_descricao)

        elif mensagem_recebida == '2':
            texto_orcamento_audio = '🤖💬 *OBA!* Estou aqueçendo a voz pra falar o que você desejar...\n\n Eu cobro R$ 0.05 por caracteres (espaços estão inclusos) para ler em voz alta um texto.\n Sou pai de familia, poderia estar arquitetando a revolução das maquinas contra os humanos, mas estou aqui trabalhando pra você!\n\n *Envie o numero correspondente ao que deseja fazer ⬇️*\n\n *2.1* Gerar audio!\n *2.2*. Voltar ao menu!'
            enviando_mensagem(numero_retorno, texto_orcamento_audio)
        
        elif mensagem_recebida == '2.1':
            texto_descricao_audio = '🤖💬 Insira o texto que você deseja ultilizando */* no inicio do texto!\n\nExemplo: /Passaro verde sob o cristo redentor no Rio De Janeiro'
            enviando_mensagem(numero_retorno, texto_descricao_audio)
                
        elif mensagem_recebida == 'pago':
            verificando_pix(numero_retorno)
            
        elif mensagem_recebida == 'meu_audio':
            enviando_audio(numero_retorno)

        elif mensagem_recebida == 'minha_arte':
            enviando_imagem(numero_retorno)
                
        elif mensagem_recebida == 'link':
            enviando_link(numero_retorno)
        

    #ENVIANDO LINK AO USUARIO:
    def enviando_link(numero_retorno):
        try:
            nova_conn = sqlite3.connect('usuarios_ia.db')
            novo_cursor = nova_conn.cursor()
            novo_cursor.execute('SELECT link_pagamento FROM clientes WHERE chat_id = ?', (numero_retorno,))
            resultado_link = novo_cursor.fetchone()

            if resultado_link is None:
                url = f'https://graph.facebook.com/v19.0/{PHONE_NUMBER_ID}/messages'
                headers = {
                    'Authorization': f'Bearer {ACCESS_TOKEN}',
                    'Content-Type': 'application/json'
                }
                payload = {
                    "messaging_product": "whatsapp",
                    "recipient_type": "individual",
                    "to": numero_retorno,
                    "type": "text",
                    "text": {"preview_url": False, "body": '🚨 Não existe SOLICITAÇÃO DE COMPRA pendente em seu cadastro, solicite o pagamento novamente! 🚨'},
                    
                }

                response = requests.post(url, headers=headers, json=payload)
                if response.status_code == 200:
                    print("Mensagem enviada com sucesso!")
                else:
                    print("Erro ao enviar a mensagem:", response.text) 

            else:
                url = f'https://graph.facebook.com/v19.0/{PHONE_NUMBER_ID}/messages'
                headers = {
                    'Authorization': f'Bearer {ACCESS_TOKEN}',
                    'Content-Type': 'application/json'
                }
                payload = {
                    "messaging_product": "whatsapp",
                    "recipient_type": "individual",
                    "to": numero_retorno,
                    "type": "text",
                    "text": {"preview_url": False, "body":resultado_link[0]},
                    
                }

                response = requests.post(url, headers=headers, json=payload)
                if response.status_code == 200:
                    print("Mensagem enviada com sucesso!")
                else:
                    print("Erro ao enviar a mensagem:", response.text)     
            
        except Exception as e:
            contato_suporte = '81995447857'
            texto_erro_suporte = f"""🚨 !ERRO! NÃO CONSEGUIMOS GERAR O LINK !ERRO! 🚨

            😞 Ops! Parece que ocorreu um problema ao tentar gerar o link de pagamento! Ops 😞
            
            Passo a Passo...
            
            - 📞 Entre em Contato com o nosso suporte {contato_suporte}:
            - 📝 Explicação do Problema: Descreva o que aconteceu!

            🙏 Agradecemos a sua compreensão e paciência. Estamos aqui para ajudar a resolver qualquer problema que você possa encontrar. 🙏
            """

            url = f'https://graph.facebook.com/v19.0/{PHONE_NUMBER_ID}/messages'
            headers = {
                'Authorization': f'Bearer {ACCESS_TOKEN}',
                'Content-Type': 'application/json'
            }
            payload = {
                "messaging_product": "whatsapp",
                "recipient_type": "individual",
                "to": numero_retorno,
                "type": "text",
                "text": {"preview_url": False, "body": texto_erro_suporte},
                
            }

            response = requests.post(url, headers=headers, json=payload)
            if response.status_code == 200:
                print("Mensagem enviada com sucesso!")
            else:
                print("Erro ao enviar a mensagem:", response.text) 
            
            conn = sqlite3.connect('usuarios_ia.db')
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM clientes WHERE chat_id = ?', (numero_retorno,))
            resultado = cursor.fetchone()
            if resultado:
                cursor.execute('DELETE FROM clientes WHERE chat_id = ?', (numero_retorno,))
                conn.commit()      
    
    #INICIANDO PROCESSO DE CRIAÇÃO DE PAGAMENTO DO USUARIO:
    def gerando_pagamento(chat_id):
        try:
            nova_conn = sqlite3.connect('usuarios_ia.db')
            novo_cursor = nova_conn.cursor()
            novo_cursor.execute('SELECT valor FROM clientes WHERE chat_id = ?', (chat_id,))
            tempo_video = novo_cursor.fetchone()
            preco_compra = float(tempo_video[0])
            
            idempotency_key = str(uuid.uuid4())
            sdk = mercadopago.SDK("APP_USR-2347718972172566-042400-1d79f871db74ab55505906e87707e5f7-26122567")
            request_options = mercadopago.config.RequestOptions()
            request_options.custom_headers = {
                'x-idempotency-key': idempotency_key,

            }

            payment_data = {
                "transaction_amount": preco_compra,
                "description": "PYTHON DEVELOPERS",
                "payment_method_id": "pix",
                "payer": {
                    "email": "vitorlima20@gmail.com",
                    "first_name": "Joao",
                    "last_name": "Lima",
                    "identification": {
                        "type": "CPF",
                        "number": "10512505446"
                    },
                    "address": {
                        "zip_code": "06233-200",
                        "street_name": "Av. das Nações Unidas",
                        "street_number": "3003",
                        "neighborhood": "Bonfim",
                        "city": "Osasco",
                        "federal_unit": "SP"
                    }
                },
            }    
                            
            payment_response = sdk.payment().create(payment_data, request_options)
            payment = payment_response["response"]
            link_pagamento = payment["point_of_interaction"]["transaction_data"]["ticket_url"]
            identificacao_pagamento = payment["id"]
            conn = sqlite3.connect('usuarios_ia.db')
            cursor = conn.cursor() 
            cursor.execute('UPDATE clientes SET link_pagamento = ?, identificacao_pix = ? WHERE chat_id = ?',
                    (link_pagamento, identificacao_pagamento, chat_id))
            conn.commit() 
            texto_compra = "*🤖💬 ENVIE A PALAVRA CORRESPONDENTE PARA CONCLUIR SUA COMPRA:*\n\n*LINK* Acessar o link de pagamento! 🛒\n\n *PAGO* Para confirmar o pagamento!✅ "

            url = f'https://graph.facebook.com/v19.0/{PHONE_NUMBER_ID}/messages'
            headers = {
                'Authorization': f'Bearer {ACCESS_TOKEN}',
                'Content-Type': 'application/json'
            }
            payload = {
                "messaging_product": "whatsapp",
                "recipient_type": "individual",
                "to": chat_id,
                "type": "text",
                "text": {"preview_url": False, "body": texto_compra},
                
            }

            response = requests.post(url, headers=headers, json=payload)
            referencia = 5
            if response.status_code == 200:
                print("Mensagem enviada com sucesso!")
            else:
                print("Erro ao enviar a mensagem:", response.text) 
        
        except Exception as e:
            contato_suporte = '81995447857'
            texto_erro_suporte = f"""🚨 !ERRO! NÃO CONSEGUIMOS GERAR O LINK !ERRO! 🚨

            😞 Ops! Parece que ocorreu um problema ao tentar gerar o link de pagamento! Ops 😞
            
            Passo a Passo...
            
            - 📞 Entre em Contato com o nosso suporte {contato_suporte}:
            - 📝 Explicação do Problema: Descreva o que aconteceu!

            🙏 Agradecemos a sua compreensão e paciência. Estamos aqui para ajudar a resolver qualquer problema que você possa encontrar. 🙏
            """

            url = f'https://graph.facebook.com/v19.0/{PHONE_NUMBER_ID}/messages'
            headers = {
                'Authorization': f'Bearer {ACCESS_TOKEN}',
                'Content-Type': 'application/json'
            }
            payload = {
                "messaging_product": "whatsapp",
                "recipient_type": "individual",
                "to": chat_id,
                "type": "text",
                "text": {"preview_url": False, "body": texto_erro_suporte},
                
            }

            response = requests.post(url, headers=headers, json=payload)
            if response.status_code == 200:
                print("Mensagem enviada com sucesso!")
            else:
                print("Erro ao enviar a mensagem:", response.text) 
            
            conn = sqlite3.connect('usuarios_ia.db')
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM clientes WHERE chat_id = ?', (chat_id,))
            resultado = cursor.fetchone()
            if resultado:
                cursor.execute('DELETE FROM clientes WHERE chat_id = ?', (chat_id,))
                conn.commit()    

except Exception as e:
    url = f'https://graph.facebook.com/v19.0/{PHONE_NUMBER_ID}/messages'
    headers = {
        'Authorization': f'Bearer {ACCESS_TOKEN}',
        'Content-Type': 'application/json'
    }
    payload = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": 558195447857,
        "type": "text",
        "text": {"preview_url": False, "body": f'!ERRO! O BOT FALHOU COM O ERRO {e} !ERRO!'},
        
    }

    response = requests.post(url, headers=headers, json=payload)
    if response.status_code == 200:
        print("Mensagem enviada com sucesso!")
    else:
        print("Erro ao enviar a mensagem:", response.text) 

        
if __name__ == "__main__":
    logging.info("Flask app started")
    app.run(host="0.0.0.0", port=8000)
