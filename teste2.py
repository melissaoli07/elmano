from turtle import update
import requests
from flask import Flask, request, jsonify
from flask_cors import CORS
from google.cloud import firestore
import os
from google.cloud.firestore_v1._helpers import DatetimeWithNanoseconds
from datetime import datetime
import uuid
import pytz

import sys
sys.stdout.reconfigure(encoding='utf-8')

# Inicializar Firestore
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "firebase-key.json"
db = firestore.Client()


app = Flask(__name__)
CORS(app)

# Variáveis
access_token = "EAATXaSQjmX8BO8Je3yQSc3gckypOXh6vOyYd8sowuffBJwCQW9rZA2kr9vR33ETiJMsILDuAUcL6LZAq9lR1SsLjDH30YDfZBItiVYTohPIH5BvLEBT0M4tZB0ZBDXftxd1IjzxOGiXZAmqNYDeSs3r36iXGOnL0p2k31H4ehJIgc9MdbcvA7G2FdBHa8WsUZBmZBDkzwsFNZCaNHeMPW8g5s20nF2mZCc6Ki3YY6LYQZDZD"
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
                "data": convert_to_local_date(data.get("inicio")),
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

                voluntario_encontrado = False

                #for query_doc in query:
                    #voluntario_doc = query[0].to_dict()
                    #voluntario_id = query[0].id 
                for query_doc in query:
                    voluntario_doc = query_doc.to_dict()
                    voluntario_id = query_doc.id


                    if voluntario_id in voluntarios_processados:
                        continue

                    numero_celular = voluntario_doc.get("nº celular", "Não encontrado")
                    datas_disponiveis = voluntario_doc.get("datas", [])  # Lista ou único timestamp
                    
                    # Exibindo dados para depuração
                    print(f"Voluntário: {voluntario_doc.get('nome', 'Não encontrado')}")
                    print(f"Datas disponíveis: {datas_disponiveis}")
                    print(f"Evento - Data: {evento_data}, Início: {evento_inicio}")
                    
                    # Convertendo a data e hora do evento para o fuso horário local
                    evento_data_local = datetime.strptime(evento_data, "%d/%m/%Y").date()
                    evento_inicio_local = datetime.strptime(evento_inicio, "%H:%M").time()               


                    # Comparar as datas disponíveis com a data e hora do evento
                    horario_correspondente = None
                    

                    # Verificando se datas_disponiveis é uma lista
                    if isinstance(datas_disponiveis, list):  
                        print(f"Datas disponíveis são uma lista. Verificando correspondência...")
                        for data in datas_disponiveis:
                            if isinstance(data, DatetimeWithNanoseconds):
                                # Convertendo cada data para o fuso horário local
                                data_local = data.astimezone(local_tz)  # Para usar o mesmo fuso horário da comparação
                                if data_local.date() == evento_data_local and data_local.time().replace(microsecond=0) == evento_inicio_local:
                                    horario_correspondente = data
                                    break
                    elif isinstance(datas_disponiveis, DatetimeWithNanoseconds):
                        data_local = datas_disponiveis.astimezone(local_tz)
                        if data_local.date() == evento_data_local and data_local.time().replace(microsecond=0) == evento_inicio_local:
                            horario_correspondente = datas_disponiveis

                    if horario_correspondente:  
                            voluntarios_nome.append({
                                "nome": voluntario_doc.get("nome", ""),
                                "id": voluntario_id,
                                "habilidade": habilidade,
                                "numero_celular": numero_celular
                            })
                            voluntarios_processados.add(voluntario_id)
                            voluntario_encontrado = True
                            break
                if not voluntario_encontrado:
                    # Nenhum voluntário disponível para essa habilidade
                    voluntarios_nome.append({
                        "nome": "Não encontrado",
                        "id": "Não encontrado",
                        "habilidade": habilidade,
                        "numero_celular": "Não encontrado"
                    })  
            else:
                print(f"Voluntário no índice {i} não é um dicionário válido!")
        return voluntarios_nome
                    
    except Exception as e:
        print(f"Erro ao buscar voluntários disponíveis no Firestore: {e}")
        return []



