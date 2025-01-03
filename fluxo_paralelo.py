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
access_token = "EAATXaSQjmX8BO0gPOrqsl5kYK2wMmvu8iDrzxl5UtcQOy595WQT8kLCp7iW7QyrxPUrmiP1j1WqemcqbyVujSRmMIFNYXwZCuP7gOILN4yKu412yGQeO3vZBP7nAPZA4uvXmfj7D6qRBnjxyZCByh8pjuZBKP0R1IHDVpEWKHLbbZCvqvlZBikdERXzhjBZCy4mf7llfJ0UJVbp0vHYH8E6cobubSvKPsZAHMxYb6"
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
                "local": data.get("local", ""),
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
def update_event_data(event_id, voluntario_id, campo):
    try:
        # Referência ao documento no Firestore
        doc_ref = db.collection("evento").document(event_id)
        
        # Atualizar apenas o campo especificado
        if campo == "corte":
            doc_ref.update({"voluntario_corte_1": voluntario_id})
        elif campo == "som":
            doc_ref.update({"voluntario_som_1": voluntario_id})
        else:
            print(f"Campo '{campo}' inválido. Use 'corte' ou 'som'.")
            return

        print(f"Campo '{campo}' do evento {event_id} atualizado com sucesso!")
    except Exception as e:
        print(f"Erro ao atualizar dados no Firestore: {e}")


# Função para salvar mensagens no Firestore com campos separados
def save_message_to_firestore(event_id,sender_id, message_type, recipient_id, message_text, button_payload, evento, data, inicio, termino, local, *kwargs):
    
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
            #"voluntario_corte_1": voluntario_corte_1,
            #"voluntario_som_1": voluntario_som_1,
            "event_id": event_id,
            "message_text": message_text,
            "button_payload": button_payload,  # Salvando o payload do botão
            "type": message_type,  # "received" ou "sent"
            "timestamp": firestore.SERVER_TIMESTAMP
        })

        for key, value in kwargs.items():
            # Se o valor for uma lista, converte para string separada por vírgulas
            if isinstance(value, list):
                value = ", ".join(value)
            doc_ref[key] = value

        print("Mensagem salva no Firestore!")
    except Exception as e:
        print(f"Erro ao salvar no Firestore: {e}")




