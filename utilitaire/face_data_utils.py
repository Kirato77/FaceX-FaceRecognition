import numpy as np
from database.face_data import update_face_data


def updateAndValidate(supabase, person, face_db):
    """
    Tente de mettre à jour les données faciales d'une personne.
    """
    face_data = update_face_data(supabase, person)
    if face_data:
        face_db[person] = face_data
        print(f"Données faciales mises à jour pour {person}.")
        return True
    else:
        print(f"Impossible de mettre à jour les données faciales pour {person}.")
        return False


def checkFaceDataValidity(supabase, person, embedding, face_db):
    """
    Vérifie que les données faciales sont valides et met à jour si nécessaire.
    """
    # Vérifier si `face_db[person]` existe et contient des données
    if person not in face_db or not face_db[person]:
        print(
            f"Aucune donnée faciale trouvée pour {person}, tentative de mise à jour..."
        )
        if updateAndValidate(supabase, person, face_db) == False:
            return False

    # Vérifications de validité de l'embedding
    try:
        embedding = np.array(embedding)  # Accès sécurisé
    except Exception as e:
        print(f"Erreur lors de la conversion des données pour {person}: {e}")
        if updateAndValidate(supabase, person, face_db) == False:
            return False

    # données sont bien numérique
    if not np.issubdtype(embedding.dtype, np.number):
        print(f"Données non numériques pour {person}, tentative de mise à jour...")
        if updateAndValidate(supabase, person, face_db) == False:
            return False

    # Bonne longeur des données
    if len(embedding) != 128:
        print(
            f"Longueur incorrecte pour les données de {person}: {len(embedding)}, mise à jour..."
        )
        if updateAndValidate(supabase, person, face_db) == False:
            return False

    return True


def normalize(embedding):
    return embedding / np.linalg.norm(embedding)
