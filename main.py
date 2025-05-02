import cv2
import time
from datetime import datetime, timedelta
from config.env_loader import load_env_variables
from database.supabase_client import create_supabase_client
from database.attendance import (
    getActiveClassStudentsFaceData,
    getAttendanceForBlock,
)
from utilitaire.face_recognition_utils import recognize_faces
from database.face_data import update_face_data
from Silent_Face_Anti_Spoofing.test import test


def get_student_name(db, email):
    """Get student's full name from email."""
    resp = db.rpc("get_user_by_email", {"user_email": email}).execute()

    if resp.data and "first_name" in resp.data and "last_name" in resp.data:
        return f"{resp.data['first_name']} {resp.data['last_name']}"
    return "Unknown"


def verify_face_data(email, face_db, db):
    """Verify and update student's face data if needed."""
    try:
        name = f"{face_db[email]['first_name']} {face_db[email]['last_name']}"
        face_data = face_db[email].get("face_data")

        if not face_data or len(face_data) == 0:
            print(f"No face data for {name}. Updating...")
            new_data = update_face_data(db, email)

            if new_data:
                face_db[email]["face_data"] = new_data
                print(f"Face data updated for {name}")
            else:
                print(f"Failed to update face data for {name}")
        else:
            print(f"Face data exists for {name}")

    except KeyError as e:
        print(f"Missing key for {email}: {e}")
    except Exception as e:
        print(f"Error for {email}: {e}")


def init_camera():
    """Initialize camera connection."""
    try:
        cam = cv2.VideoCapture(0)
        if not cam.isOpened():
            raise Exception("Cannot access camera")
        print("Camera started")
        return cam
    except Exception as e:
        print(f"Camera error: {e}")
        return None


def main():
    # Init environment and DB
    env = load_env_variables()
    db = create_supabase_client(env["DB_URL"], env["DB_KEY"])

    # Get class info
    block_id, face_db = getActiveClassStudentsFaceData(db, env["LOCAL"])
    print(f"Room: {env['LOCAL']} | Block ID: {block_id}")

    # Check active class
    if face_db is None:
        print("No active class")
        time.sleep(10)
        main()
        return

    # Verify face data
    print("Verifying face data...")
    for email in face_db:
        verify_face_data(email, face_db, db)
    print("Verification complete")

    # Init attendance
    attendance = getAttendanceForBlock(db, block_id)

    # Start camera
    cam = init_camera()
    if not cam:
        return

    # Init timing
    last_check = datetime.now()
    CHECK_INTERVAL = timedelta(minutes=5)
    FRAME_INTERVAL = 0.5  # 0.5 seconds between frames (2 frames per second)
    last_frame_time = time.time()

    # Main loop
    while True:
        try:
            current_time = time.time()
            
            # Only process frame every FRAME_INTERVAL seconds
            if current_time - last_frame_time < FRAME_INTERVAL:
                if cv2.waitKey(1) & 0xFF == ord("q"):
                    break
                continue
                
            last_frame_time = current_time

            # Check block changes
            now = datetime.now()
            if now - last_check > CHECK_INTERVAL:
                block_id, _ = getActiveClassStudentsFaceData(db, env["LOCAL"])
                attendance = getAttendanceForBlock(db, block_id)
                last_check = now

            # Get frame
            try:
                ok, frame = cam.read()
                if not ok:
                    print("Camera read failed")
                    raise SystemError("Camera error")
            except SystemError as e:
                print(f"Camera error: {e}")
                break

            # Check if the frame is real
            label = test(
                image=frame,
                model_dir="Silent_Face_Anti_Spoofing/resources/anti_spoof_models",
                device_id=0
                )

            if label == 1:
                print("Real frame")
                # Process faces
                recognize_faces(frame, face_db, attendance, db, block_id)
            else:
                print("Fake frame")

        except Exception as e:
            print(f"Recognition error: {e}")
            break

        # Check quit
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    # Cleanup
    cam.release()


if __name__ == "__main__":
    main()
