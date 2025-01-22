from turtle import update
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
access_token = "EAATXaSQjmX8BOZBAYCOgoZAQqPhrYK60jKqViKvh0ckEgbqjc8hsuLjJwic701dUUufYI4Gs00G5zmqdWOCAHUZCvZCMaNd1OhoFguacoQcqNCOhAE3D1td5Yswfe2HOhtrtU1LttjcR9KKMkTLtkZAEEW9aHSkMQIO14coAVMG8OFRAwQoCe7RzelNvQ9L8kzPK7rKe0hIWAVN27g5g3GgkgeZCIzt4ujrQQZD"
phone_number_id = "434398029764267"

# Armazenamento do estado da conversa para cada usuário
user_state = {}


def serialize_firestore_field(value):
    if isinstance(value, DatetimeWithNanoseconds):
        return value.isoformat()
    return value


def convert_to_local(dt):
    local_tz = pytz.timezone("America/Sao_Paulo")
    if isinstance(dt, DatetimeWithNanoseconds):
        return dt.astimezone(local_tz).strftime("%H:%M")
    return ""

def convert_to_local_date(dt):
    local_tz = pytz.timezone("America/Sao_Paulo")
    if isinstance(dt, DatetimeWithNanoseconds):
        return dt.astimezone(local_tz).strftime("%d/%m/%Y")  # Formato dia/mês/ano
    return ""


def pegar_dados_evento(event_id):
    try:
        # Referência ao documento no Firestore
        doc_ref = db.collection("evento").document(event_id)
        doc = doc_ref.get()

        if doc.exists:
            data = doc.to_dict()
            print("Dados do evento encontrados:", data)

        
            # Retornar os dados do evento com a formatação necessária
            return {
                "evento": data.get("evento", ""),
                "data": convert_to_local_date(data.get("data")),
                "inicio": convert_to_local(data.get("inicio")),
                "termino": convert_to_local(data.get("término")),
                "local": data.get("local", ""),
                "instituicao":  data.get("instituição", ""),
                "voluntarios": data.get("voluntarios", []),
            }
        
        else:
            print("Documento do evento não encontrado!")
            return None

    except Exception as e:
        print(f"Erro ao buscar dados no Firestore: {e}")
        return None






def buscar_voluntarios(voluntarios, instituicao_evento, evento_data, evento_inicio):
    
    local_tz = pytz.timezone("America/Sao_Paulo")

    try:
        voluntarios_nome = []
        voluntarios_processados = set()  

        for i, voluntario in enumerate(voluntarios):
            if isinstance(voluntario, dict):  # Verificar se é um dicionário   
                habilidade = voluntario.get("habilidade", "")

                # Buscar na coleção "voluntários" com a mesma instituição e habilidade
                query = (
                    db.collection("voluntários")
                    .where("habilidades", "array_contains", habilidade)
                    .where("instituicao", "==", instituicao_evento)
                    .get()
                )

                for query_doc in query:
                    voluntario_doc = query[0].to_dict()
                    voluntario_id = query[0].id 

                    if voluntario_id in voluntarios_processados:
                        continue

                    numero_celular = voluntario_doc.get("nº celular", "Não encontrado")
                    datas_disponiveis = voluntario_doc.get("datas", [])  # Lista ou único timestamp
                    
                    # Exibindo dados para depuração
                    print(f"Voluntário: {voluntario_doc.get('nome', 'Não encontrado')}")
                    print(f"Datas disponíveis: {datas_disponiveis}")
                    print(f"Evento - Data: {evento_data}, Início: {evento_inicio}")
                    
                    # Comparar as datas disponíveis com a data e hora do evento
                    horario_correspondente = None
                    
                    # Convertendo a data e hora do evento para o fuso horário local
                    evento_data_local = datetime.strptime(evento_data, "%d/%m/%Y").date()
                    evento_inicio_local = datetime.strptime(evento_inicio, "%H:%M").time()

                    # Verificando se datas_disponiveis é uma lista
                    if isinstance(datas_disponiveis, list):  
                        print(f"Datas disponíveis são uma lista. Verificando correspondência...")
                        for data in datas_disponiveis:
                            if isinstance(data, DatetimeWithNanoseconds):
                                # Convertendo cada data para o fuso horário local
                                data_local = data.astimezone(local_tz)  # Para usar o mesmo fuso horário da comparação
                                data_convertida = data_local.date()
                                horario_convertido = data_local.time().replace(microsecond=0)  # Ignorando nanosegundos
                                
                                # Verificando a correspondência entre a data e o horário
                                if data_convertida == evento_data_local and horario_convertido == evento_inicio_local:
                                    horario_correspondente = data
                                    print(f"Correspondência encontrada para: {data_convertida} - {horario_convertido}")
                                    break  # Encontrou correspondência, sai do loop
                                else:
                                    print(f"Sem correspondência para: {data_convertida} - {horario_convertido}")
                    else:
                        print(f"Datas disponíveis não são uma lista. Verificando única data...")
                        # Se for um único Timestamp
                        if isinstance(datas_disponiveis, DatetimeWithNanoseconds):  
                            data_local = datas_disponiveis.astimezone(local_tz)
                            data_convertida = data_local.date()
                            horario_convertido = data_local.time().replace(microsecond=0)  # Ignorando nanosegundos
                            
                            if data_convertida == evento_data_local and horario_convertido == evento_inicio_local:
                                horario_correspondente = datas_disponiveis
                                print(f"Correspondência encontrada para: {data_convertida} - {horario_convertido}")

                    if horario_correspondente:  # Se houver uma correspondência
                        if voluntario_id not in voluntarios_processados:
                            voluntarios_nome.append({
                                "nome": voluntario_doc.get("nome", ""),
                                "id": voluntario_id,
                                "habilidade": habilidade,
                                "numero_celular": numero_celular
                            })
                            voluntarios_processados.add(voluntario_id)
                        else:
                            print(f"Voluntário '{voluntario_doc.get('nome', 'Não encontrado')}' já foi adicionado.")
                    else:
                        print(f"Voluntário '{voluntario_doc.get('nome', 'Não encontrado')}' indisponível para a data e horário do evento.")
                else:
                    voluntarios_nome.append({
                        "nome": "Não encontrado",
                        "habilidade": habilidade,
                        "numero_celular": "Não encontrado"
                    })
            else: 
                print(f"Voluntário no índice {i} não é um dicionário válido!")

        return voluntarios_nome

    except Exception as e:
        print(f"Erro ao buscar voluntários disponíveis no Firestore: {e}")
        return []






