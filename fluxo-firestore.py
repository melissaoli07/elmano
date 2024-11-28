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
access_token = "EAATXaSQjmX8BO1KE0fczIRNjk5HZCz5piPr3zJnGqKvTWZBzJU9rrkeJTFB7AcgrDDAMHRTfRDgPgBiaDTZCE0jT7gDBSaOH8YpmlKBU1m20EyfwFcMWZBIVLcUqXfHk39jkbu9u8Jmx6lGwNHTmvPpe9ONPxZBjbDly8fsOki6zFOEXs7g4BlW1CsLWZCWamZATsaxcZCTKWfQvJAQSDZBfVGssk6bfZBEKnZBbScZD"
phone_number_id = "434398029764267"

# Armazenamento do estado da conversa para cada usuário
user_state = {}

evento = "Culto"
data = "15"
hora = "20"
local = "Auditório 1"
nome = "Carlos"

# Função para salvar mensagens no Firestore com campos separados
def save_message_to_firestore(sender_id, message_type, recipient_id,**kwargs):
    try:
        evento = kwargs.get("evento", "")
        data = kwargs.get("data", "")
        hora = kwargs.get("hora", "")
        local = kwargs.get("local", "")
        nome = kwargs.get("nome", "")
        message_text = kwargs.get("message_text", "")
        button_payload = kwargs.get("button_payload", "")  # Adiciona este campo





        doc_ref = db.collection("mensagens").document()
        doc_ref.set({
            "sender_id": sender_id,
            "recipient_id": recipient_id or "",
            "evento": evento,
            "data": data,
            "hora": hora,
            "local": local,
            "nome": nome,
            "message_text": message_text,
            "button_payload": button_payload,  # Salvando o payload do botão
            "type": message_type,  # "received" ou "sent"
            "timestamp": firestore.SERVER_TIMESTAMP
        })
        print("Mensagem salva no Firestore!")
    except Exception as e:
        print(f"Erro ao salvar no Firestore: {e}")



#Template 1
def send_message_to_whatsapp():
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
        save_message_to_firestore("15551910903", "sent", "5511950404471", evento=evento, data=data, hora=hora, local=local, nome=nome)
    else:
        print("Erro ao enviar a mensagem inicial:", response.json())


# Template 2
def reply_to_whatsapp_message(recipient_id, button_payload):
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
        save_message_to_firestore("15551910903", "sent", "5511950404471", nome=nome, data=data, hora=hora, local=local)
    elif response.status_code == 200 and button_payload == "nao":
        print("Resposta de agradecimento enviada com sucesso!")
        save_message_to_firestore("15551910903", "sent", "5511950404471", message_text="Ok. Obrigada pela resposta.")
    else:
        print("Erro ao enviar a resposta:", response.json())



# Template 3
def template3(recipient_id, message_text):
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
        save_message_to_firestore("15551910903", "sent", "5511950404471", nome=nome, data=data, hora=hora, local=local)
    else:
        print("Erro ao enviar a resposta:", response.json())



# Template 4
def template4(recipient_id):
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
        save_message_to_firestore("15551910903", "sent", "5511950404471", nome=nome, data=data, local=local)
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
                                sender_id = message["from"]  # Número do remetente
                                recipient_id = change["value"].get("metadata", {}).get("display_phone_number")   
                                message_text = message.get("text", {}).get("body", "")
                                # Verificar se há um botão
                                if "button" in message:
                                    button_payload = message["button"].get("payload")
                                    if button_payload:
                                        print(f"Payload do botão recebido: {button_payload}")
                                        #save_message_to_firestore(sender_id, "received", button_payload=button_payload)
                                        save_message_to_firestore(sender_id, "received", recipient_id, button_payload=button_payload)
                                        # Lógica com base no payload do botão
                                        reply_to_whatsapp_message(sender_id, button_payload)
                                        # Continuar a lógica com base no payload
                                        if user_state.get(sender_id) == "awaiting_template2_response" and button_payload == "Tudo certo!":
                                            template3(sender_id, "Tudo certo!")
                                            user_state[sender_id] = "awaiting_template3_response"
                                        elif user_state.get(sender_id) == "awaiting_template3_response":
                                            template4(sender_id)
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
                                    save_message_to_firestore(sender_id, "received", recipient_id, message_text=message_text)
                                    reply_to_whatsapp_message(sender_id, message_text)

        return jsonify({"status": "received"}), 200

if __name__ == "__main__":
    send_message_to_whatsapp()
    app.run(debug=False, port=5000)





         
   
         
        
            
        
    


        
            
        
    


    


            
        
    


        
    



            
        