'''

def atualizar_voluntarios2(event_id, voluntarios):  
    try:
        doc_ref = db.collection("evento").document(event_id)
        doc = doc_ref.get()

        if not doc.exists:
            print("Documento do evento não encontrado!")
            return

        data = doc.to_dict()
        event_data = pegar_dados_evento(event_id)

        if not event_data:
            print("Dados do evento não encontrados!")
            return

        voluntarios_nome = buscar_voluntarios(
            event_data["voluntarios"],
            event_data["instituicao"], 
            event_data["data"],
            event_data["inicio"]
        )

        voluntarios_existentes = data.get("voluntarios", [])

        if not voluntarios_existentes:
            print("Nenhum voluntário encontrado no evento.")
            return

        instituicao_evento = data.get("instituição", "")

        # Criar cópia para evitar sobrescrita da lista original
        voluntarios_atualizados = voluntarios_nome.copy()
        voluntarios_nao_encontrados = []  # Lista para armazenar os voluntários "Não encontrado"
        
        # Contagem de "Não encontrado"
        for v_registro in voluntarios_atualizados:
            if v_registro.get("id") == "Não encontrado":
                voluntarios_nao_encontrados.append(v_registro)

        # Se houver voluntários "Não encontrado", faça as atualizações necessárias
        if voluntarios_nao_encontrados:
            print(f"Encontrados {len(voluntarios_nao_encontrados)} voluntários 'Não encontrado'.")
            
            for i, v_registro in enumerate(voluntarios_atualizados):
                id_atual = v_registro.get("id", "")
                habilidade = v_registro.get("habilidade", "")
                
                # Atualiza apenas voluntários "Não encontrado"
                if id_atual == "Não encontrado":
                    query = (
                        db.collection("voluntários")
                        .where("habilidades", "array_contains", habilidade)
                        .where("instituicao", "==", instituicao_evento)
                        .get()
                    )

                    id_encontrado = "Não encontrado"
                    nome = v_registro.get("nome", "Não encontrado")
                    numero_celular = v_registro.get("numero_celular", "Não encontrado")

                    if query:
                        for q_doc in query:
                            voluntario_doc = q_doc.to_dict()

                            if (
                                voluntario_doc.get("nome") == nome
                                and voluntario_doc.get("nº celular") == numero_celular
                            ):
                                id_encontrado = q_doc.id
                                break

                    # Atualiza o voluntário encontrado na lista
                    voluntarios_atualizados[i] = {
                        "nome": nome,
                        "id": id_encontrado,
                        "habilidade": habilidade,
                        "numero_celular": numero_celular
                    }
                    print(f"Voluntário atualizado: {voluntarios_atualizados[i]}")
        
            # Atualizar no Firestore somente os voluntários que foram alterados (com "Não encontrado")
            for v_registro in voluntarios_atualizados:
                if v_registro.get("id") == "Não encontrado":
                    # Encontra o voluntário correto na lista original
                    index = next(
                        (index for (index, d) in enumerate(voluntarios_existentes) 
                        if d["habilidade"] == v_registro["habilidade"] and d["id"] == "Não encontrado"), 
                        None
                    )
                    if index is not None:
                        # Atualiza apenas o voluntário correspondente
                        voluntarios_existentes[index] = v_registro

            # Salvar a lista de voluntários atualizada no Firestore
            doc_ref.update({"voluntarios": voluntarios_existentes})
            print("Atualização salva no Firestore!")

        else:
            print("Nenhum voluntário com ID 'Não encontrado'. Nenhuma atualização necessária.")

    except Exception as e:
        print(f"Erro ao atualizar voluntários no Firestore: {e}")
    
'''


    

def atualizar_voluntarios(event_id, voluntarios):
    try:
        # Referência ao documento no Firestore
        doc_ref = db.collection("evento").document(event_id)
        doc = doc_ref.get()

        if doc.exists:
            data = doc.to_dict()
            voluntarios_existentes = data.get("voluntarios", [])

            if not voluntarios_existentes:
                print("Nenhum voluntário encontrado no evento.")
                return

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

                id_encontrado = "Não encontrado"

                if query:
                    for q_doc in query:
                        voluntario_doc = q_doc.to_dict()
                        if (
                            voluntario_doc.get("nome") == voluntario.get("nome")
                            and voluntario_doc.get("nº celular") == voluntario.get("numero_celular")
                        ):
                            id_encontrado = q_doc.id
                            nome = voluntario_doc.get("nome")
                            numero_celular = voluntario_doc.get("nº celular")
                            break
                
                # Atualizar o id no voluntário correto dentro do array existente
                for v in voluntarios_existentes:
                    if v.get("habilidade") == habilidade and not v.get("id"):
                        v["id"] = id_encontrado
                        v["nome"] = nome
                        v["numero_celular"] = numero_celular
                        break  # Para não modificar outros registros com a mesma habilidade

            # Atualizar no Firestore apenas os IDs dos voluntários
            doc_ref.update({"voluntarios": voluntarios_existentes})

            print("Voluntários atualizados:", voluntarios_existentes)

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
        #cloud_function_url = "http://127.0.0.1:5001/elmano-escala/us-central1/webhook?event_id=8"
        #response = requests.post(cloud_function_url, headers=headers, json={"message_data": message_data})
        if response.status_code == 200:

            print(f"Mensagem enviada para '{nome_message}' com sucesso!")
            
            # Salvar no Firestore
            save_message_to_firestore(event_id, "15551910903", "sent", numero_celular, 
                                    "message_text", "button_payload", event_data['evento'], 
                                    event_data['data'], event_data['inicio'], event_data['termino'],
                                    event_data['local'], nome_message=nome_message, area=area)
            
            
            

        else:
            print(f"Erro ao enviar mensagem para '{nome_message}':", response.json())