def atualizar_voluntarios(event_id, voluntarios):
    try:
        # Referência ao documento no Firestore
        doc_ref = db.collection("evento").document(event_id)
        doc = doc_ref.get()

        if doc.exists:
            data = doc.to_dict()
            voluntarios_atualizados = []

            if "voluntarios" in data:
                for i, voluntario in enumerate(voluntarios):
                    if not isinstance(voluntario, dict):
                        print(f"Erro: Voluntário no índice {i} não é um dicionário válido: {voluntario}")
                        continue

                    habilidade = voluntario.get("habilidade", "")
                    instituicao_evento = data.get("instituição", "")

                    # Buscar na coleção 'voluntários' por documentos com a mesma habilidade e instituição
                    query = (
                        db.collection("voluntários")
                        .where("habilidades", "array_contains", habilidade)
                        .where("instituicao", "==", instituicao_evento)
                        .get()
                    )

                    if query:
                        voluntario_doc = query[0].to_dict()
                        voluntario_id = query[0].id  # ID do voluntário encontrado

                        # Atualizar apenas o campo 'id' no voluntário correspondente
                        voluntario["id"] = voluntario_id

                    else:
                        voluntario["id"] = "Não encontrado"

                    # Adicionar o voluntário ao array atualizado
                    voluntarios_atualizados.append(voluntario)

                # Atualizar o array de voluntários no Firestore com os dados modificados
                doc_ref.update({"voluntarios": voluntarios_atualizados})

                print("Voluntários atualizados:", voluntarios_atualizados)

            else:
                print("Nenhum voluntário encontrado no evento.")

        else:
            print("Documento do evento não encontrado!")

    except Exception as e:
        print(f"Erro ao atualizar voluntários no Firestore: {e}")

            

