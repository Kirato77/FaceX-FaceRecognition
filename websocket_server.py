import asyncio
import websockets
import json
import base64
import jwt
import cv2
import numpy as np
import face_recognition
from datetime import datetime
from config.env_loader import load_env_variables
from database.supabase_client import create_supabase_client
from database.attendance import getAttendanceForBlock, postStudentAttendanceDB
from utilitaire.face_recognition_utils import recognize_faces
from database.face_data import update_face_data
from Silent_Face_Anti_Spoofing.test import test


class WebSocketServer:
    def __init__(self, host="0.0.0.0", port=8765):
        self.host = host
        self.port = port
        self.connected_clients = set()
        self.env = load_env_variables()
        self.db = create_supabase_client(self.env["DB_URL"], self.env["DB_KEY"])
        self.active_courses = {}  # Store active course data for each client
        self.active_sessions = {}  # Store active attendance sessions

    def verify_token(self, token):
        """Verify Supabase JWT token and check if user is an instructor."""
        try:
            jwt_secret = self.env["DB_JWT"]
            expected_issuer = f"{self.env['DB_URL']}/auth/v1"
            print(f"Expected issuer: {expected_issuer}")

            decoded = jwt.decode(
                token,
                jwt_secret,
                algorithms=["HS256"],
                audience="authenticated",
                issuer=expected_issuer,
            )

            print(f"Token decoded successfully. Issuer in token: {decoded.get('iss')}")
            user_email = decoded.get("email")

            # Vérifier le rôle dans la table users
            response = (
                self.db.table("users").select("role").eq("email", user_email).execute()
            )

            if response.data and len(response.data) > 0:
                user_role = response.data[0].get("role")
                print(f"User role from database: {user_role}")
                if user_role == "instructor":
                    print("Access granted: User is an instructor")
                    return True
                else:
                    print("Access denied: User is not an instructor")
                    return False
            else:
                print(f"No role found in database for user with email: {user_email}")
                return False

        except jwt.ExpiredSignatureError:
            print("Token has expired")
            return False
        except jwt.InvalidTokenError as e:
            print(f"Invalid token: {e}")
            return False
        except Exception as e:
            print(f"Token verification failed: {e}")
            return False

    async def start_attendance_session(self, block_id, websocket):
        """Start a new attendance session for a block."""
        try:
            # Get students for this block
            response = (
                self.db.table("class_blocks")
                .select("course_id")
                .eq("block_id", block_id)
                .execute()
            )
            print(f"Block response: {response.data}")

            if not response.data:
                await websocket.send(
                    json.dumps({"status": "error", "message": "Block not found"})
                )
                return False

            course_id = response.data[0]["course_id"]
            print(f"Found course_id: {course_id}")

            # Get students for this course
            response = (
                self.db.table("student_courses")
                .select("student_email")
                .eq("course_id", course_id)
                .execute()
            )
            print(f"Students response: {response.data}")

            if not response.data:
                await websocket.send(
                    json.dumps(
                        {
                            "status": "error",
                            "message": "No students found for this course",
                        }
                    )
                )
                return False

            # Get face data and user info for all students
            face_db = {}
            for student in response.data:
                email = student["student_email"]
                # Get user info and face data
                user_response = (
                    self.db.table("users")
                    .select("face_data,first_name,name")
                    .eq("email", email)
                    .execute()
                )
                if user_response.data and user_response.data[0].get("face_data"):
                    face_data = user_response.data[0]["face_data"]

                    # Convert face data to numpy array if it's not already
                    if isinstance(face_data, list):
                        try:
                            face_data = [
                                np.array(emb, dtype=np.float32) for emb in face_data
                            ]
                        except Exception as e:
                            print(f"Error converting face data for {email}: {e}")
                            continue

                    face_db[email] = {
                        "face_data": face_data,
                        "first_name": user_response.data[0]["first_name"],
                        "last_name": user_response.data[0]["name"],
                    }
                    print(f"Added data for student: {email}")

            print(f"Total students with face data: {len(face_db)}")

            # Get attendance data
            attendance = getAttendanceForBlock(self.db, block_id)

            # Store session data
            self.active_sessions[websocket] = {
                "block_id": block_id,
                "course_id": course_id,
                "face_db": face_db,
                "attendance": attendance,
                "start_time": datetime.now(),
            }

            await websocket.send(
                json.dumps(
                    {
                        "status": "success",
                        "message": "Attendance session started",
                        "data": {
                            "total_students": len(face_db),
                            "start_time": datetime.now().isoformat(),
                        },
                    }
                )
            )
            return True

        except Exception as e:
            print(f"Error starting attendance session: {e}")
            await websocket.send(
                json.dumps(
                    {
                        "status": "error",
                        "message": f"Error starting attendance session: {str(e)}",
                    }
                )
            )
            return False

    async def end_attendance_session(self, websocket):
        """End an attendance session and clean up."""
        if websocket in self.active_sessions:
            # session = self.active_sessions[websocket]
            # duration = datetime.now() - session['start_time']
            # await websocket.send(json.dumps({
            #     "status": "success",
            #     "message": "Attendance session ended",
            #     "data": {
            #         "duration": str(duration),
            #         "attendance_count": len(session['attendance'])
            #     }
            # }))
            del self.active_sessions[websocket]

    async def process_image(self, image_data, websocket):
        """Process received image for face recognition."""
        if websocket not in self.active_sessions:
            await websocket.send(
                json.dumps(
                    {"status": "error", "message": "No active attendance session"}
                )
            )
            return

        try:
            # Convert base64 to image
            nparr = np.frombuffer(image_data, np.uint8)
            frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)

            # Ensure frame is in the correct format
            if frame is None:
                print("Error: Failed to decode image")
                await websocket.send(
                    json.dumps({"status": "error", "message": "Failed to decode image"})
                )
                return

            # Convert to uint8 if not already
            if frame.dtype != np.uint8:
                frame = frame.astype(np.uint8)

            # Ensure frame is in BGR format (OpenCV default)
            if len(frame.shape) == 2:  # If grayscale
                frame = cv2.cvtColor(frame, cv2.COLOR_GRAY2BGR)
            elif len(frame.shape) == 3 and frame.shape[2] == 4:  # If RGBA
                frame = cv2.cvtColor(frame, cv2.COLOR_RGBA2BGR)

            session = self.active_sessions[websocket]

            # Check if frame is real using anti-spoofing
            label = test(
                image=frame,
                model_dir="Silent_Face_Anti_Spoofing/resources/anti_spoof_models",
                device_id=0,
            )

            if label == 1:  # Real frame
                print("Real frame detected, attempting face recognition")
                # Try to recognize faces
                result, recognized_email = recognize_faces(
                    frame,
                    session["face_db"],
                    session["attendance"],
                    self.db,
                    session["block_id"],
                )

                if result is True and recognized_email:  # New face recognized
                    student_data = session["face_db"][recognized_email]
                    student_name = (
                        f"{student_data['first_name']} {student_data['last_name']}"
                    )
                    print(f"Face recognized: {student_name}")

                    # Record attendance immediately
                    if postStudentAttendanceDB(
                        self.db, recognized_email, session["block_id"]
                    ):
                        session["attendance"].add(recognized_email)
                        await websocket.send(
                            json.dumps(
                                {
                                    "status": "success",
                                    "message": f"Attendance recorded for {student_name}",
                                    "data": {
                                        "email": recognized_email,
                                        "name": student_name,
                                        "attendance_count": len(session["attendance"]),
                                    },
                                }
                            )
                        )
                    else:
                        await websocket.send(
                            json.dumps(
                                {
                                    "status": "error",
                                    "message": f"Failed to record attendance for {student_name}",
                                    "data": {
                                        "email": recognized_email,
                                        "name": student_name,
                                    },
                                }
                            )
                        )
                elif result is None and recognized_email:  # Face already present
                    student_data = session["face_db"][recognized_email]
                    student_name = (
                        f"{student_data['first_name']} {student_data['last_name']}"
                    )
                    print(f"Face already present: {student_name}")
                    await websocket.send(
                        json.dumps(
                            {
                                "status": "info",
                                "message": f"Face already present: {student_name}",
                                "data": {
                                    "email": recognized_email,
                                    "name": student_name,
                                    "attendance_count": len(session["attendance"]),
                                },
                            }
                        )
                    )
                else:
                    print("No new face recognized in frame")
            else:
                print("Fake frame detected")
                await websocket.send(
                    json.dumps({"status": "warning", "message": "Fake frame detected"})
                )

        except Exception as e:
            print(f"Error processing image: {e}")
            await websocket.send(
                json.dumps(
                    {"status": "error", "message": f"Error processing image: {str(e)}"}
                )
            )

    async def handle_connection(self, websocket, path):
        """Handle incoming WebSocket connections."""
        client_added = False
        try:
            print(f"New connection attempt from {websocket.remote_address}")

            # Extract token from query parameters
            query_params = dict(
                param.split("=") for param in path.split("?")[1].split("&")
            )
            token = query_params.get("token")

            if not token or not self.verify_token(token):
                print("Token verification failed")
                await websocket.send(
                    json.dumps({"status": "error", "message": "Unauthorized access"})
                )
                return

            self.connected_clients.add(websocket)
            client_added = True
            print(f"Client connected. Total clients: {len(self.connected_clients)}")

            # Send a test message
            await websocket.send(
                json.dumps({"status": "success", "message": "Connection established"})
            )

            async for message in websocket:
                try:
                    # Check if the message is binary (image data)
                    if isinstance(message, bytes):
                        print("Received binary data (image)")
                        await self.process_image(message, websocket)
                    else:
                        # Handle text messages
                        print(f"Received text message: {message[:100]}...")
                        try:
                            data = json.loads(message)
                            if "action" in data:
                                if (
                                    data["action"] == "start_attendance"
                                    and "block_id" in data
                                ):
                                    await self.start_attendance_session(
                                        data["block_id"], websocket
                                    )
                                elif data["action"] == "end_attendance":
                                    await self.end_attendance_session(websocket)
                                else:
                                    await websocket.send(
                                        json.dumps(
                                            {
                                                "status": "error",
                                                "message": "Invalid action",
                                            }
                                        )
                                    )
                            else:
                                await websocket.send(
                                    json.dumps(
                                        {
                                            "status": "error",
                                            "message": "Invalid message format",
                                        }
                                    )
                                )
                        except json.JSONDecodeError:
                            await websocket.send(
                                json.dumps(
                                    {
                                        "status": "error",
                                        "message": "Invalid JSON format",
                                    }
                                )
                            )
                except Exception as e:
                    print(f"Error processing message: {e}")
                    await websocket.send(
                        json.dumps(
                            {
                                "status": "error",
                                "message": f"Error processing message: {str(e)}",
                            }
                        )
                    )

        except websockets.exceptions.ConnectionClosed:
            print("Client disconnected")
        except Exception as e:
            print(f"Error handling connection: {e}")
        finally:
            if client_added:
                self.connected_clients.remove(websocket)
                if websocket in self.active_sessions:
                    del self.active_sessions[websocket]
                print(
                    f"Client disconnected. Total clients: {len(self.connected_clients)}"
                )

    async def start(self):
        """Start the WebSocket server."""
        server = await websockets.serve(self.handle_connection, self.host, self.port)
        print(f"WebSocket server started on ws://{self.host}:{self.port}")
        await server.wait_closed()


if __name__ == "__main__":
    server = WebSocketServer()
    asyncio.get_event_loop().run_until_complete(server.start())