'''

# Template 2
def reply_to_whatsapp_message(event_id, recipient_id, button_payload):

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
    
    

    # Variáveis do evento
    evento = event_data["evento"]
    data = event_data["data"]
    inicio = event_data["inicio"]
    termino = event_data["termino"]
    local = event_data["local"]

    if not all([evento, data, inicio, termino, local]):
        print("Erro: Campos obrigatórios estão faltando.")
        return

    # Se for a primeira mensagem (estado inicial), associar o voluntário ao recipient_id
    if recipient_id not in user_state:
        voluntario_atual = next(
            (vol for vol in voluntarios_nome if vol.get("numero_celular") == recipient_id),
            None
        )
        if not voluntario_atual:
            print(f"Erro: Voluntário com número {recipient_id} não encontrado na lista.")
            return

        # Armazenar os dados do voluntário no estado
        user_state[recipient_id] = {
            "state": "awaiting_template1_response",
            "voluntario": voluntario_atual
        }
    else:
        # Recuperar os dados do voluntário a partir do estado
        #voluntario_atual = user_state[recipient_id].get("voluntario")
        #if not voluntario_atual:
         #   print(f"Erro: Dados do voluntário não encontrados para o número {recipient_id}.")
          #  return
        
        # Recuperar os dados do voluntário a partir do estado
        recipient_state = user_state.get(recipient_id)
        if isinstance(recipient_state, dict):
            voluntario_atual = recipient_state.get("voluntario")
        else:
            print(f"Erro: Formato inesperado em user_state para o número {recipient_id}.")
            return
    


    nome_message = voluntario_atual.get("nome", "Voluntário")
    numero_celular = voluntario_atual.get("numero_celular", "")
    area = voluntario_atual.get("habilidade", "Não especificada")

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
        user_state[recipient_id] = {
            "state": "awaiting_template2_response",
            "voluntario": voluntario_atual
        }

            
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
    #cloud_function_url = "http://127.0.0.1:5001/elmano-escala/us-central1/webhook?event_id=8"
    #response = requests.post(cloud_function_url, headers=headers, json={"message_data": message_data})

    if response.status_code == 200 and button_payload == "sim":

        print("Resposta enviada com sucesso!")
        save_message_to_firestore(event_id, "15551910903", "sent", numero_celular, "message_text", "button_payload",
            "",    
            event_data['data'], 
            event_data['inicio'],
            event_data['termino'],
            event_data['local'], 
            nome_message=nome_message, area=area)

        #atualizar_voluntarios(event_id, voluntarios_nome)

    elif response.status_code == 200 and button_payload == "nao":
        print("Resposta de agradecimento enviada com sucesso!")
        save_message_to_firestore("15551910903", "sent", "", "", "", "", "", "", "", "", "", numero_celular, "Ok. Obrigada pela resposta.")
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
        event_data["instituicao"], 
        event_data["data"],
        event_data["inicio"]
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

    

    # Se for a primeira mensagem (estado inicial), associar o voluntário ao recipient_id
    if recipient_id not in user_state:
        voluntario_atual = next(
            (vol for vol in voluntarios_nome if vol.get("numero_celular") == recipient_id),
            None
        )
        # Verifica se o voluntário foi encontrado
        if not voluntario_atual:
            print(f"Erro: Voluntário com número {recipient_id} não encontrado na lista.")
            return

        # Armazenar os dados do voluntário no estado
        user_state[recipient_id] = {
            "state": "awaiting_template3_response",
            "voluntario": voluntario_atual
        }
    
    else:
        recipient_state = user_state.get(recipient_id)
        
        # Verificar se é um dicionário com as chaves esperadas
        if isinstance(recipient_state, dict) and "voluntario" in recipient_state:
            voluntario_atual = recipient_state.get("voluntario")
        else:
            print(f"Erro: Formato inesperado em user_state para o número {recipient_id}.")
            print(f"Dados em user_state: {recipient_state}")
            return
    

    nome_message = voluntario_atual.get("nome", "Voluntário")
    numero_celular = voluntario_atual.get("numero_celular", "")
    area = voluntario_atual.get("habilidade", "Não especificada")
    
    

    url = f"https://graph.facebook.com/v17.0/{phone_number_id}/messages"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }


    
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
                            {"type": "text", "text": termino},
                            {"type": "text", "text": local},
                            {"type": "text", "text": inicio},
                            {"type": "text", "text": area}
                        ]
                    }
                ]
            }
        }
        # Atualizar o estado do usuário para aguardar resposta ao template2
        user_state[recipient_id] = {
            "state": "awaiting_template3_response",
            "voluntario": voluntario_atual
        }
            
            
    elif message_text.lower() in ["não conseguirei estar..."]:
        message_data = {
            "messaging_product": "whatsapp",
            "to": numero_celular,
            "type": "text",
            "text": {
                "body": "Ok. Obrigada pela resposta."
            }
        }

    


    response = requests.post(url, headers=headers, json=message_data)
    #cloud_function_url = "http://127.0.0.1:5001/elmano-escala/us-central1/webhook?event_id=8"
    #response = requests.post(cloud_function_url, headers=headers, json={"message_data": message_data})

    if response.status_code == 200 and message_text.lower() in ["tudo certo!"]:
        print("Resposta enviada com sucesso!")
        save_message_to_firestore(event_id, "15551910903", "sent", numero_celular, "message_text", "button_payload",
        "",    
        event_data['data'], 
        event_data['inicio'],
        event_data['termino'],
        event_data['local'], 
        nome_message=nome_message, area=area)

        #atualizar_voluntarios(event_id, voluntarios_nome)
    elif response.status_code == 200 and message_text.lower() in ["não conseguirei estar..."]:
        print("Resposta de agradecimento enviada com sucesso!")
        save_message_to_firestore("15551910903", "sent", "", "", "", "", "", "", "", "", "", numero_celular, "Ok. Obrigada pela resposta.")

    else:
        print("Erro ao enviar a resposta:", response.json())



# Template 4
def template4(event_id, recipient_id, message_text):

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
    

    # Variáveis do evento
    evento = event_data["evento"]
    data = event_data["data"]
    inicio = event_data["inicio"]
    termino = event_data["termino"]
    local = event_data["local"]


    if not all([evento, data, inicio, termino, local]):
        print("Erro: Campos obrigatórios estão faltando.")
        return


    


    # Se for a primeira mensagem (estado inicial), associar o voluntário ao recipient_id
    if recipient_id not in user_state:
        voluntario_atual = next(
            (vol for vol in voluntarios_nome if vol.get("numero_celular") == recipient_id),
            None
        )
        # Verifica se o voluntário foi encontrado
        if not voluntario_atual:
            print(f"Erro: Voluntário com número {recipient_id} não encontrado na lista.")
            return

        # Armazenar os dados do voluntário no estado
        user_state[recipient_id] = {
            "state": "awaiting_template3_response",
            "voluntario": voluntario_atual
        }
    
    else:
        recipient_state = user_state.get(recipient_id)
        
        # Verificar se é um dicionário com as chaves esperadas
        if isinstance(recipient_state, dict) and "voluntario" in recipient_state:
            voluntario_atual = recipient_state.get("voluntario")
        else:
            print(f"Erro: Formato inesperado em user_state para o número {recipient_id}.")
            print(f"Dados em user_state: {recipient_state}")
            return


    nome_message = voluntario_atual.get("nome", "Voluntário")
    numero_celular = voluntario_atual.get("numero_celular", "")
    area = voluntario_atual.get("habilidade", "Não especificada")

    url = f"https://graph.facebook.com/v17.0/{phone_number_id}/messages"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }

        
    if message_text.lower() in ["tudo certo!"]:
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

    elif message_text.lower() in ["não conseguirei..."]:
        message_data = {
            "messaging_product": "whatsapp",
            "to": numero_celular,
            "type": "text",
            "text": {
                "body": "Ok. Obrigada pela resposta."
            }
        }


    response = requests.post(url, headers=headers, json=message_data)
    #cloud_function_url = "http://127.0.0.1:5001/elmano-escala/us-central1/webhook?event_id=8"
    #response = requests.post(cloud_function_url, headers=headers, json={"message_data": message_data})


    if response.status_code == 200 and message_text.lower() in ["tudo certo!"]:
        print("Template 4 enviado com sucesso!")
            
        save_message_to_firestore(event_id, "15551910903", "sent", numero_celular, "message_text", "button_payload", 
        "",  "",
        event_data['inicio'],
        event_data['termino'],       
        event_data['local'],   
        nome_message=nome_message, area=area)
            
       
        atualizar_voluntarios(event_id, [voluntario_atual])
        
    elif response.status_code == 200 and message_text.lower() in ["não conseguirei..."]:
        print("Resposta de agradecimento enviada com sucesso!")
        save_message_to_firestore("15551910903", "sent", "", "", "", "", "", "", "", "", "", numero_celular, "Ok. Obrigada pela resposta.")


    else:
        print("Erro ao enviar Template 4:", response.json())
'''


if __name__ == "__main__":
    event_id = "8"
    send_message_to_whatsapp(event_id)
    app.run(debug=False, port=5000)
