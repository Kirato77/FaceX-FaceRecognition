import face_recognition
from supabase import Client
from PIL import Image
import io
import numpy as np


def img_to_face_data(img):
    """Extract face encoding data from an image."""
    try:
        print("Processing image...")

        # Convert to RGB if needed
        if img.mode != "RGB":
            img = img.convert("RGB")

        # Convert to numpy array and get face encoding
        img_array = np.array(img)
        face_encodings = face_recognition.face_encodings(img_array)

        if face_encodings:
            return face_encodings[0].tolist()

        print("No face encoding found in image.")
        return None

    except Exception as e:
        print(f"Error extracting face encoding: {e}")
        return None


def student_img_to_face_data(db: Client, email: str):
    """Get face encoding data from student's stored image."""
    # Get student ID
    resp = db.rpc("get_user_by_email", {"user_email": email}).execute()
    student_id = resp.data["matricule"]

    # Get image from storage
    img_data = db.storage.from_("id-pictures").download(f"students/{student_id}.jpg")
    img = Image.open(io.BytesIO(img_data))

    # Extract face data
    face_data = img_to_face_data(img)
    if face_data:
        return face_data
    print("No face encoding found for student.")
    return None


def update_all_face_data(db: Client):
    """Update face data for all students in database."""
    users = db.rpc("get_all_users").execute()

    for user in users.data:
        if user["role"] == "student":
            print(f"Processing: {user['email']}")
            face_data = [student_img_to_face_data(db, user["email"])]
            db.rpc(
                "update_face_data",
                {"user_email": user["email"], "new_face_data": face_data},
            ).execute()


def update_one_face_data(db: Client, email: str):
    """Update face data for single student."""
    print(f"Updating face data for: {email}")

    face_data = [student_img_to_face_data(db, email)]
    db.rpc(
        "update_face_data", {"user_email": email, "new_face_data": face_data}
    ).execute()

    print(f"Face data update complete for: {email}")
    return face_data
