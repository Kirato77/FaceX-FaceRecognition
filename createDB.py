import os
from supabase import create_client, Client
from dotenv import load_dotenv
from utils import UpdateAllFaceData

# Chargement des variables d'environnement
load_dotenv()
DB_URL = os.getenv("DB_URL")
DB_KEY = os.getenv("DB_KEY")
LOCAL = os.getenv("LOCAL")

supabase: Client = create_client(DB_URL, DB_KEY)

UpdateAllFaceData(supabase)
# print(studentsImgToFaceData(supabase,'gaetan.carbonnelle1@gmail.com'))
