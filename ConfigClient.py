# client.py
import socket
import json
import threading
import time
from colorama import Fore, Style, init
init(autoreset=True)

class ConfigClient:
    def __init__(self):
        self.client_id = "ConfigClient"
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.connected = False
        
    def connect(self):
        try:
            # Step 1: Connect to server
            self.socket.connect(('localhost', 12345))
            print(f"{self.client_id} connecting to server...")

            # Step 2: Send identification message
            id_message = {
                "type": "identification",
                "client_name": self.client_id
            }
            self.socket.send(json.dumps(id_message).encode('utf-8'))

            # Step 3: Wait for server confirmation
            confirmation_data = self.socket.recv(1024).decode('utf-8')
            confirmation = json.loads(confirmation_data)

            if confirmation.get("type") == "identification_confirmed":
                self.connected = True
                if confirmation.get("is_reconnection"):
                    print(Fore.GREEN + f"{self.client_id} RECONNECTED! (Connection #{confirmation.get('connection_number')})")
                    print(f"   Previous messages sent: {confirmation.get('previous_messages')}")
                else:
                    print(Fore.GREEN + f"{self.client_id} connected as NEW client")

                # Start listener thread for server responses
                listener = threading.Thread(target=self.listen_for_responses)
                listener.daemon = True
                listener.start()
            else:
                print(Fore.RED + f"Server rejected {self.client_id}")

        except Exception as e:
            print(Fore.RED + f"{self.client_id} failed to connect: {e}")

    def listen_for_responses(self):
        while self.connected:
            try:
                data = self.socket.recv(8192).decode('utf-8')
                if not data:
                    continue

                response = json.loads(data)
                if response.get("type") == "confirmation":
                    if response.get("matched"):
                        print(Fore.GREEN + f"Server confirmed config received and matched.")
                        self.disconnect()
                    else:
                        print(Fore.RED + f"Server responded but config was invalid: {response}")

            except Exception as e:
                if self.connected:
                    print(Fore.RED + f"Error receiving data: {e}")
                break

    def send_config(self, config, erasion, hex_path, upload_delay):
        if not self.connected:
            print(f"Not connected to server")
            return

        config_message = {
            "config": config,
            "erasion": erasion,
            "hex_path": hex_path,
            "upload_delay": upload_delay
        }

        try:
            self.socket.send(json.dumps(config_message).encode('utf-8'))
            print(f"Sent configuration: {config_message}")
        except Exception as e:
            print(f"Failed to send config: {e}")

    def disconnect(self):
        self.connected = False
        self.socket.close()
        print(Fore.GREEN + f"{self.client_id} disconnected")

if __name__ == "__main__":
    client = ConfigClient()
    client.connect()

    # Example configuration message
    time.sleep(1)
    client.send_config(
        config="ASI",
        erasion="Yes",
        hex_path="C:/Projects/Firmware/Output/",
        upload_delay=10
    )

    # Keep alive until confirmation or disconnection
    while client.connected:
        time.sleep(0.5)
