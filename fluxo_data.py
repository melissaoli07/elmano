import requests
from flask import Flask, request, jsonify
from flask_cors import CORS
from google.cloud import firestore
import os
from google.cloud.firestore_v1._helpers import DatetimeWithNanoseconds
from datetime import datetime
import pytz


# Inicializar Firestore
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "firebase-key.json"
db = firestore.Client()


app = Flask(__name__)
CORS(app)

# Variáveis
access_token = "EAATXaSQjmX8BO2FtyfZAYyo5ZCZBtHcV4pkY4qU1mM2YT0fim2uEXmMNFUKPRNuW14INskhIdtZB4uZAFP27uxMDpt7gRbrTsMcQdH6uIZAcb6vniusU0CEhRYL2JuE24L9Smh1cQd1JSaaRDPJTcfIebZBZC8N14XIdzS0izX9h82i2iBBsgjkZBRFZARFSW2bILU1Gxq0h3MQjtHokfZBnhryXh4nA76j8hCjpuMZD"
phone_number_id = "434398029764267"

# Armazenamento do estado da conversa para cada usuário
user_state = {}


def serialize_firestore_field(value):
    if isinstance(value, DatetimeWithNanoseconds):
        return value.isoformat()
    return value



# Função para buscar dados de um evento no Firestore
def get_event_data(event_id):
    try:
        # Referência ao documento no Firestore
        doc_ref = db.collection("evento").document(event_id)
        doc = doc_ref.get()

        if doc.exists:
            data = doc.to_dict()

            local_tz = pytz.timezone("America/Sao_Paulo")

            def convert_to_local(dt):
                if isinstance(dt, DatetimeWithNanoseconds):
                    return dt.astimezone(local_tz).strftime("%H:%M")
                return ""
            
            def convert_to_local_date(dt):
                if isinstance(dt, DatetimeWithNanoseconds):
                    return dt.astimezone(local_tz).strftime("%d/%m/%Y")  # Formato dia/mês/ano
                return ""

            print("Dados do evento encontrados:", data)
            #voluntario_corte_1 = get_nome_from_another_collection()
            voluntario_corte_1 = get_voluntarios_from_instituicao_corte()
            voluntario_som_1 = get_voluntarios_from_instituicao_som()


            return {
                "evento": data.get("evento", ""),
                "data": convert_to_local_date(data.get("data")), 
                "inicio": convert_to_local(data.get("inicio")),
                "termino": convert_to_local(data.get("termino")),
                #"data": data["data"].date().isoformat() if isinstance(data.get("data"), DatetimeWithNanoseconds) else "",
                #"inicio": data["inicio"].time().strftime("%H:%M:%S") if isinstance(data.get("inicio"), DatetimeWithNanoseconds) else "",
                #"termino": data["termino"].time().strftime("%H:%M:%S") if isinstance(data.get("termino"), DatetimeWithNanoseconds) else "",
                "local": data.get("local", ""),
                #"nomes": nomes
                "voluntario_corte_1": voluntario_corte_1,
                "voluntario_som_1": voluntario_som_1
            }
        else:
            print("Documento não encontrado!")
            return None
    except Exception as e:
        print(f"Erro ao buscar dados no Firestore: {e}")
        return None

        


# Função para buscar voluntários da instituição "Batista" e com 'corte' em 'habilidades'
def get_voluntarios_from_instituicao_corte():
    try:
        # Referência à coleção "voluntários"
        voluntarios_ref = db.collection("voluntários")
        # Realizar uma consulta filtrando pela instituição "Batista" e se 'habilidades' contém o valor 'corte'
        docs = voluntarios_ref.where("instituicao", "==", "Batista").where("habilidades", "array_contains", "corte").stream()

        voluntario_corte_1 = []
        voluntario_corte_id = []
        for doc in docs:
            voluntario_data = doc.to_dict()
            nome = voluntario_data.get("nome", "")
            if nome:
                voluntario_corte_1.append(nome)
            voluntario_id = doc.id
            voluntario_corte_id.append(voluntario_id)

        if voluntario_corte_1:
            print(f"Voluntários encontrados na instituição 'Batista' com a habilidade 'corte': {voluntario_corte_1}")
            return voluntario_corte_1, voluntario_corte_id  # Retorna uma lista com os nomes encontrados
        else:
            print("Nenhum voluntário encontrado na instituição 'Batista' com a habilidade 'corte'!")
            return [], []

    except Exception as e:
        print(f"Erro ao buscar voluntários na coleção 'voluntários': {e}")
        return [], []



