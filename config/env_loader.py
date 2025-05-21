import os
from dotenv import load_dotenv


def load_env_variables():
    # charger les variables d'environement
    try:
        load_dotenv()
    except Exception as e:
        print(f"Erreur lors du chargement des variables d'environement : {e}")
        return None

    try:
        db_url = os.getenv("DB_URL")
        db_key = os.getenv("DB_KEY")
        db_jwt = os.getenv("DB_JWT")
        local = os.getenv("LOCAL")

        # check qu'elles existe
        if not db_url:
            raise ValueError("la variable d'environnement 'DB_URL' est manquante")
        if not db_key:
            raise ValueError("la variable d'environnement 'DB_KEY' est manquante")
        if not db_jwt:
            raise ValueError("la variable d'environnement 'DB_JWT' est manquante")
        if not local:
            raise ValueError("la variable d'environnement 'LOCAL' est manquante")

        return {
            "DB_URL": db_url,
            "DB_KEY": db_key,
            "DB_JWT": db_jwt,
            "LOCAL": local,
        }

    except ValueError as ve:
        print(f"erreur :  {ve}")
        return None
