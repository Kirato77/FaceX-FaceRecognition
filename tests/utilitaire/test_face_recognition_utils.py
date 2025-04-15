from unittest import TestCase
import cv2
import numpy as np
import json
from utilitaire.face_recognition_utils import recognize_faces, studentsImgToFaceData
from database.supabase_client import create_supabase_client
from config.env_loader import load_env_variables


class Test_studentsImgToFaceData(TestCase):
    def setUp(self):
        """Initialisation des variables de test"""
        env_vars = load_env_variables()
        self.supabase = create_supabase_client(env_vars["DB_URL"], env_vars["DB_KEY"])
        self.email = "gaetan.carbonnelle1@gmail.com"
        self.fake_email = "gaetan.cernauhfesl@gmail.com"
        self.matricule = ""

    def test_studentsImgToFaceData_success(self):
        face_data = studentsImgToFaceData(self.supabase, self.email)
        face_data = np.array(face_data)

        # Check visage existe
        self.assertIsNotNone(
            face_data, "Test_studentsImgToFaceData : Aucun visage détecté"
        )

        # Check longeur data est juste
        self.assertTrue(
            len(face_data) == 128,
            "Test_studentsImgToFaceData : Longeur face_data pas bonne",
        )

        # Check si le tableau à les bonne données
        self.assertTrue(
            np.issubdtype(face_data.dtype, np.number),
            "Test_studentsImgToFaceData : infos dans face_data incorect ",
        )

    def test_studentsImgToFaceData_invalid_email(self):
        face_data = studentsImgToFaceData(self.supabase, self.fake_email)

        # Vérifiez que la fonction retourne bien None pour un email invalide
        self.assertIsNone(
            face_data,
            "Test_studentsImgToFaceData : Il ne devrait pas y avoir d'image pour cet email",
        )


class Test_recognize_faces(TestCase):
    def setUp(self):
        """Initialisation des variables de test"""
        env_vars = load_env_variables()
        self.supabase = create_supabase_client(env_vars["DB_URL"], env_vars["DB_KEY"])
        self.block_id = "4"

        # récup image de test
        with open(r"tests\test_data\img_gaetan.json", "r") as file:
            content = file.read()
            img_data = json.loads(content)
            self.img = np.array(img_data, dtype=np.uint8)

        # récup fake data pour les test
        with open(r"tests\test_data\data_test.json", "r") as file:
            content = file.read()
            data = json.loads(content)
            self.face_db = data.get("face_db", [])
            self.existing_attendance = data.get("existing_attendance", [])

    def test_recognize_faces_succes(self):
        empty_existing_attendance = {"rien@test.com"}

        # Vérifie s'il arrive bien à retrouver le visage et le met présent
        self.assertTrue(
            recognize_faces(
                self.img,
                self.face_db,
                empty_existing_attendance,
                self.supabase,
                self.block_id,
            ),
            "Test_recognize_faces : n'arrive plus à trouver le visage dans l'image",
        )

    def test_recognize_faces_déja_enregisté(self):
        # Vérifie s'il arrive bien à retrouver le visage et à savoir qu'il à déja été enregisté dans la existing_attendance
        self.assertIsNone(
            recognize_faces(
                self.img,
                self.face_db,
                self.existing_attendance,
                self.supabase,
                self.block_id,
            ),
            "Test_recognize_faces : n'arrive plus à voir que le visage est déja enregisté",
        )

    def test_recognize_faces_inconu(self):
        noise = np.random.randint(-100, 100, self.img.shape, dtype="int16")
        noisy_img = cv2.add(self.img.astype("int16"), noise)
        noisy_img = np.clip(noisy_img, 0, 255).astype("uint8")

        # Vérifie s'il arrive bien à retrouver le visage et à savoir qu'il à déja été enregisté dans la existing_attendance
        self.assertFalse(
            recognize_faces(
                noisy_img,
                self.face_db,
                self.existing_attendance,
                self.supabase,
                self.block_id,
            ),
            "Test_recognize_faces : Ne doit trouver personne",
        )