# Função para buscar voluntários da instituição "Batista" e com 'som' em 'habilidades'
def get_voluntarios_from_instituicao_som():
    try:
        # Referência à coleção "voluntários"
        voluntarios_ref = db.collection("voluntários")
        # Realizar uma consulta filtrando pela instituição "Batista" e se 'habilidades' contém o valor 'corte'
        docs = voluntarios_ref.where("instituicao", "==", "Batista").where("habilidades", "array_contains", "som").stream()

        voluntario_som_1 = []
        voluntario_som_id = []
        for doc in docs:
            voluntario_data = doc.to_dict()
            nome = voluntario_data.get("nome", "")
            if nome:
                voluntario_som_1.append(nome)
            voluntario_id = doc.id
            voluntario_som_id.append(voluntario_id)

        if voluntario_som_1:
            print(f"Voluntários encontrados na instituição 'Batista' com a habilidade 'som': {voluntario_som_1}")
            return voluntario_som_1, voluntario_som_id  # Retorna uma lista com os nomes encontrados
        else:
            print("Nenhum voluntário encontrado na instituição 'Batista' com a habilidade 'som'!")
            return [], []

    except Exception as e:
        print(f"Erro ao buscar voluntários na coleção 'voluntários': {e}")
        return [], []







# Função para atualizar dados de um evento no Firestore
def update_event_data(event_id, voluntario_id):
    try:
        # Referência ao documento no Firestore
        doc_ref = db.collection("evento").document(event_id)
        doc_ref.update({"voluntario_corte_1": voluntario_id})
        doc_ref.update({"voluntario_som_1": voluntario_id})
        print(f"Dados do evento {event_id} atualizados com sucesso!")
    except Exception as e:
        print(f"Erro ao atualizar dados no Firestore: {e}")




