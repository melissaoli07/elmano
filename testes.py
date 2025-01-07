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
access_token = "EAATXaSQjmX8BO0gPOrqsl5kYK2wMmvu8iDrzxl5UtcQOy595WQT8kLCp7iW7QyrxPUrmiP1j1WqemcqbyVujSRmMIFNYXwZCuP7gOILN4yKu412yGQeO3vZBP7nAPZA4uvXmfj7D6qRBnjxyZCByh8pjuZBKP0R1IHDVpEWKHLbbZCvqvlZBikdERXzhjBZCy4mf7llfJ0UJVbp0vHYH8E6cobubSvKPsZAHMxYb6"
phone_number_id = "434398029764267"

# Armazenamento do estado da conversa para cada usuário
user_state = {}


def serialize_firestore_field(value):
    if isinstance(value, DatetimeWithNanoseconds):
        return value.isoformat()
    return value

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

            voluntarios_nome = []
            if "voluntarios" in data:
                for i, voluntario in enumerate(data["voluntarios"]):
                    habilidade = voluntario.get("habilidade", "")
                    instituicao_evento = data.get("instituição", "")

                    # Buscar na coleção 'voluntarios' por documentos com a mesma habilidade e instituição
                    query = (
                        db.collection("voluntários")
                        .where("habilidades", "array_contains", habilidade)
                        .where("instituicao", "==", instituicao_evento)
                        .get()
                    )

                    if query:
                        voluntario_doc = query[0].to_dict()
                        voluntario_id = query[0].id  # ID do voluntário encontrado

                        voluntarios_nome.append({
                            "nome": voluntario_doc.get("nome", ""),
                            "id": voluntario_id,
                        })
                    else:
                        voluntarios_nome.append({
                            "nome": "Não encontrado",
                        })

                print("Voluntários:", voluntarios_nome)
            else:
                print("Nenhum voluntário encontrado no evento.")

            # Retornar os dados do evento com a formatação necessária
            return {
                "evento": data.get("evento", ""),
                "data": convert_to_local_date(data.get("data")),
                "inicio": convert_to_local(data.get("inicio")),
                "termino": convert_to_local(data.get("termino")),
                "local": data.get("local", ""),
                "instituicao": instituicao_evento,
                "voluntarios": voluntarios_nome
            }
        
        else:
            print("Documento do evento não encontrado!")
            return None

    except Exception as e:
        print(f"Erro ao buscar dados no Firestore: {e}")
        return None



def update_voluntarios(event_id, voluntarios):
    try:
        # Referência ao documento no Firestore
        doc_ref = db.collection("evento").document(event_id)
        doc = doc_ref.get()

        if doc.exists:
            data = doc.to_dict()
            voluntarios_atualizados = []

            if "voluntarios" in data:
                for i, voluntario in enumerate(voluntarios):
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

               

         




if __name__ == "__main__":
    event_id = "8"
    get_event_data(event_id)
    voluntarios = [
    {"habilidade": "corte", "id": "voluntario1_id"},
    {"habilidade": "som", "id": "voluntario2_id"}
    ]
    update_voluntarios(event_id, voluntarios)
    app.run(debug=False, port=5000)