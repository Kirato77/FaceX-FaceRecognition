from utilitaire.face_recognition_utils import studentsImgToFaceData


def update_face_data(supabase, email):
    face_data = [studentsImgToFaceData(supabase, email)]

    try:
        print(f"Données faciales pour {email} avant mise à jour : {face_data}")
        response = supabase.rpc(
            "update_face_data", {"user_email": email, "new_face_data": face_data}
        ).execute()

        if response.data is None:
            raise Exception(
                f"Erreur lors de la mise à jour des données faciales pour {email}."
            )

        return face_data

    except Exception as e:
        print(f"Erreur lors de l'exécution de la procédure stockée pour {email}: {e}")
        return None
