import cv2
import time
import numpy as np
import face_recognition
from datetime import datetime, timedelta
from config.env_loader import load_env_variables
from database.supabase_client import create_supabase_client
from database.attendance import (
    getActiveClassStudentsFaceData,
    getAttendanceForBlock,
    postStudentAttendanceDB,
)
from utilitaire.face_recognition_utils import recognize_faces
from database.face_data import update_face_data
from Silent_Face_Anti_Spoofing.test import test


def get_student_name(db, email):
    """Get student's full name from email."""
    resp = db.rpc("get_user_by_email", {"user_email": email}).execute()
    data = resp.data
    return (
        f"{data['first_name']} {data['last_name']}"
        if data and "first_name" in data
        else "Unknown"
    )


def verify_face_data(email, face_db, db):
    """Verify and update student's face data if needed."""
    try:
        student_data = face_db[email]
        name = f"{student_data['first_name']} {student_data['last_name']}"
        face_data = student_data.get("face_data")

        if not face_data:
            print(f"No face data for {name}. Updating...")
            if new_data := update_face_data(db, email):
                student_data["face_data"] = new_data
                print(f"Face data updated for {name}")
            else:
                print(f"Failed to update face data for {name}")
        else:
            print(f"Face data exists for {name}")

    except Exception as e:
        print(f"Error processing {email}: {e}")


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


def process_frame(frame, face_db, attendance, db, block_id):
    """Process a single frame for face recognition."""
    # Check if frame is real using anti-spoofing
    label = test(
        image=frame,
        model_dir="Silent_Face_Anti_Spoofing/resources/anti_spoof_models",
        device_id=0,
    )

    if label == 1:
        print("Real frame")
        # Try to recognize faces and return both result and recognized email
        result, recognized_email = recognize_faces(frame, face_db, attendance, db, block_id)
        return result, recognized_email
    else:
        print("Fake frame")
        return False, None


def main():
    # Init environment and DB
    env = load_env_variables()
    db = create_supabase_client(env["DB_URL"], env["DB_KEY"])
    local = env["LOCAL"]

    # Define constants
    CHECK_INTERVAL = timedelta(minutes=5)
    FRAME_INTERVAL = 0.2  # Increased frame rate to 5 FPS
    VOTING_THRESHOLD = 3  # Number of consecutive matches required
    ANTI_SPOOF_VOTING_THRESHOLD = 2  # Number of consecutive real frames required

    # Initialize voting counters
    face_recognition_votes = {}
    anti_spoof_votes = 0

    while True:
        # Get class info
        block_id, face_db = getActiveClassStudentsFaceData(db, local)
        print(f"Room: {local} | Block ID: {block_id}")

        if face_db is None:
            print("No active class")
            time.sleep(10)
            continue

        # Verify face data for all students
        print("Verifying face data...")
        for email in face_db:
            verify_face_data(email, face_db, db)
        print("Verification complete")

        # Initialize attendance tracking and camera
        attendance = getAttendanceForBlock(db, block_id)
        if not (cam := init_camera()):
            return

        # Initialize timing variables
        last_check = datetime.now()
        last_frame_time = time.time()

        # Main frame processing loop
        while True:
            try:
                # Control frame processing rate
                current_time = time.time()
                if current_time - last_frame_time < FRAME_INTERVAL:
                    if cv2.waitKey(1) & 0xFF == ord("q"):
                        return
                    continue

                last_frame_time = current_time

                # Periodically check for block changes
                now = datetime.now()
                if now - last_check > CHECK_INTERVAL:
                    block_id, _ = getActiveClassStudentsFaceData(db, local)
                    attendance = getAttendanceForBlock(db, block_id)
                    last_check = now

                # Capture and process frame
                ok, frame = cam.read()
                if not ok:
                    print("Camera read failed")
                    break

                # Process frame and update voting
                result, recognized_email = process_frame(frame, face_db, attendance, db, block_id)
                
                if result is True and recognized_email:  # New face recognized
                    if recognized_email not in face_recognition_votes:
                        face_recognition_votes[recognized_email] = 1
                    else:
                        face_recognition_votes[recognized_email] += 1
                        
                        # Check if we have enough votes
                        if face_recognition_votes[recognized_email] >= VOTING_THRESHOLD:
                            postStudentAttendanceDB(db, recognized_email, block_id)
                            attendance.add(recognized_email)
                            print(f"Attendance recorded for {recognized_email} after {VOTING_THRESHOLD} confirmations")
                            face_recognition_votes.pop(recognized_email)
                elif result is False:  # No face or fake frame
                    # Reset face recognition votes
                    face_recognition_votes.clear()
                    anti_spoof_votes = 0
                # If result is None, face was already marked present, no action needed

                # Check for quit command
                if cv2.waitKey(1) & 0xFF == ord("q"):
                    break

            except Exception as e:
                print(f"Recognition error: {e}")
                break

        cam.release()


if __name__ == "__main__":
    main()