# Função para salvar mensagens no Firestore com campos separados
def save_message_to_firestore(event_id,sender_id, message_type, recipient_id, message_text, button_payload, evento, data, inicio, termino, local, voluntario_corte_1, voluntario_som_1):
    
    if isinstance(voluntario_corte_1, list):
        voluntario_corte_1 = ", ".join(voluntario_corte_1)
    
    
    if isinstance(voluntario_som_1, list):
        voluntario_som_1 = ", ".join(voluntario_som_1)
    
    try:

        doc_ref = db.collection("mensagens").document()
        doc_ref.set({
            "sender_id": sender_id,
            "recipient_id": recipient_id or "",
            "evento": evento,
            "data": data,
            "inicio": inicio,
            "termino": termino,
            "local": local,
            #"nome": nome,
            "voluntario_corte_1": voluntario_corte_1,
            "voluntario_som_1": voluntario_som_1,
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

    #event_data_serialized = serialize_firestore_field(event_data)

    #voluntario_corte_1, voluntario_corte_1_id = get_nome_from_another_collection()
    voluntario_corte_1, voluntario_corte_1_id = get_voluntarios_from_instituicao_corte()
    voluntario_som_1, voluntario_som_1_id = get_voluntarios_from_instituicao_som()

    if not voluntario_corte_1 or not voluntario_corte_1_id:
        print("Erro: Nenhum voluntário encontrado.")
        return
    
    if not voluntario_som_1 or not voluntario_som_1_id:
        print("Erro: Nenhum voluntário encontrado.")
        return


    # Variáveis do evento
    evento = event_data["evento"]
    data = event_data["data"]
    inicio = event_data["inicio"]
    termino = event_data["termino"]
    local = event_data["local"]
    voluntario_corte_1 = voluntario_corte_1
    voluntario_som_1 = voluntario_som_1

    if not all([evento, data, inicio, termino, local, voluntario_corte_1]):
        print("Erro: Campos obrigatórios estão faltando.")
        return
    
    if not all([evento, data, inicio, termino, local, voluntario_som_1]):
        print("Erro: Campos obrigatórios estão faltando.")
        return

     # Exemplo de como você pode usar os nomes na mensagem
    nome_message = ", ".join(voluntario_corte_1)  # Concatena os nomes em uma string
    nome_message2 = ", ".join(voluntario_som_1)  # Concatena os nomes em uma string

    todos_voluntarios = voluntario_corte_1 + voluntario_som_1

    for voluntario in todos_voluntarios:
        parameters = [
                {"type": "text", "text": evento},
                {"type": "text", "text": data},
                {"type": "text", "text": inicio},
                {"type": "text", "text": local},
                {"type": "text", "text": voluntario}, # Adiciona o nome do voluntário individualmente
                {"type": "text", "text": termino} 
            ]


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
                    "parameters": parameters
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
        event_data['inicio'],  
        event_data['termino'],    
        event_data['local'],  
        "", "")


        # Atualizar os dados do evento no Firestore
        voluntario_id = voluntario_corte_1_id[0]
        update_event_data(event_id, voluntario_id)

        #Ou pro som
        voluntario_id = voluntario_som_1_id[0]
        update_event_data(event_id, voluntario_id)

    else:
        print("Erro ao enviar a mensagem inicial:", response.json())


# Template 2
def reply_to_whatsapp_message(event_id, recipient_id, button_payload):

    # Buscar os dados do evento no Firestore
    event_data = get_event_data(event_id)
    if not event_data:
        print("Erro: Não foi possível obter os dados do evento.")
        return

    #voluntario_corte_1, voluntario_corte_1_id = get_nome_from_another_collection()
    voluntario_corte_1, voluntario_corte_1_id = get_voluntarios_from_instituicao_corte()
    voluntario_som_1, voluntario_som_1_id = get_voluntarios_from_instituicao_som()

    if not voluntario_corte_1 or not voluntario_corte_1_id:
        print("Erro: Nenhum voluntário encontrado.")
        return
    
    if not voluntario_som_1 or not voluntario_som_1_id:
        print("Erro: Nenhum voluntário encontrado.")
        return
    

    # Variáveis do evento
    evento = event_data["evento"]
    data = event_data["data"]
    inicio = event_data["inicio"]
    termino = event_data["termino"]
    local = event_data["local"]
    voluntario_corte_1 = voluntario_corte_1
    voluntario_som_1 = voluntario_som_1

    if not all([evento, data, inicio, termino, local, voluntario_corte_1]):
        print("Erro: Campos obrigatórios estão faltando.")
        return
    
    if not all([evento, data, inicio, termino, local, voluntario_som_1]):
        print("Erro: Campos obrigatórios estão faltando.")
        return

     # Exemplo de como você pode usar os nomes na mensagem
    nome_message = ", ".join(voluntario_corte_1)  # Concatena os nomes em uma string
    nome_message2 = ", ".join(voluntario_som_1)  # Concatena os nomes em uma string

    todos_voluntarios = voluntario_corte_1 + voluntario_som_1

    for voluntario in todos_voluntarios:
        parameters = [
                {"type": "text", "text": voluntario},
                {"type": "text", "text": data},
                {"type": "text", "text": inicio},
                {"type": "text", "text": local}, 
                {"type": "text", "text": termino} 
            ]

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
                "name": "template_novo_2",  
                "language": {
                    "code": "pt_BR"  
                },
                "components": [
                    {
                        "type": "body",
                        "parameters": parameters
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
        save_message_to_firestore(event_id, "15551910903", "sent", "5511950404471", "message_text", "button_payload", "",
        event_data['data'],    
        event_data['inicio'],
        event_data['termino'],      
        event_data['local'],
        "", "")

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

    #voluntario_corte_1, voluntario_corte_1_id = get_nome_from_another_collection()
    voluntario_corte_1, voluntario_corte_1_id = get_voluntarios_from_instituicao_corte()
    voluntario_som_1, voluntario_som_1_id = get_voluntarios_from_instituicao_som()

    if not voluntario_corte_1 or not voluntario_corte_1_id:
        print("Erro: Nenhum voluntário encontrado.")
        return
    
    if not voluntario_som_1 or not voluntario_som_1_id:
        print("Erro: Nenhum voluntário encontrado.")
        return
    

    # Variáveis do evento
    evento = event_data["evento"]
    data = event_data["data"]
    inicio = event_data["inicio"]
    termino = event_data["termino"]
    local = event_data["local"]
    voluntario_corte_1 = voluntario_corte_1
    voluntario_som_1 = voluntario_som_1

    if not all([evento, data, inicio, termino, local, voluntario_corte_1]):
        print("Erro: Campos obrigatórios estão faltando.")
        return
    
    if not all([evento, data, inicio, termino, local, voluntario_som_1]):
        print("Erro: Campos obrigatórios estão faltando.")
        return

     # Exemplo de como você pode usar os nomes na mensagem
    nome_message = ", ".join(voluntario_corte_1)  # Concatena os nomes em uma string
    nome_message2 = ", ".join(voluntario_som_1)  # Concatena os nomes em uma string


    todos_voluntarios = voluntario_corte_1 + voluntario_som_1

    for voluntario in todos_voluntarios:
        parameters = [
                {"type": "text", "text": voluntario},
                {"type": "text", "text": data},
                {"type": "text", "text": inicio},
                {"type": "text", "text": local}, 
                {"type": "text", "text": termino} 
            ]

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
            "name": "template_novo3",  
            "language": {
                "code": "pt_BR"  
            },
            "components": [
                {
                    "type": "body",
                    "parameters": parameters
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
        event_data['inicio'],  
        event_data['termino'],  
        event_data['local'],
        "","")
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

    #voluntario_corte_1, voluntario_corte_1_id = get_nome_from_another_collection()
    voluntario_corte_1, voluntario_corte_1_id = get_voluntarios_from_instituicao_corte()
    voluntario_som_1, voluntario_som_1_id = get_voluntarios_from_instituicao_som()

    if not voluntario_corte_1 or not voluntario_corte_1_id:
        print("Erro: Nenhum voluntário encontrado.")
        return
    
    if not voluntario_som_1 or not voluntario_som_1_id:
        print("Erro: Nenhum voluntário encontrado.")
        return
    

    # Variáveis do evento
    evento = event_data["evento"]
    data = event_data["data"]
    inicio = event_data["inicio"]
    termino = event_data["termino"]
    local = event_data["local"]
    voluntario_corte_1 = voluntario_corte_1
    voluntario_som_1 = voluntario_som_1

    if not all([evento, data, inicio, termino, local, voluntario_corte_1]):
        print("Erro: Campos obrigatórios estão faltando.")
        return
    
    if not all([evento, data, inicio, termino, local, voluntario_som_1]):
        print("Erro: Campos obrigatórios estão faltando.")
        return

     # Exemplo de como você pode usar os nomes na mensagem
    nome_message = ", ".join(voluntario_corte_1)  # Concatena os nomes em uma string
    nome_message2 = ", ".join(voluntario_som_1)  # Concatena os nomes em uma string

    todos_voluntarios = voluntario_corte_1 + voluntario_som_1

    for voluntario in todos_voluntarios:
        parameters = [
                {"type": "text", "text": voluntario},
                {"type": "text", "text": inicio},
                {"type": "text", "text": local}, 
                {"type": "text", "text": termino} 
            ]


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
            "name": "template_novo4",  
            "language": {
                "code": "pt_BR"  
            },
            "components": [
                {
                    "type": "body",
                    "parameters": parameters
                }
            ]
        }
    }

    response = requests.post(url, headers=headers, json=message_data)

    if response.status_code == 200:
        print("Template 4 enviado com sucesso!")
        #save_message_to_firestore("15551910903", "sent" ,nome, data, local, "sent")
        save_message_to_firestore(event_id, "15551910903", "sent", "5511950404471", "message_text", "button_payload", "", "",  
        event_data['inicio'],
        event_data['termino'],       
        event_data['local'],   
        "","")
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
                                        save_message_to_firestore(event_id, sender_id, "received", recipient_id, message_text, button_payload, evento=None, data=data, inicio=None, termino=None, local=None, voluntario_corte_1=None, voluntario_som_1=None)
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
                                    save_message_to_firestore(event_id, sender_id, "received", recipient_id, message_text, button_payload, evento=None, data=data, inicio=None, termino=None, local=None, voluntario_corte_1=None, voluntario_som_1=None)
                                    reply_to_whatsapp_message(sender_id, message_text)

        return jsonify({"status": "received"}), 200

if __name__ == "__main__":
    event_id = "7"
    send_message_to_whatsapp(event_id)
    app.run(debug=False, port=5000)




        
        