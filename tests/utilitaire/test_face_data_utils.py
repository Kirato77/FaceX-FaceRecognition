from unittest import TestCase
import json
import copy
from utilitaire.face_recognition_utils import recognize_faces, studentsImgToFaceData
from database.supabase_client import create_supabase_client
from config.env_loader import load_env_variables
from utilitaire.face_data_utils import checkFaceDataValidity


class Test_checkFaceDataValidity(TestCase):
    def setUp(self):
        env_vars = load_env_variables()
        self.supabase = create_supabase_client(env_vars["DB_URL"], env_vars["DB_KEY"])
        self.person = "gaetan.carbonnelle1@gmail.com"

        with open(r"tests\test_data\data_test.json", "r") as file:
            content = file.read()
            data = json.loads(content)
            self.face_db = data.get("face_db", [])
            self.existing_attendance = data.get("existing_attendance", [])

    def test_checkFaceDataValidity_valid(self):
        # tout devrait bien se passer
        self.assertTrue(
            checkFaceDataValidity(
                self.supabase, self.person, self.face_db[self.person][0], self.face_db
            ),
            "Test_checkFaceDataValidity : la face_data de test n'est plus valide",
        )

    def test_checkFaceDataValidity_error(self):
        bad_embedding_len = copy.copy(self.face_db[self.person][0])
        bad_embedding_len.pop()
        bad_embedding_bad_data = copy.copy(self.face_db[self.person][0])
        bad_embedding_bad_data[5] = "tres"
        person = "Inexistant@test.com"

        print(
            checkFaceDataValidity(
                self.supabase, self.person, bad_embedding_len, self.face_db
            )
        )
        # bad len
        self.assertFalse(
            checkFaceDataValidity(
                self.supabase, self.person, bad_embedding_len, self.face_db
            ),
            "Test_checkFaceDataValidity : l'embeding est trop court",
        )

        # bad data
        self.assertFalse(
            checkFaceDataValidity(
                self.supabase, self.person, bad_embedding_bad_data, self.face_db
            ),
            "Test_checkFaceDataValidity : pas de bonne embeding dans les données",
        )

        # no data for person
        self.assertFalse(
            checkFaceDataValidity(
                self.supabase, person, self.face_db[self.person][0], self.face_db
            ),
            "Test_checkFaceDataValidity : la personne ne devrait pas etre trouvé",
        )
