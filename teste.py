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
# Definição de variáveis de configuração (substitua pelos valores reais)
access_token = "EAATXaSQjmX8BO1KE0fczIRNjk5HZCz5piPr3zJnGqKvTWZBzJU9rrkeJTFB7AcgrDDAMHRTfRDgPgBiaDTZCE0jT7gDBSaOH8YpmlKBU1m20EyfwFcMWZBIVLcUqXfHk39jkbu9u8Jmx6lGwNHTmvPpe9ONPxZBjbDly8fsOki6zFOEXs7g4BlW1CsLWZCWamZATsaxcZCTKWfQvJAQSDZBfVGssk6bfZBEKnZBbScZD"
phone_number_id = "434398029764267"

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

# Função para salvar a mensagem no Firestore
def save_message_to_firestore(sender, status, recipient, evento, data, hora, local, nome):
    try:
        # Referência à coleção de mensagens
        doc_ref = db.collection("mensagens").document()
        doc_ref.set({
            #"sender_id": sender_id,
            #"recipient_id": recipient_id or "",
            "evento": evento,
            "data": data,
            "hora": hora,
            "local": local,
            "nome": nome,
            #"message_text": message_text,
            #"button_payload": button_payload,  # Salvando o payload do botão
            #"type": message_type,  # "received" ou "sent"
            "timestamp": firestore.SERVER_TIMESTAMP
        })
        print("Mensagem salva com sucesso!")
    except Exception as e:
        print(f"Erro ao salvar a mensagem no Firestore: {e}")

# Função para enviar mensagem via WhatsApp
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

    # URL e cabeçalhos para a API do WhatsApp
    url = f"https://graph.facebook.com/v17.0/{phone_number_id}/messages"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    # Dados da mensagem
    message_data = {
        "messaging_product": "whatsapp",
        "to": "5511950404471",  # Número de telefone do destinatário
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
                    "type": "button",
                    "sub_type": "quick_reply",
                    "index": "0",
                    "parameters": [
                        {"type": "payload", "payload": "sim"}
                    ]
                },
                {
                    "type": "button",
                    "sub_type": "quick_reply",
                    "index": "1",
                    "parameters": [
                        {"type": "payload", "payload": "nao"}
                    ]
                }
            ]
        }
    }

    # Enviar a mensagem
    response = requests.post(url, headers=headers, json=message_data)

    if response.status_code == 200:
        print("Template 1 enviado com sucesso!")
        save_message_to_firestore("15551910903", "sent", "5511950404471", **event_data)
    else:
        print("Erro ao enviar a mensagem inicial:", response.json())

# Rodando o Flask (se necessário)
if __name__ == "__main__":
    event_id = "1"  # Substitua pelo ID real
    send_message_to_whatsapp(event_id)
    # app.run(debug=False, port=5000)  # Se estiver usando o Flask
