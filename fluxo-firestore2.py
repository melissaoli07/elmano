import requests
from flask import Flask, request, jsonify
from flask_cors import CORS
from google.cloud import firestore
import os


# Inicializar Firestore
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "firebase-key.json"
db = firestore.Client()


app = Flask(__name__)
CORS(app)

# Variáveis
access_token = "EAATXaSQjmX8BO0S1nNjjwpJkFUZB7yCZCEts4ivvfhNZASQpfLGJ7H9RIB3s7QTl6cJAfwbMdVx2JQIJIZAq7C1TJDnqgXL8MkHp5tUNaZBiycAezZBCauugFsNQZAo9dIhZBP5eO265AeYjpT0848oiHNkW63KZBb8PjcaYaVresQ52b0J9vUcQvU269XBeRMnrdB3DHvhDddzCyM95OMZA22I0zK6zqExlQedRoZD"
phone_number_id = "434398029764267"

# Armazenamento do estado da conversa para cada usuário
user_state = {}


# Função para buscar dados de um evento no Firestore
def get_event_data(event_id):
    try:
        # Referência ao documento no Firestore
        doc_ref = db.collection("evento").document(event_id)
        doc = doc_ref.get()

        if doc.exists:
            data = doc.to_dict()
            print("Dados do evento encontrados:", data)
            return {
                "evento": data.get("evento", ""),
                "data": data.get("data", ""),
                "hora": data.get("hora", ""),
                "local": data.get("local", ""),
                "nome": data.get("nome", "")
            }
        else:
            print("Documento não encontrado!")
            return None
    except Exception as e:
        print(f"Erro ao buscar dados no Firestore: {e}")
        return None



# Função para salvar mensagens no Firestore com campos separados
def save_message_to_firestore(event_id,sender_id, message_type, recipient_id, message_text, button_payload, evento, data, hora, local, nome):
    try:

        doc_ref = db.collection("mensagens").document()
        doc_ref.set({
            "sender_id": sender_id,
            "recipient_id": recipient_id or "",
            "evento": evento,
            "data": data,
            "hora": hora,
            "local": local,
            "nome": nome,
            "event_id": event_id,
            "message_text": message_text,
            "button_payload": button_payload,  # Salvando o payload do botão
            "type": message_type,  # "received" ou "sent"
            "timestamp": firestore.SERVER_TIMESTAMP
        })
        print("Mensagem salva no Firestore!")
    except Exception as e:
        print(f"Erro ao salvar no Firestore: {e}")



#Template 1
def send_message_to_whatsapp(event_id):
    # Buscar os dados do evento no Firestore
    event_data = get_event_data(event_id)
    if not event_data:
        print("Erro: Não foi possível obter os dados do evento.")
        return

    # Variáveis do evento
    evento = event_data["evento"]
    data = event_data["data"]
    hora = event_data["hora"]
    local = event_data["local"]
    nome = event_data["nome"]

    url = f"https://graph.facebook.com/v17.0/{phone_number_id}/messages"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    message_data = {
        "messaging_product": "whatsapp",
        "to": "5511950404471",  
        "type": "template",
        "template": {
            "name": "template_11",  
            "language": {
                "code": "pt_BR"  
            },
            "components": [
                {
                    "type": "body",
                    "parameters": [
                        {"type": "text", "text": evento},
                        {"type": "text", "text": data},
                        {"type": "text", "text": hora},
                        {"type": "text", "text": local},
                        {"type": "text", "text": nome}
                    ]
                },
                {
                "type": "button",  # Componente de botão
                "sub_type": "quick_reply",  # Tipo do botão (quick reply)
                "index": "0",  # Índice do botão
                "parameters": [
                    {
                        "type": "payload",
                        "payload": "sim"  # Valor associado ao botão
                    }
                ]
            },
            {
                "type": "button",
                "sub_type": "quick_reply",
                "index": "1",
                "parameters": [
                    {
                        "type": "payload",
                        "payload": "nao"
                    }
                ]
            }
            ]
        }
    }

    response = requests.post(url, headers=headers, json=message_data)

    if response.status_code == 200:
        print("Template 1 enviado com sucesso!")
        save_message_to_firestore(event_id, "15551910903", "sent", "5511950404471", "message_text", "button_payload", 
        event_data['evento'],
        event_data['data'],    
        event_data['hora'],    
        event_data['local'],   
        event_data['nome'])
    else:
        print("Erro ao enviar a mensagem inicial:", response.json())


