import asyncio
import websockets
import json
import base64
import jwt
from config.env_loader import load_env_variables
from database.supabase_client import create_supabase_client

class WebSocketServer:
    def __init__(self, host="0.0.0.0", port=8765):
        self.host = host
        self.port = port
        self.connected_clients = set()
        self.env = load_env_variables()
        self.db = create_supabase_client(self.env["DB_URL"], self.env["DB_KEY"])

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
                issuer=expected_issuer
            )
            
            print(f"Token decoded successfully. Issuer in token: {decoded.get('iss')}")
            user_email = decoded.get("email")
            
            # Vérifier le rôle dans la table users
            response = self.db.table('users').select('role').eq('email', user_email).execute()
            
            if response.data and len(response.data) > 0:
                user_role = response.data[0].get('role')
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

    async def handle_connection(self, websocket, path):
        """Handle incoming WebSocket connections."""
        client_added = False
        try:
            print(f"New connection attempt from {websocket.remote_address}")
            
            # Extract token from query parameters
            query_params = dict(param.split('=') for param in path.split('?')[1].split('&'))
            token = query_params.get('token')
            
            if token:
                masked_token = f"{token[:10]}...{token[-10:]}" if len(token) > 20 else "***"
                print(f"Received token: {masked_token}")

            if not token or not self.verify_token(token):
                print("Token verification failed")
                await websocket.send(json.dumps({
                    "status": "error",
                    "message": "Unauthorized access"
                }))
                return

            self.connected_clients.add(websocket)
            client_added = True
            print(f"Client connected. Total clients: {len(self.connected_clients)}")

            # Send a test message
            await websocket.send(json.dumps({
                "status": "success",
                "message": "Connection established"
            }))

            async for message in websocket:
                try:
                    # Check if the message is binary (image data)
                    if isinstance(message, bytes):
                        print("Received binary data (image)")
                        # Send acknowledgment
                        await websocket.send(json.dumps({
                            "status": "success",
                            "message": "Image received successfully",
                            "data": "Image processed"
                        }))
                    else:
                        # Handle text messages
                        print(f"Received text message: {message[:100]}...")
                        await websocket.send(json.dumps({
                            "status": "success",
                            "message": "Message received",
                            "data": message[:100]
                        }))
                except Exception as e:
                    print(f"Error processing message: {e}")
                    await websocket.send(json.dumps({
                        "status": "error",
                        "message": f"Error processing message: {str(e)}"
                    }))

        except websockets.exceptions.ConnectionClosed:
            print("Client disconnected")
        except Exception as e:
            print(f"Error handling connection: {e}")
        finally:
            if client_added:
                self.connected_clients.remove(websocket)
                print(f"Client disconnected. Total clients: {len(self.connected_clients)}")

    async def start(self):
        """Start the WebSocket server."""
        server = await websockets.serve(
            self.handle_connection,
            self.host,
            self.port
        )
        print(f"WebSocket server started on ws://{self.host}:{self.port}")
        await server.wait_closed()

if __name__ == "__main__":
    server = WebSocketServer()
    asyncio.get_event_loop().run_until_complete(server.start())