# Função para salvar mensagens no Firestore com campos separados
def save_message_to_firestore(event_id,sender_id, message_type, recipient_id, message_text, button_payload, evento, data, inicio, termino, local, nome_message, area, **kwargs):
    
    try:

        doc_ref = db.collection("mensagens").document()
        message_data = {
            "sender_id": sender_id,
            "recipient_id": recipient_id or "",
            "evento": evento,
            "data": data,
            "inicio": inicio,
            "termino": termino,
            "local": local,
            "event_id": event_id,
            "message_text": message_text,
            "button_payload": button_payload,  # Salvando o payload do botão
            "type": message_type,  # "received" ou "sent"
            "timestamp": firestore.SERVER_TIMESTAMP,
            "nome_voluntario": nome_message,
            "area": area
        }

        # Aqui você pode tratar os voluntários dinamicamente
        if "voluntarios_nome" in kwargs:
            voluntarios = kwargs["voluntarios_nome"]
            habilidade_count = {}  # Dicionário para contar voluntários por habilidade

            for voluntario in voluntarios:
                # Verificar se o voluntário tem os campos esperados
                habilidade = voluntario.get("habilidade")
                nome = voluntario.get("nome", "Não encontrado")

                if habilidade:
                    # Incrementar o contador de voluntários por habilidade
                    habilidade_count[habilidade] = habilidade_count.get(habilidade, 0) + 1
                    index = habilidade_count[habilidade]

                    # Salvar o nome do voluntário no campo específico
                    message_data[f"voluntario_{habilidade}_{index}_nome"] = nome
                    # Salvar o ID do voluntário no campo específico
                    message_data[f"voluntario_{habilidade}_{index}_id"] = voluntario.get("id", "")

            
        # Salvando a mensagem no Firestore
        doc_ref.set(message_data)
        print("Mensagem salva no Firestore!")
    except Exception as e:
        print(f"Erro ao salvar no Firestore: {e}")


#função do ranking

   



#Template 1 
def send_message_to_whatsapp(event_id):

    # Buscar os dados do evento no Firestore
    event_data = pegar_dados_evento(event_id)
    if event_data:
        # Buscar voluntários disponíveis com base nos dados do evento
        voluntarios_nome = buscar_voluntarios(
        event_data["voluntarios"],
        event_data["instituicao"], 
        event_data["data"],
        event_data["inicio"]
        )

        # Atualizar os dados de voluntários no evento, se necessário
        print("Dados do evento:", event_data)
        print("Voluntários disponíveis:", voluntarios_nome)
    else:
        print("Não foi possível obter os dados do evento.")
        return



    # Variáveis do evento
    evento = event_data["evento"]
    data = event_data["data"]
    inicio = event_data["inicio"]
    termino = event_data["termino"]
    local = event_data["local"]

    if not all([evento, data, inicio, termino, local]):
        print("Erro: Campos obrigatórios estão faltando.")
        return


    url = f"https://graph.facebook.com/v17.0/{phone_number_id}/messages"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    for voluntario in voluntarios_nome:
        nome_message = voluntario.get("nome", "Voluntário")
        numero_celular = voluntario.get("numero_celular", "")
        area = voluntario.get("habilidade", "Não especificada")

        if not numero_celular:
            print(f"Erro: Número de celular não encontrado para o voluntário '{nome_message}'.")
            continue

        message_data = {
            "messaging_product": "whatsapp",
            "to": numero_celular,
            "type": "template",
            "template": {
                "name": "template_1_cargo",
                "language": {"code": "pt_BR"},
                "components": [
                    {
                        "type": "body",
                        "parameters": [
                            {"type": "text", "text": evento},
                            {"type": "text", "text": data},
                            {"type": "text", "text": inicio},
                            {"type": "text", "text": local},
                            {"type": "text", "text": nome_message},
                            {"type": "text", "text": termino},
                            {"type": "text", "text": area}
                        ]
                    },
                    {
                        "type": "button",
                        "sub_type": "quick_reply",
                        "index": "0",
                        "parameters": [{"type": "payload", "payload": "sim"}]
                    },
                    {
                        "type": "button",
                        "sub_type": "quick_reply",
                        "index": "1",
                        "parameters": [{"type": "payload", "payload": "nao"}]
                    }
                ]
            }
        }

        # Enviar mensagem para o voluntário
        response = requests.post(url, headers=headers, json=message_data)
        if response.status_code == 200:
            print(f"Mensagem enviada para '{nome_message}' com sucesso!")
            
            # Salvar no Firestore
            save_message_to_firestore(event_id, "15551910903", "sent", numero_celular, 
                                    "message_text", "button_payload", event_data['evento'], 
                                    event_data['data'], event_data['inicio'], event_data['termino'],
                                    event_data['local'], nome_message=nome_message, area=area)
            
            
            # Atualizar os dados do evento no Firestore
            atualizar_voluntarios(event_id, voluntarios_nome)
        else:
            print(f"Erro ao enviar mensagem para '{nome_message}':", response.json())


