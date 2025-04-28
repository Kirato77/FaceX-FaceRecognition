import cv2
import numpy as np
import face_recognition
from database.attendance import postStudentAttendanceDB
from PIL import Image
import io


def normalize(emb):
    """Normalize a face embedding vector."""
    return emb / np.linalg.norm(emb)


def get_student_name(db, email):
    """Get student's full name from their email."""
    resp = db.rpc("get_user_by_email", {"user_email": email}).execute()

    if resp.data and "first_name" in resp.data and "last_name" in resp.data:
        return f"{resp.data['first_name']} {resp.data['last_name']}"
    return "Inconnu"


def recognize_faces(img, face_db, attendance, db, block_id):
    """
    Recognize faces in an image and handle attendance.

    Args:
        img: Input image
        face_db: Database of known face embeddings
        attendance: Set of students already marked present
        db: Supabase client
        block_id: Current class block ID

    Returns:
        - False if no faces found
        - True if new attendance recorded
        - None if face already marked present
    """
    try:
        # Convert and resize image
        rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        small = cv2.resize(rgb, (0, 0), None, 0.5, 0.5)

        # Find faces
        locs = face_recognition.face_locations(small)
        encs = face_recognition.face_encodings(small, locs)

        # Check each face
        for enc in encs:
            min_dist = float("inf")
            match = None

            # Compare with known faces
            for email, data in face_db.items():
                embs = data.get("face_data")
                if not embs:
                    print(f"No face data for {email}")
                    continue

                # Find best match
                for emb in embs:
                    dist = np.linalg.norm(enc - normalize(np.array(emb)))
                    if dist < min_dist:
                        min_dist = dist
                        match = email

            # Handle match results
            if min_dist < 0.65:
                name = f"{face_db[match]['first_name']} {face_db[match]['last_name']}"
                print(f"Found: {name} (dist: {min_dist:.3f})")

                if match not in attendance:
                    postStudentAttendanceDB(db, match, block_id)
                    attendance.add(match)
                    return True
                else:
                    print(f"{name} already present (dist: {min_dist:.3f})")
                    return None
            else:
                print("Face found but not recognized")
                return False

    except Exception as e:
        print(f"Recognition error: {e}")
        return False


def studentsImgToFaceData(db, email):
    """
    Extract face embeddings from a student's profile picture.

    Args:
        db: Supabase client
        email: Student's email address

    Returns:
        Face embedding as list or None if failed
    """
    try:
        # Get student info
        try:
            resp = db.rpc("get_user_by_email", {"user_email": email}).execute()
            if not resp.data:
                raise ValueError(f"No user found for {email}")
        except ValueError as e:
            print(f"DB error: {e}")
            return None

        # Get profile picture
        id = resp.data["matricule"]
        img_bytes = db.storage.from_("id-pictures").download(f"students/{id}.jpg")

        # Process image
        img = Image.open(io.BytesIO(img_bytes))
        if img.mode != "RGB":
            img = img.convert("RGB")

        # Get face data
        arr = np.array(img)
        faces = face_recognition.face_encodings(arr)

        if faces:
            return faces[0].tolist()

        print(f"No face found for {email}")
        return None

    except Exception as e:
        print(f"Error processing {email}: {e}")
        return None
