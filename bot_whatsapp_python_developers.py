import requests
import logging
from flask import Flask, request, jsonify


#ngrok http 8000 --domain oryx-romantic-condor.ngrok-free.app
app = Flask(__name__)
ACCESS_TOKEN="EAAXPj6OzA3oBO5uuKcy7sWnQiKZAO8SFSfyRelNQPeC9RLqtlytM06dzS35SZAXplJMXrViA8ozQxX7L80q7jdZCgl74c370Q7kubURB5ZBBA9bPo0MSP52Tz3et6RVHSJLndBme903UykXGDYXptyzkD8AMrR7W240OeaktfxuEKx8UleC3hdROIu3BVTr2XCvoRkfOWYBIkT6a"
APP_ID="1635590717244282"
APP_SECRET="ac481f183cf46f41e374378b70193277"
RECIPIENT_WAID="+5581995447857" 
VERSION="v19.0"
PHONE_NUMBER_ID="239278652611341"
VERIFY_TOKEN="VITORXAMA"

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
                        primeiro_contato = message.get('type')
                        send_message(numero_retorno, mensagem_recebida, primeiro_contato)
                    
       
        return jsonify({'message': 'Recebido com sucesso'}), 200
    
def send_message(numero_retorno, mensagem_recebida, primeiro_contato):
    
    if mensagem_recebida not in ['1', '2', '3', '4', 'whatsapp', 'Whatsapp', 'telegram', 'Telegram', ]:
        
        texto_menu = "*Olá! Bem-vindo à Python Developer!*\n\n- Entendemos o *VALOR* do seu tempo e dinheiro! ⏳\n- Somos uma empresa focada em automação de processos e desenvolvimento de soluções inovadoras 🤖\n- Estamos aqui para ajudar a tornar seus projetos uma realidade.🚀\n\n*Escolha o numero referente ao que deseja fazer ⬇️*\n\n1. Solicitar orçamento!\n2. Qual sua proposta?\n3. Porfólio!\n4. Suporte tecnico!\n"


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
            "text": {"preview_url": False, "body": texto_menu},
            
        }

        response = requests.post(url, headers=headers, json=payload)
        if response.status_code == 200:
            print("Mensagem enviada com sucesso!")
        else:
            print("Erro ao enviar a mensagem:", response.text)
        

    
    elif mensagem_recebida == '1':
        texto_orcamento = '*🤖💬 DIGITE PARA QUAL APLICATIVO VOCÊ DESEJA DESENVOLVER UMA AUTOMAÇÃO!*\n\nWhatsapp\nTelegram'
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
            "text": {"preview_url": False, "body": texto_orcamento},
            
        }

        response = requests.post(url, headers=headers, json=payload)
        if response.status_code == 200:
            print("Mensagem enviada com sucesso!")
        else:
            print("Erro ao enviar a mensagem:", response.text)

    
    elif mensagem_recebida == 'Whatsapp' or mensagem_recebida == 'whatsapp':        
        
        texto_whatsapp = "🤖💬 *DESENVOLVA UM BOT PARA WHATSAPP E TRANSFORME SEU ATENDIMENTO*\n\nVocê deseja oferecer um atendimento excepcional aos seus clientes enquanto impulsiona suas vendas?\n\nUm bot para WhatsApp pode ser a solução que você procura! 💡✨\n\n*BENEFÍCIOS DO BOT PARA WHATSAPP:*\n\n- Disponibilidade 24/7: Imagine seus clientes obtendo suporte e informações sempre que precisarem, mesmo fora do horário comercial. 🕒\n- Respostas Rápidas e Precisas: Com um bot inteligente, suas dúvidas serão respondidas de forma rápida e precisa, aumentando a satisfação do cliente. 🚀\n- Redução da Carga de Trabalho: Libere sua equipe para lidar com questões mais complexas ao automatizar tarefas repetitivas, otimizando tempo e recursos. ⏳\n\n*ENTENDA OS CUSTOS DA API DO WHATSAPP:*\n\n📝 Sua empresa precisa de um CNPJ, é uma obrigatoriedade da API do WhatsApp Business.\n💳 É necessário cadastrar um cartão de crédito no Facebook para suprir os custos do serviço.\n ✨ Cada conta do WhatsApp Business tem direito a 1.000 conversas de serviço gratuitas por mês. Além disso, aqui estão os custos médios por tipo de conversa:\n\n💼 Conversa tipo marketing: $0.06\n 🛠️ Conversas tipo utilidade: $0.03\n 🔑 Conversas tipo autenticação: $0.03\n🤝 Conversas tipo serviço: $0.03\n 🔍 Entenda mais: https://developers.facebook.com/docs/whatsapp/pricing#rate-cards\n\n *COMO ESTIPULAMOS O CUSTO DO SEU PROJETO:*\n\n🛠️ Desenvolvemos bots para atendimento a clientes com a possibilidade de adicionar funcionalidades de vendas.\n 💬 Caso seu bot seja apenas para atendimento, o custo mínimo será de R$ 400, variando de acordo com a complexidade do projeto.\n 💰 Se você deseja incluir vendas, não há investimento inicial. Cobramos 20% POR VENDA, com uma necessidade venda mínima de R$ 500 mensais pra suprir custos de hospedagem e suporte tecnico.\n\n*ENTRE EM CONTATO E DEIXE-NOS AJUDÁ-LO:* 📞\n\nContato: 81995447857 📱\nEmail: vitorlima20@gmail.com 📧"

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
            "text": {"preview_url": False, "body": texto_whatsapp},
            
        }

        response = requests.post(url, headers=headers, json=payload)
        if response.status_code == 200:
            print("Mensagem enviada com sucesso!")
        else:
            print("Erro ao enviar a mensagem:", response.text)
    
    elif mensagem_recebida == 'Telegram' or mensagem_recebida == 'telegram':        
        
        texto_telegram = "🤖💬 *DESENVOLVA UM BOT PARA TELEGRAM E TRANSFORME SEU ATENDIMENTO*\n\n Você deseja oferecer um atendimento excepcional aos seus clientes enquanto impulsiona suas vendas?\n\n Um bot para Telegram pode ser a solução que você procura! 💡✨\n\n*BENEFÍCIOS DO BOT PARA TELEGRAM:*\n\n- Disponibilidade 24/7: Imagine seus clientes obtendo suporte e informações sempre que precisarem, mesmo fora do horário comercial. 🕒\n- Respostas Rápidas e Precisas: Com um bot inteligente, suas dúvidas serão respondidas de forma rápida e precisa, aumentando a satisfação do cliente. 🚀\n- Redução da Carga de Trabalho: Libere sua equipe para lidar com questões mais complexas ao automatizar tarefas repetitivas, otimizando tempo e recursos. ⏳\n*ENTENDA OS CUSTOS DA API DO TELEGRAM:*\n\n💰 A API do Telegram é gratuita, podendo ser cobrado apenas o custo de hospedagem do BOT!\n\n*COMO ESTIPULAMOS O CUSTO DO SEU PROJETO:*\n\n🛠️ Desenvolvemos bots para variadas intenções, como atendimento a clientes com a possibilidade de adicionar funcionalidades de vendas.\n 💬 Todo e qualquer automação tera custo mínimo de R$ 400, variando de acordo com a complexidade do projeto.\n 💰 Se você deseja criar um bot que lide com vendas, não há investimento inicial. Cobramos 20% POR VENDA, com uma necessidade venda mínima de R$ 500 mensais pra suprir custos de hospedagem e suporte tecnico.\n\n*ENTRE EM CONTATO E DEIXE-NOS AJUDÁ-LO:* 📞\n\nContato: 81995447857 📱\nEmail: vitorlima20@gmail.com 📧"
        

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
            "text": {"preview_url": False, "body": texto_telegram},
            
        }

        response = requests.post(url, headers=headers, json=payload)
        if response.status_code == 200:
            print("Mensagem enviada com sucesso!")
        else:
            print("Erro ao enviar a mensagem:", response.text)

    elif mensagem_recebida == '2':   

        texto_proposta = "🤖 *SOLUÇÕES DE AUTOMAÇÃO PERSONALIZADAS PARA O SEU PROJETO!*\n\nSe o seu projeto não está relacionado à automação para WhatsApp ou Telegram, não tem problema!\n Estamos aqui para ajudar você a encontrar a solução perfeita.\n\nIndependentemente da plataforma ou do tipo de automação que você precisa, estamos prontos para ouvir sobre as suas necessidades e oferecer soluções personalizadas.\n\nEnvie-nos sua proposta ou explique suas necessidades e deixe-nos transformar suas ideias em realidade!\n\n*ENTRE EM CONTATO E DEIXE-NOS AJUDÁ-LO:* 📞\n\nContato: 81995447857 📱\nEmail: vitorlima20@gmail.com 📧\n"

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
            "text": {"preview_url": False, "body": texto_proposta},
            
        }

        response = requests.post(url, headers=headers, json=payload)
        if response.status_code == 200:
            print("Mensagem enviada com sucesso!")
        else:
            print("Erro ao enviar a mensagem:", response.text)    

    elif mensagem_recebida == '3':  

        texto_portfolio = "🌟 *EXLORE MEU PORTFÓLIO* 🌟\n\n👨‍💻 Dê uma olhada no meu portfólio e descubra projetos incríveis que podem inspirar você.\n 🌐 Visite agora mesmo: https://www.github.com/VitorLima081"

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
            "text": {"preview_url": False, "body": texto_portfolio},
            
        }

        response = requests.post(url, headers=headers, json=payload)
        if response.status_code == 200:
            print("Mensagem enviada com sucesso!")
        else:
            print("Erro ao enviar a mensagem:", response.text)   

    elif mensagem_recebida == '4':   
        texto_suporte = "🛠️ *VOCÊ TEM ALGUMA AUTOMAÇÃO QUE FOI DESENVOLVIDA POR NÓS E PRECISA DE UM SUPORTE?!* 🛠️\n\nContato: 81995447857 📱\nEmail: vitorlima20@gmail.com 📧"

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
            "text": {"preview_url": False, "body": texto_suporte},
            
        }

        response = requests.post(url, headers=headers, json=payload)
        if response.status_code == 200:
            print("Mensagem enviada com sucesso!")
        else:
            print("Erro ao enviar a mensagem:", response.text) 
            
if __name__ == "__main__":
    logging.info("Flask app started")
    app.run(host="0.0.0.0", port=8000)
