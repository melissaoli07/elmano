import requests
from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# Variáveis
access_token = "EAATXaSQjmX8BOxG2XQWnZClZCYsgQhEoxGxve3BteeMEjuuohZAn2eZCKIL9wrlVW5kcqTYIL3kqC3fGmzattosCJm3Hssl9i5Qf904DHWF5Qfs8KMjwdootm2t4PnDUDAtgLz0C9HfHZC1gOTsNJINJ13DrDzuZBuZAtxTQrgSNai28kFWT2FCyjEO68xPYjiB8C92vQ4ZAxE46ZBuOIoZBDWKKTqprK1wL87mzsZD"
phone_number_id = "434398029764267"

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

    # Verificar se a mensagem é "sim" ou "topo" 
    if message_text.lower() in ["sim", "topo"]:
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

# Endpoint para receber mensagens do webhook
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
                            message_text = message.get("text", {}).get("body", "")
                            print(f"Mensagem recebida: {message_text}")
 
                            reply_to_whatsapp_message(sender_id, message_text)
        
        return jsonify({"status": "received"}), 200

if __name__ == "__main__":
    send_message_to_whatsapp()
    app.run(debug=False, port=5000)