#Template 1 - mandando para 2 ao mesmo tempo mas sendo especificado 
def send_message_to_whatsapp(event_id):
    # Buscar os dados do evento no Firestore
    event_data = get_event_data(event_id)
    if not event_data:
        print("Erro: Não foi possível obter os dados do evento.")
        return

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
    nome_message = ", ".join(voluntario_corte_1)  # Concatena os nomes em uma string
    nome_message2 = ", ".join(voluntario_som_1)

    if not all([evento, data, inicio, termino, local]):
        print("Erro: Campos obrigatórios estão faltando.")
        return


    url = f"https://graph.facebook.com/v17.0/{phone_number_id}/messages"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    message_data_corte = {
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
                    {"type": "text", "text": inicio},
                    {"type": "text", "text": local},
                    {"type": "text", "text": nome_message},
                    {"type": "text", "text": termino} 
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


    message_data_som = {
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
                    {"type": "text", "text": inicio},
                    {"type": "text", "text": local},
                    {"type": "text", "text": nome_message2},
                    {"type": "text", "text": termino} 
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

   
        # Enviar mensagem para Matheus
    response_corte = requests.post(url, headers=headers, json=message_data_corte)
    if response_corte.status_code == 200:
        print(f"Mensagem enviada para '{voluntario_corte_1}' com sucesso!")

        if isinstance(voluntario_corte_1, list):
            voluntario_corte_1 = ", ".join(voluntario_corte_1)
    
        if isinstance(voluntario_som_1, list):
            voluntario_som_1 = ", ".join(voluntario_som_1)

        save_message_to_firestore(event_id, "15551910903", "sent", "5511950404471", "message_text", "button_payload", 
        event_data['evento'],
        event_data['data'],    
        event_data['inicio'],
        event_data['termino'],      
        event_data['local'],
        nome_message, "")

         # Atualizar os dados do evento no Firestore
        voluntario_id = voluntario_corte_1_id[0]
        update_event_data(event_id, voluntario_id, "corte")
    else:
        print(f"Erro ao enviar mensagem para '{voluntario_corte_1}':", response_corte.json())

    # Enviar mensagem para Manoel
    response_som = requests.post(url, headers=headers, json=message_data_som)
    if response_som.status_code == 200:
        print(f"Mensagem enviada para '{voluntario_som_1}' com sucesso!")

        if isinstance(voluntario_corte_1, list):
            voluntario_corte_1 = ", ".join(voluntario_corte_1)
    
    
        if isinstance(voluntario_som_1, list):
            voluntario_som_1 = ", ".join(voluntario_som_1)
            
        save_message_to_firestore(event_id, "15551910903", "sent", "5511950404471", "message_text", "button_payload", 
        event_data['evento'],
        event_data['data'],    
        event_data['inicio'],
        event_data['termino'],      
        event_data['local'],
        "", nome_message2)

        #Ou pro som
        voluntario_id = voluntario_som_1_id[0]
        update_event_data(event_id, voluntario_id, "som")
    else:
        print(f"Erro ao enviar mensagem para '{voluntario_som_1}':", response_som.json())


#Template 1 - mandando so pra um
def send_message_to_whatsapp(event_id):
    # Buscar os dados do evento no Firestore
    event_data = get_event_data(event_id)
    if not event_data:
        print("Erro: Não foi possível obter os dados do evento.")
        return

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
    nome_message = ", ".join(voluntario_corte_1)  # Concatena os nomes em uma string

    if not all([evento, data, inicio, termino, local]):
        print("Erro: Campos obrigatórios estão faltando.")
        return


    url = f"https://graph.facebook.com/v17.0/{phone_number_id}/messages"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

    message_data_corte = {
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
                    {"type": "text", "text": inicio},
                    {"type": "text", "text": local},
                    {"type": "text", "text": nome_message},
                    {"type": "text", "text": termino} 
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


   
        # Enviar mensagem para Matheus
    response_corte = requests.post(url, headers=headers, json=message_data_corte)
    if response_corte.status_code == 200:
        print(f"Mensagem enviada para '{voluntario_corte_1}' com sucesso!")

        if isinstance(voluntario_corte_1, list):
            voluntario_corte_1 = ", ".join(voluntario_corte_1)
    
        if isinstance(voluntario_som_1, list):
            voluntario_som_1 = ", ".join(voluntario_som_1)

        save_message_to_firestore(event_id, "15551910903", "sent", "5511950404471", "message_text", "button_payload", 
        event_data['evento'],
        event_data['data'],    
        event_data['inicio'],
        event_data['termino'],      
        event_data['local'],
        nome_message, "")

         # Atualizar os dados do evento no Firestore
        voluntario_id = voluntario_corte_1_id[0]
        update_event_data(event_id, voluntario_id, "corte")
    else:
        print(f"Erro ao enviar mensagem para '{voluntario_corte_1}':", response_corte.json())


#Template 1 - função send_message_to_whatsapp fazendo por parametro   



def get_voluntarios_by_field(field_name):
    """
    Obtém os voluntários e seus IDs de acordo com o campo especificado no Firestore.
    
    :param field_name: Nome do campo relacionado aos voluntários (ex: 'voluntario_corte_1').
    :return: Uma tupla (voluntarios, ids), onde:
             - voluntarios é uma lista de nomes dos voluntários.
             - ids é uma lista de IDs dos voluntários.
    """
    try:
        # Referência para a coleção de voluntários
        voluntarios_ref = db.collection("voluntários")
        
        # Consulta baseada no campo fornecido
        query = voluntarios_ref.where("field", "==", field_name).stream()
        
        voluntarios = []
        ids = []
        
        # Itera pelos resultados
        for doc in query:
            data = doc.to_dict()
            voluntarios.append(data.get("name"))
            ids.append(doc.id)  # Assume que o ID do documento é o identificador do voluntário
        
        return voluntarios, ids
    
    except Exception as e:
        print(f"Erro ao acessar o Firestore: {e}")
        return [], []







def send_message_to_whatsapp(event_id):
    # Buscar os dados do evento no Firestore
    event_data = get_event_data(event_id)
    if not event_data:
        print("Erro: Não foi possível obter os dados do evento.")
        return

    # Identificar campos relacionados a voluntários
    voluntarios_necessarios = [
        key for key in event_data.keys() if "voluntario" in key.lower()
    ]

    if not voluntarios_necessarios:
        print("Erro: Nenhum campo de voluntário encontrado no evento.")
        return

    # Obter os voluntários necessários de acordo com os campos
    voluntarios_data = {}
    for voluntario_field in voluntarios_necessarios:
        voluntarios, voluntarios_id = get_voluntarios_by_field(voluntario_field)
        if not voluntarios or not voluntarios_id:
            print(f"Erro: Nenhum voluntário encontrado para o campo '{voluntario_field}'.")
            return
        voluntarios_data[voluntario_field] = {
            "names": voluntarios,
            "ids": voluntarios_id
        }

    # Variáveis do evento
    evento = event_data.get("evento")
    data = event_data.get("data")
    inicio = event_data.get("inicio")
    termino = event_data.get("termino")
    local = event_data.get("local")

    if not all([evento, data, inicio, termino, local]):
        print("Erro: Campos obrigatórios estão faltando.")
        return

    # Preparar a mensagem com base nos voluntários identificados
    nomes_voluntarios = ", ".join(
        [", ".join(data["names"]) for data in voluntarios_data.values()]
    )

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
            "language": {"code": "pt_BR"},
            "components": [
                {
                    "type": "body",
                    "parameters": [
                        {"type": "text", "text": evento},
                        {"type": "text", "text": data},
                        {"type": "text", "text": inicio},
                        {"type": "text", "text": local},
                        {"type": "text", "text": nomes_voluntarios},
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

    # Enviar mensagem
    response = requests.post(url, headers=headers, json=message_data)
    if response.status_code == 200:
        print(f"Mensagem enviada para '{nomes_voluntarios}' com sucesso!")

        # Salvar mensagens e atualizar evento
        save_message_to_firestore(
            event_id, "15551910903", "sent", "5511950404471", 
            "message_text", "button_payload", evento, data, inicio, termino, local, 
            nomes_voluntarios, ""
        )

        for field, data in voluntarios_data.items():
            update_event_data(event_id, data["ids"][0], field)
    else:
        print(f"Erro ao enviar mensagem para '{nomes_voluntarios}':", response.json())

        

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
                        {"type": "text", "text": nome_message2},
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
        save_message_to_firestore(event_id, "15551910903", "sent", "5511950404471", "message_text", "button_payload", "",
        event_data['data'],    
        event_data['inicio'], 
        event_data['termino'],
        event_data['local'],
        nome_message2, "")

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
                    {"type": "text", "text": nome_message2}, 
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
        nome_message2,"")
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
        nome_message2,"")
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




        
        