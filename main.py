import cv2
from datetime import datetime, timedelta
from config.env_loader import load_env_variables
from database.supabase_client import create_supabase_client
from database.attendance import (
    getActiveClassStudentsFaceData,
    getAttendanceForBlock,
    postStudentAttendanceDB,
)
from utilitaire.face_data_utils import checkFaceDataValidity, normalize
from utilitaire.face_recognition_utils import recognize_faces
from database.face_data import update_face_data

# from utilitaire.lcd import lcd_init, lcd_set_cursor, lcd_write
# import RPi.GPIO as GPIO
import time


def get_student_name(supabase, email):
    response = supabase.rpc("get_user_by_email", {"user_email": email}).execute()

    if response.data and "first_name" in response.data and "last_name" in response.data:
        return f"{response.data['first_name']} {response.data['last_name']}"
    else:
        return "Inconnu"


def main():
    env_vars = load_env_variables()
    supabase = create_supabase_client(env_vars["DB_URL"], env_vars["DB_KEY"])

    block_id, face_db = getActiveClassStudentsFaceData(supabase, env_vars["LOCAL"])
    print(
        f"Vous êtes dans le local : {env_vars['LOCAL']} avec un block_id : {block_id}"
    )

    if face_db == None:
        print("Il y a pas cours dans ce local actuellement")
        time.sleep(10)
        main()

    print("Vérification initiale des face data...")
    for email in face_db:
        # print(f"Vérification des données pour {email}: {face_db[email]}")
        try:
            student_name = (
                f"{face_db[email]['first_name']} {face_db[email]['last_name']}"
            )
            face_data = face_db[email].get("face_data")

            if not face_data or len(face_data) == 0:
                print(
                    f"Aucune donnée faciale trouvée pour {student_name}. Tentative de mise à jour..."
                )
                updated_face_data = update_face_data(supabase, email)
                if updated_face_data:
                    face_db[email]["face_data"] = updated_face_data
                    print(f"Données faciales mises à jour pour {student_name}.")
                else:
                    print(
                        f"Échec de la mise à jour des données faciales pour {student_name}."
                    )
            else:
                print(f"Données faciales déjà présentes pour {student_name}.")
        except KeyError as e:
            print(f"Clé manquante pour {email}: {e}")
        except Exception as e:
            print(f"Erreur inattendue pour {email}: {e}")
    print("Vérification terminée.")

    existing_attendance = getAttendanceForBlock(supabase, block_id)

    try:
        cam = cv2.VideoCapture(0)

        if not cam.isOpened():
            raise Exception("Impossible d'accéder à la camera")
        print("Webcam démarrée")
    except Exception as e:
        print(f"Erreur avec la camera : {e}")
        return

    last_block_check_time = datetime.now()
    block_change_check_interval = timedelta(minutes=5)

    while True:
        try:
            if datetime.now() - last_block_check_time > block_change_check_interval:
                block_id = getActiveClassStudentsFaceData(supabase, env_vars["LOCAL"])[
                    0
                ]
                existing_attendance = getAttendanceForBlock(supabase, block_id)
                last_block_check_time = datetime.now()

            try:
                success, img = cam.read()
                if not success:
                    print("Erreur de lecture de la webcam.")
                    raise SystemError("Erreur de lecture de la webcam.")
            except SystemError as e:
                print(f"Erreur avec la camera : {e}")
                break

            recognize_faces(img, face_db, existing_attendance, supabase, block_id)

        except Exception as e:
            print(
                f"Erreur lors du traitement de l'image ou de la reconnaissance faciale : {e}"
            )
            break

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    cam.release()


if __name__ == "__main__":
    main()
