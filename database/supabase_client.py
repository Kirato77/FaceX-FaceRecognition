from supabase import create_client


def create_supabase_client(url, key):
    """
    Création du client supabase affin de lui faire des requètes
    """
    try:
        client = create_client(url, key)
        return client
    except Exception as e:
        print(f"Erreur lors de la création du client supabase : {e}")
        raise
