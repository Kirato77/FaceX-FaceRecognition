import numpy as np
from database.face_data import update_face_data


def update_and_validate(db, email, faces):
    """Update face data for a person and store in face database."""
    data = update_face_data(db, email)
    if data:
        faces[email] = data
        print(f"Face data updated for {email}")
        return True
    print(f"Could not update face data for {email}")
    return False


def check_face_data(db, email, emb, faces):
    """Validate face data and update if needed."""
    # Check if face data exists
    if email not in faces or not faces[email]:
        print(f"No face data for {email}, updating...")
        if not update_and_validate(db, email, faces):
            return False

    # Convert embedding to numpy array
    try:
        emb = np.array(emb)
    except Exception as e:
        print(f"Error converting data for {email}: {e}")
        if not update_and_validate(db, email, faces):
            return False

    # Validate numeric data
    if not np.issubdtype(emb.dtype, np.number):
        print(f"Non-numeric data for {email}, updating...")
        if not update_and_validate(db, email, faces):
            return False

    # Check embedding length
    if len(emb) != 128:
        print(f"Invalid embedding length for {email}: {len(emb)}, updating...")
        if not update_and_validate(db, email, faces):
            return False

    return True


def normalize(emb):
    """Normalize face embedding vector."""
    return emb / np.linalg.norm(emb)