# Template 2
def reply_to_whatsapp_message(event_id, recipient_id, button_payload):

    # Buscar os dados do evento no Firestore
    event_data = get_event_data(event_id)
    if not event_data:
        print("Erro: Não foi possível obter os dados do evento.")
        return

    # Variáveis do evento
    evento = event_data["evento"]
    data = event_data["data"]
    hora = event_data["hora"]
    local = event_data["local"]
    nome = event_data["nome"]


    url = f"https://graph.facebook.com/v17.0/{phone_number_id}/messages"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    message_data = {}
    
    # Verificar se a mensagem é "sim" 
    if button_payload == "sim":
        message_data = {
            "messaging_product": "whatsapp",
            "to": recipient_id,
            "type": "template",
            "template": {
                "name": "template2",  
                "language": {
                    "code": "pt_BR"  
                },
                "components": [
                    {
                        "type": "body",
                        "parameters": [
                            {"type": "text", "text": nome},
                            {"type": "text", "text": data},
                            {"type": "text", "text": hora},
                            {"type": "text", "text": local}
                        ]
                    }
                ]
            }
        }
        # Atualizar o estado do usuário para aguardar resposta ao template2
        user_state[recipient_id] = "awaiting_template2_response"
        
    elif button_payload == "nao":
        message_data = {
            "messaging_product": "whatsapp",
            "to": recipient_id,
            "type": "text",
            "text": {
                "body": "Ok. Obrigada pela resposta."
            }
        }

    # Enviar a mensagem
    response = requests.post(url, headers=headers, json=message_data)

    if response.status_code == 200 and button_payload == "sim":
        print("Resposta enviada com sucesso!")
        save_message_to_firestore(event_id,"15551910903", "sent", "5511950404471", "message_text", "button_payload", "",
        event_data['data'],    
        event_data['hora'],    
        event_data['local'],   
        event_data['nome'])
    elif response.status_code == 200 and button_payload == "nao":
        print("Resposta de agradecimento enviada com sucesso!")
        save_message_to_firestore("15551910903", "sent", "5511950404471", message_text="Ok. Obrigada pela resposta.")
    else:
        print("Erro ao enviar a resposta:", response.json())



# Template 3
def template3(event_id, recipient_id, message_text):

    # Buscar os dados do evento no Firestore
    event_data = get_event_data(event_id)
    if not event_data:
        print("Erro: Não foi possível obter os dados do evento.")
        return

    # Variáveis do evento
    evento = event_data["evento"]
    data = event_data["data"]
    hora = event_data["hora"]
    local = event_data["local"]
    nome = event_data["nome"]

    url = f"https://graph.facebook.com/v17.0/{phone_number_id}/messages"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    # Verificar se a mensagem é "Tudo certo!" 
    if message_text.lower() in ["tudo certo!"]:
        message_data = {
        "messaging_product": "whatsapp",
        "to": recipient_id,
        "type": "template",
        "template": {
            "name": "template3",  
            "language": {
                "code": "pt_BR"  
            },
            "components": [
                {
                    "type": "body",
                    "parameters": [
                        {"type": "text", "text": nome},
                        {"type": "text", "text": data},
                        {"type": "text", "text": hora},
                        {"type": "text", "text": local}
                    ]
                }
            ]
        }
    }
        
    else:
        message_data = {
            "messaging_product": "whatsapp",
            "to": recipient_id,
            "type": "text",
            "text": {
                "body": "Ok. Obrigada pela resposta."
            }
        }

    

    response = requests.post(url, headers=headers, json=message_data)

    if response.status_code == 200:
        print("Resposta enviada com sucesso!")
        #save_message_to_firestore("15551910903", "sent", nome, data, hora, local, )
        save_message_to_firestore(event_id, "15551910903", "sent", "5511950404471", "message_text", "button_payload", "",
        event_data['data'],    
        event_data['hora'],    
        event_data['local'],   
        event_data['nome'])
        #save_message_to_firestore("15551910903", "sent", "5511950404471", nome=nome, data=data, hora=hora, local=local, event_id=event_id)
    else:
        print("Erro ao enviar a resposta:", response.json())



