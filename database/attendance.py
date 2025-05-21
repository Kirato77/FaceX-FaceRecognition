from datetime import datetime


def getActiveClassStudentsFaceData(supabase, local):
    try:
        response = supabase.rpc(
            "get_active_class_students_face_data", {"local_now": local}
        ).execute()
        return response.data["block_id"], response.data["students"]

    except ValueError:
        print(
            "Erreur supabase : soucis dans la requete vers supabase 'get_active_class_students_face_data'"
        )
        return None


def getAttendanceForBlock(supabase, class_block_id):
    try:
        response = supabase.rpc(
            "get_attendance_for_class_block_python",
            {"class_block_id": int(class_block_id)},
        ).execute()
        return {attendance["student_email"] for attendance in response.data}

    except ValueError:
        print(
            "Erreur supabase : soucis dans la requete vers supabase 'get_attendance_for_class_block_python'"
        )
        return None


def postStudentAttendanceDB(
    supabase, student_email, block_id, timestamp=None, status="Present"
):
    if not timestamp:
        timestamp = datetime.now().isoformat()
    try:
        print(
            f"Attempting to record attendance for {student_email} in block {block_id}"
        )
        response = supabase.rpc(
            "post_new_attendance",
            {
                "attendance_student_email": student_email,
                "attendance_block_id": block_id,
                "attendance_status": status,
                "attendance_timestamp": timestamp,
            },
        ).execute()

        if response.data:
            print(f"Présence enregistrée pour {student_email} (Block ID : {block_id}).")
            return True
        else:
            print(f"{student_email} était déjà enregistré pour ce bloc.")
            return False
    except Exception as e:
        print(
            f"Erreur supabase : soucis dans la requete vers supabase 'post_new_attendance' pour cet étudiant {student_email}: {str(e)}"
        )
        return False
