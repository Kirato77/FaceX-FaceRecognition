import os
import json
import face_recognition
from supabase import create_client, Client
from dotenv import load_dotenv
from PIL import Image
import io
import numpy as np


def imgToFaceData(img):
    try:
        print(f"Traitement de l'image.")
        # Vérifier que l'image est bien en format RGB (important)
        if img.mode != "RGB":
            img = img.convert("RGB")

        # Traiter l'image en numpy
        img_array = np.array(img)

        # Retrouver les visages
        face_encodings = face_recognition.face_encodings(img_array)

        # Vérifier si un encodage a été extrait
        if len(face_encodings) > 0:
            embedding = face_encodings[0]
            return embedding.tolist()
        else:
            print(f"Aucun encodage extrait pour l'image.")
            return None

    except Exception as e:
        print(f"Erreur lors de l'extraction des encodages : {e}")
        return None


def studentsImgToFaceData(supabase: Client, studentsEmail: str):
    """
    Recoit email d'un étudants et renvoir les face_data de son image stocké dans supabase
    """

    # récuperer matricutle étudiant
    response = supabase.rpc(
        "get_user_by_email",
        {
            "user_email": studentsEmail,
        },
    ).execute()
    matricule = response.data["matricule"]

    # Télécharger l'image binaire depuis le stockage Supabase
    binary_data = supabase.storage.from_("id-pictures").download(
        "students/" + matricule + ".jpg"
    )

    # Créer une image à partir des données binaires
    image = Image.open(io.BytesIO(binary_data))
    # image.show()

    # Extraire les données du visage
    encodings = imgToFaceData(image)
    if encodings:
        return encodings
    else:
        print("Aucun encodage trouvé pour cet étudiant.")


def UpdateAllFaceData(supabase: Client):
    """
    update dans la DB toutes les face_data des users étudiants à partir de leur image qui se trouve dans le bucket
    """
    reponse = supabase.rpc("get_all_users").execute()
    # print(reponse.data)

    for i in reponse.data:
        if i["role"] == "student":
            print("Au tour de : " + i["email"])
            faceData = [studentsImgToFaceData(supabase, i["email"])]
            response = supabase.rpc(
                "update_face_data",
                {"user_email": i["email"], "new_face_data": faceData},
            ).execute()


def UpdateOneFaceData(supabase: Client, email):
    """
    update dans la DB une seul face_data à partir de l'email de étudiant
    """
    print(f"update de la photo de : {email} sur base de celle dans la DB")

    faceData = [studentsImgToFaceData(supabase, email)]
    response = supabase.rpc(
        "update_face_data", {"user_email": email, "new_face_data": faceData}
    ).execute()

    print(f"update fini pour la face_data de : {email}")

    return faceData
