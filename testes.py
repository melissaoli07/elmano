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
access_token = "EAATXaSQjmX8BO8IqXLry7NYOD3BboSkTZBIEAS9Lpjmul5TWHDZABFgQ0dpDOq5RZCTMZAOprurOWECkNIU4bNwi1fDeBvvqZBOLCPlvaGD6P6rMO5dn9ds0zNZA9gKEEYpjeIv1uODe1M3EfUOdEIlqBOXOafMW6drewebhaqA0Lwgh36gQJZC8SasGrFIh58G6sLGAfHfBFyK2jaebbN9gsMsiZCK34EPMd9cZD"
phone_number_id = "434398029764267"

# Armazenamento do estado da conversa para cada usuário
user_state = {}


def serialize_firestore_field(value):
    if isinstance(value, DatetimeWithNanoseconds):
        return value.isoformat()
    return value

def pegar_dados_evento(event_id):
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

        
            # Retornar os dados do evento com a formatação necessária
            return {
                "evento": data.get("evento", ""),
                "data": convert_to_local_date(data.get("data")),
                "inicio": convert_to_local(data.get("inicio")),
                "termino": convert_to_local(data.get("término")),
                "local": data.get("local", ""),
                "instituicao":  data.get("instituição", ""),
                "voluntarios": data.get("voluntarios", [])
            }
        
        else:
            print("Documento do evento não encontrado!")
            return None

    except Exception as e:
        print(f"Erro ao buscar dados no Firestore: {e}")
        return None



def buscar_voluntarios(voluntarios, instituicao_evento):
    try:
        voluntarios_nome = []


        for i, voluntario in enumerate(voluntarios):
            if isinstance(voluntario, dict):  # Verificar se é um dicionário   
                habilidade = voluntario.get("habilidade", "")

            
                #buscar na coleçao voluntariso com a mesma instituição e a mesma habilidade
                query = (
                    db.collection("voluntários")
                    .where("habilidades", "array_contains", habilidade)
                    .where("instituicao", "==", instituicao_evento)
                    .get()
                )

                if query:
                    voluntario_doc = query[0].to_dict()
                    voluntario_id = query[0].id 

                    numero_celular = voluntario_doc.get("nº celular", "Não encontrado")

                    voluntarios_nome.append({
                    "nome": voluntario_doc.get("nome", ""),
                    "id": voluntario_id,
                    "habilidade": habilidade,
                    "numero_celular": numero_celular 
                    })
                else:
                    voluntarios_nome.append({
                        "nome": "Não encontrado",
                        "habilidade": habilidade,
                        "numero_celular": "Nao encontrado"
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
def save_message_to_firestore(event_id,sender_id, message_type, recipient_id, message_text, button_payload, evento, data, inicio, termino, local, nome_message, **kwargs):
    
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

        if not numero_celular:
            print(f"Erro: Número de celular não encontrado para o voluntário '{nome_message}'.")
            continue

        message_data = {
            "messaging_product": "whatsapp",
            "to": numero_celular,
            "type": "template",
            "template": {
                "name": "template_11",
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
                            {"type": "text", "text": termino}
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
                                    event_data['local'], nome_message=nome_message)
            
            
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

        if not numero_celular:
            print(f"Erro: Número de celular não encontrado para o voluntário '{nome_message}'.")
            continue
    
        # Verificar se a mensagem é "sim" 
        if button_payload == "sim":
            message_data = {
                "messaging_product": "whatsapp",
                "to": numero_celular,
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
                            {"type": "text", "text": nome_message},
                            {"type": "text", "text": data},
                            {"type": "text", "text": inicio},
                            {"type": "text", "text": local},
                            {"type": "text", "text": termino}
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
            save_message_to_firestore(event_id, "15551910903", "sent", numero_celular, "message_text", "button_payload", "",
            event_data['data'],    
            event_data['inicio'], 
            event_data['termino'],
            event_data['local'],
            "", nome_message)

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
                "name": "template3",  
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
                        {"type": "text", "text": termino}
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
            #save_message_to_firestore("15551910903", "sent", nome, data, hora, local, )
            save_message_to_firestore(event_id, "15551910903", "sent", numero_celular, "message_text", "button_payload", "",
            event_data['data'],    
            event_data['inicio'],  
            event_data['termino'],  
            event_data['local'],
            "", nome_message)

            atualizar_voluntarios(event_id, voluntarios_nome)
        else:
            print("Erro ao enviar a resposta:", response.json())

'''


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
                    {"type": "text", "text": nome_message2},
                    {"type": "text", "text": inicio},
                    {"type": "text", "text": local}, 
                    {"type": "text", "text": termino},
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
        event_data['inicio'],
        event_data['termino'],       
        event_data['local'],   
        "", nome_message2)
        #save_message_to_firestore("15551910903", "sent", "5511950404471", nome=nome, data=data, local=local, event_id=event_id)
    else:
        print("Erro ao enviar Template 4:", response.json())



'''

if __name__ == "__main__":
    event_id = "8"
    send_message_to_whatsapp(event_id)
    app.run(debug=False, port=5000)