# Template 4
def template4(event_id, recipient_id):

    # Buscar os dados do evento no Firestore
    event_data = get_event_data(event_id)
    if not event_data:
        print("Erro: Não foi possível obter os dados do evento.")
        return

    # Variáveis do evento
    evento = event_data["evento"]
    data = event_data["data"]
    hora = event_data["hora"]
    local = event_data["local"]
    nome = event_data["nome"]

    url = f"https://graph.facebook.com/v17.0/{phone_number_id}/messages"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    message_data = {
        "messaging_product": "whatsapp",
        "to": "5511950404471",  
        "type": "template",
        "template": {
            "name": "template4",  
            "language": {
                "code": "pt_BR"  
            },
            "components": [
                {
                    "type": "body",
                    "parameters": [
                        {"type": "text", "text": nome},
                        {"type": "text", "text": data},
                        {"type": "text", "text": local}
                    ]
                }
            ]
        }
    }

    response = requests.post(url, headers=headers, json=message_data)

    if response.status_code == 200:
        print("Template 4 enviado com sucesso!")
        #save_message_to_firestore("15551910903", "sent" ,nome, data, local, "sent")
        save_message_to_firestore(event_id, "15551910903", "sent", "5511950404471", "message_text", "button_payload", "", "",  
        event_data['data'],        
        event_data['local'],   
        event_data['nome'])
        #save_message_to_firestore("15551910903", "sent", "5511950404471", nome=nome, data=data, local=local, event_id=event_id)
    else:
        print("Erro ao enviar Template 4:", response.json())







@app.route('/webhook', methods=['GET', 'POST'])
def webhook():
    if request.method == 'GET':
        token = request.args.get('hub.verify_token')
        if token == "elmano":
            return request.args.get('hub.challenge')
        else:
            return 'Token inválido', 403
    elif request.method == 'POST':
        data = request.get_json()

        if data.get("entry"):
            for entry in data["entry"]:
                if "changes" in entry:
                    for change in entry["changes"]:
                        if "messages" in change["value"]:
                            for message in change["value"]["messages"]:
                                sender_id = message["from"]
                                #sender_id = message["from"]  # Número do remetente
                                recipient_id = change["value"].get("metadata", {}).get("display_phone_number")   
                                message_text = message.get("text", {}).get("body", "")
                                # Verificar se há um botão
                                if "button" in message:
                                    button_payload = message["button"].get("payload")
                                    if button_payload:
                                        print(f"Payload do botão recebido: {button_payload}")
                                        #save_message_to_firestore(sender_id, "received", button_payload=button_payload)
                                        save_message_to_firestore(event_id, sender_id, "received", recipient_id, message_text, button_payload, evento=None, data=data, hora=None, local=None, nome=None)
                                        # Lógica com base no payload do botão
                                        reply_to_whatsapp_message(event_id, sender_id, button_payload)
                                        # Continuar a lógica com base no payload
                                        if user_state.get(sender_id) == "awaiting_template2_response" and button_payload == "Tudo certo!":
                                            template3(event_id, sender_id, "Tudo certo!")
                                            user_state[sender_id] = "awaiting_template3_response"
                                        elif user_state.get(sender_id) == "awaiting_template3_response":
                                            template4(event_id,sender_id)
                                            user_state[sender_id] = None
                                        #if user_state.get(sender_id) == "awaiting_template2_response":
                                            #if button_payload == "Sim":
                                                #reply_to_whatsapp_message(sender_id, "Sim")
                                            #elif button_payload == "Não":
                                                #reply_to_whatsapp_message(sender_id, "Não")
                                            #user_state[sender_id] = "awaiting_template2_response"
                                else:
                                    message_text = message.get("text", {}).get("body", "").lower()
                                    #save_message_to_firestore(sender_id, "received", message_text=message_text)
                                    #save_message_to_firestore(sender_id, "received", recipient_id, message_text=message_text)
                                    save_message_to_firestore(event_id, sender_id, "received", recipient_id, message_text, evento=None, data=data, hora=None, local=None, nome=None)
                                    reply_to_whatsapp_message(sender_id, message_text)

        return jsonify({"status": "received"}), 200

if __name__ == "__main__":
    event_id = "2"
    send_message_to_whatsapp(event_id)
    app.run(debug=False, port=5000)




        
        