# Template 2
def reply_to_whatsapp_message(event_id, recipient_id, button_payload):

    # Buscar os dados do evento no Firestore
    event_data = pegar_dados_evento(event_id)
    if event_data:
        # Buscar voluntários disponíveis com base nos dados do evento
        voluntarios_nome = buscar_voluntarios(
        event_data["voluntarios"],
        event_data["instituicao"]
        )

        # Atualizar os dados de voluntários no evento, se necessário
        print("Dados do evento:", event_data)
        print("Voluntários disponíveis:", voluntarios_nome)
    else:
        print("Não foi possível obter os dados do evento.")
    
    

    # Variáveis do evento
    evento = event_data["evento"]
    data = event_data["data"]
    inicio = event_data["inicio"]
    termino = event_data["termino"]
    local = event_data["local"]

    if not all([evento, data, inicio, termino, local]):
        print("Erro: Campos obrigatórios estão faltando.")
        return
    

    url = f"https://graph.facebook.com/v17.0/{phone_number_id}/messages"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    for voluntario in voluntarios_nome:
        nome_message = voluntario.get("nome", "Voluntário")
        numero_celular = voluntario.get("numero_celular", "")
        area = voluntario.get("habilidade", "Não especificada")

        if not numero_celular:
            print(f"Erro: Número de celular não encontrado para o voluntário '{nome_message}'.")
            continue
    
        message_data = {}

        # Verificar se a mensagem é "sim" 
        if button_payload == "sim":
            message_data = {
                "messaging_product": "whatsapp",
                "to": numero_celular,
                "type": "template",
                "template": {
                    "name": "template_22_cargo",  
                    "language": {
                        "code": "pt_BR"  
                    },
                    "components": [
                        {
                            "type": "body",
                            "parameters": [
                            {"type": "text", "text": nome_message},
                            {"type": "text", "text": data},
                            {"type": "text", "text": inicio},
                            {"type": "text", "text": local},
                            {"type": "text", "text": termino},
                            {"type": "text", "text": area}
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
                "to": numero_celular,
                "type": "text",
                "text": {
                    "body": "Ok. Obrigada pela resposta."
                }
            }

        # Enviar a mensagem
        response = requests.post(url, headers=headers, json=message_data)

        if response.status_code == 200 and button_payload == "sim":
            print("Resposta enviada com sucesso!")
            save_message_to_firestore(event_id, "15551910903", "sent", numero_celular, "message_text", "button_payload",
            "",    
            event_data['data'], 
            event_data['inicio'],
            event_data['termino'],
            event_data['local'], 
            nome_message=nome_message, area=area)

            atualizar_voluntarios(event_id, voluntarios_nome)

        elif response.status_code == 200 and button_payload == "nao":
            print("Resposta de agradecimento enviada com sucesso!")
            save_message_to_firestore("15551910903", "sent", numero_celular, message_text="Ok. Obrigada pela resposta.")
        else:
            print("Erro ao enviar a resposta:", response.json())



# Template 3
def template3(event_id, recipient_id, message_text):

    
    # Buscar os dados do evento no Firestore
    event_data = pegar_dados_evento(event_id)
    if event_data:
        # Buscar voluntários disponíveis com base nos dados do evento
        voluntarios_nome = buscar_voluntarios(
        event_data["voluntarios"],
        event_data["instituicao"]
        )

        # Atualizar os dados de voluntários no evento, se necessário
        print("Dados do evento:", event_data)
        print("Voluntários disponíveis:", voluntarios_nome)
    else:
        print("Não foi possível obter os dados do evento.")

    

    # Variáveis do evento
    evento = event_data["evento"]
    data = event_data["data"]
    inicio = event_data["inicio"]
    termino = event_data["termino"]
    local = event_data["local"]


    if not all([evento, data, inicio, termino, local]):
        print("Erro: Campos obrigatórios estão faltando.")
        return
    

    url = f"https://graph.facebook.com/v17.0/{phone_number_id}/messages"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    for voluntario in voluntarios_nome:
        nome_message = voluntario.get("nome", "Voluntário")
        numero_celular = voluntario.get("numero_celular", "")
        area = voluntario.get("habilidade", "Não especificada")

        if not numero_celular:
            print(f"Erro: Número de celular não encontrado para o voluntário '{nome_message}'.")
            continue


        # Verificar se a mensagem é "Tudo certo!" 
        if message_text.lower() in ["tudo certo!"]:
            message_data = {
            "messaging_product": "whatsapp",
            "to": numero_celular,
            "type": "template",
            "template": {
                "name": "template_3_cargo",  
                "language": {
                    "code": "pt_BR"  
                },
                "components": [
                    {
                        "type": "body",
                        "parameters": [
                        {"type": "text", "text": nome_message}, 
                        {"type": "text", "text": data},
                        {"type": "text", "text": inicio},
                        {"type": "text", "text": local},
                        {"type": "text", "text": termino},
                        {"type": "text", "text": area}
                        ]
                    }
                ]
            }
        }
            
        else:
            message_data = {
                "messaging_product": "whatsapp",
                "to": numero_celular,
                "type": "text",
                "text": {
                    "body": "Ok. Obrigada pela resposta."
                }
            }

        

        response = requests.post(url, headers=headers, json=message_data)

        if response.status_code == 200:
            print("Resposta enviada com sucesso!")
            save_message_to_firestore(event_id, "15551910903", "sent", numero_celular, "message_text", "button_payload",
            "",    
            event_data['data'], 
            event_data['inicio'],
            event_data['termino'],
            event_data['local'], 
            nome_message=nome_message, area=area)

            atualizar_voluntarios(event_id, voluntarios_nome)
        else:
            print("Erro ao enviar a resposta:", response.json())



# Template 4
def template4(event_id, recipient_id):

    # Buscar os dados do evento no Firestore
    event_data = pegar_dados_evento(event_id)
    if event_data:
        # Buscar voluntários disponíveis com base nos dados do evento
        voluntarios_nome = buscar_voluntarios(
        event_data["voluntarios"],
        event_data["instituicao"]
        )

        # Atualizar os dados de voluntários no evento, se necessário
        print("Dados do evento:", event_data)
        print("Voluntários disponíveis:", voluntarios_nome)
    else:
        print("Não foi possível obter os dados do evento.")
    

    # Variáveis do evento
    evento = event_data["evento"]
    data = event_data["data"]
    inicio = event_data["inicio"]
    termino = event_data["termino"]
    local = event_data["local"]


    if not all([evento, data, inicio, termino, local]):
        print("Erro: Campos obrigatórios estão faltando.")
        return


    url = f"https://graph.facebook.com/v17.0/{phone_number_id}/messages"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    for voluntario in voluntarios_nome:
        nome_message = voluntario.get("nome", "Voluntário")
        numero_celular = voluntario.get("numero_celular", "")
        area = voluntario.get("habilidade", "Não especificada")

        if not numero_celular:
            print(f"Erro: Número de celular não encontrado para o voluntário '{nome_message}'.")
            continue

        message_data = {
            "messaging_product": "whatsapp",
            "to": numero_celular,  
            "type": "template",
            "template": {
                "name": "template_4_cargo",  
                "language": {
                    "code": "pt_BR"  
                },
                "components": [
                    {
                        "type": "body",
                        "parameters": [
                        {"type": "text", "text": nome_message},
                        {"type": "text", "text": inicio},
                        {"type": "text", "text": local}, 
                        {"type": "text", "text": termino},
                        {"type": "text", "text": area}
                        ]
                    }
                ]
            }
        }

        response = requests.post(url, headers=headers, json=message_data)

        if response.status_code == 200:
            print("Template 4 enviado com sucesso!")
            
            save_message_to_firestore(event_id, "15551910903", "sent", numero_celular, "message_text", "button_payload", 
            "",  "",
            event_data['inicio'],
            event_data['termino'],       
            event_data['local'],   
            nome_message=nome_message, area=area)
            
            atualizar_voluntarios(event_id, voluntarios_nome)

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
                                recipient_id = change["value"].get("metadata", {}).get("display_phone_number")   
                                message_text = message.get("text", {}).get("body", "")
                                # Verificar se há um botão
                                if "button" in message:
                                    button_payload = message["button"].get("payload")
                                    if button_payload:
                                        print(f"Payload do botão recebido: {button_payload}")
                                        save_message_to_firestore(event_id, sender_id, "received", recipient_id, message_text, button_payload, evento=None, data=data, inicio=None, termino=None, local=None, nome_message=None, area=None)
                                        # Lógica com base no payload do botão
                                        reply_to_whatsapp_message(event_id, sender_id, button_payload)
                                        # Continuar a lógica com base no payload
                                        if user_state.get(sender_id) == "awaiting_template2_response" and button_payload == "Tudo certo!":
                                            template3(event_id, sender_id, "Tudo certo!")
                                            user_state[sender_id] = "awaiting_template3_response"
                                        elif user_state.get(sender_id) == "awaiting_template3_response":
                                            template4(event_id,sender_id)
                                            user_state[sender_id] = None
                                else:
                                    message_text = message.get("text", {}).get("body", "").lower()
                                    save_message_to_firestore(event_id, sender_id, "received", recipient_id, message_text, button_payload, evento=None, data=data, inicio=None, termino=None, local=None, nome_message=None, area=None)
                                    reply_to_whatsapp_message(sender_id, message_text)

        return jsonify({"status": "received"}), 200


if __name__ == "__main__":
    event_id = "8"
    send_message_to_whatsapp(event_id)
    app.run(debug=False, port=5000)



