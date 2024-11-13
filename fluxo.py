import requests
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# Variáveis
access_token = "EAATXaSQjmX8BO6tXZCq9YRxZBv8dwiZCSEJX5S4jJOEj4Kwg6sZBoBAKYeuc7xGajMN5VW9gUEGQhgQU1ebhWwajszDODRShLCMOpqWCoVsLxfZBVZC2PPcWQKbRQrZB1Rx0RZCMftjpahQKCOM9OgH9ZBA8weyo6Evon1ZBXkOUClgPgG8BTyZA3foLXAXJmtfloipYt75ZAmQ6FmA4UPoEcydn7ygABuHDBFRteQYZD"
phone_number_id = "434398029764267"

# Armazenamento do estado da conversa para cada usuário
user_state = {}

# Template 1
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
                        {"type": "text", "text": "Culto"},
                        {"type": "text", "text": "15"},
                        {"type": "text", "text": "20"},
                        {"type": "text", "text": "Auditório 1"},
                        {"type": "text", "text": "Carlos"}
                    ]
                }
            ]
        }
    }

    response = requests.post(url, headers=headers, json=message_data)

    if response.status_code == 200:
        print("Template 1 enviado com sucesso!")
    else:
        print("Erro ao enviar a mensagem inicial:", response.json())

# Template 2
def reply_to_whatsapp_message(recipient_id, message_text):
    url = f"https://graph.facebook.com/v17.0/{phone_number_id}/messages"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    # Verificar se a mensagem é "Topo!" 
    if message_text.lower() == "topo!":
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
                            {"type": "text", "text": "Carlos"},
                            {"type": "text", "text": "15"},
                            {"type": "text", "text": "20"},
                            {"type": "text", "text": "Auditório 1"}
                        ]
                    }
                ]
            }
        }
        # Atualizar o estado do usuário para aguardar resposta ao template2
        user_state[recipient_id] = "awaiting_template2_response"
        
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
                        {"type": "text", "text": "Carlos"},
                        {"type": "text", "text": "15"},
                        {"type": "text", "text": "20"},
                        {"type": "text", "text": "Auditório 1"}
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
                        {"type": "text", "text": "Carlos"},
                        {"type": "text", "text": "20"},
                        {"type": "text", "text": "Auditório 1"}
                    ]
                }
            ]
        }
    }

    response = requests.post(url, headers=headers, json=message_data)

    if response.status_code == 200:
        print("Template 4 enviado com sucesso!")
    else:
        print("Erro ao enviar Template 4:", response.json())








# Função de verificação do botão e envio do template 3
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
                        if "value" in change and "messages" in change["value"]:
                            message = change["value"]["messages"][0]
                            sender_id = message["from"]

                            # Checar se a mensagem contém um botão e capturar o payload
                            if message.get("button"):
                                button_payload = message["button"].get("payload")
                                print(f"Payload do botão recebido: {button_payload}")

                                # Verifique o payload do botão para continuar a conversa
                                if user_state.get(sender_id) == "awaiting_template2_response" and button_payload == "Tudo certo!":
                                    print(f"Enviando Template 3 para o usuário {sender_id}")
                                    message_text = "Tudo certo!"  # Ou capture a resposta do botão diretamente, se for o caso.
                                    template3(sender_id, message_text)
                                
                                    # Limpar o estado do usuário após enviar o Template 3
                                    user_state[sender_id] = "awaiting_template3_response"

                                elif user_state.get(sender_id) == "awaiting_template3_response":
                                    print(f"Enviando Template 4 para o usuário {sender_id}")
                                    template4(sender_id)
    
                                    # Limpar o estado após enviar o Template 4
                                    user_state[sender_id] = None
                                else:
                                    print(f"O estado do usuário {sender_id} não está correto ou o botão pressionado não corresponde.")
                            else:
                                # Aqui tratamos mensagens digitadas normalmente
                                message_text = message.get("text", {}).get("body", "").lower()
                                print(f"Mensagem recebida: {message_text}")
                                reply_to_whatsapp_message(sender_id, message_text)
        
        return jsonify({"status": "received"}), 200


if __name__ == "__main__":
    send_message_to_whatsapp()
    app.run(debug=False, port=5000)


