import sys
import os
import shutil
import tkinter as tk
from tkinter import filedialog

# Agregar el directorio gRPC al PYTHONPATH
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'gRPC'))

import requests
import json
import grpc
import file_service_pb2
import file_service_pb2_grpc
import argparse

# Archivo de configuración del peer
CONFIG_FILE = "peer3\\config_peer_3.json"

# Cargar configuración del peer desde archivo
def load_config():
    with open(CONFIG_FILE, "r") as file:
        return json.load(file)

# Obtener lista de archivos en el directorio compartido
def get_files(directory):
    return os.listdir(directory)

# Función para iniciar sesión en el servidor
def login(config):
    url = f"http://{config['server_ip']}:{config['server_port']}/login"
    data = {
        "peer_id": config["peer_id"],
        "ip": config["ip"],
        "port": config["port"]
    }
    try:
        response = requests.post(url, json=data)
        response.raise_for_status()
        print(response.json())
    except requests.RequestException as e:
        print(f"Error during login: {e}")

# Función para cerrar sesión en el servidor
def logout(config):
    url = f"http://{config['server_ip']}:{config['server_port']}/logout"
    data = {"peer_id": config["peer_id"]}
    try:
        response = requests.put(url, json=data)
        response.raise_for_status()
        print(response.json())
    except requests.RequestException as e:
        print(f"Error during logout: {e}")

# Función para eliminar el peer del servidor
def delete_peer(config):
    url = f"http://{config['server_ip']}:{config['server_port']}/delete"
    data = {"peer_id": config["peer_id"]}
    try:
        response = requests.delete(url, json=data)
        response.raise_for_status()
        print(response.json())
    except requests.RequestException as e:
        print(f"Error during delete_peer: {e}")

# Función para cargar archivos disponibles en el servidor
def load_files(config):
    url = f"http://{config['server_ip']}:{config['server_port']}/load_files"
    files = get_files(config["directory"])
    data = {"peer_id": config["peer_id"], "files": files}
    try:
        response = requests.post(url, json=data)
        response.raise_for_status()
        print(response.json())
    except requests.RequestException as e:
        print(f"Error during load_files: {e}")

# Función para buscar un archivo en el servidor
def find_file(config, filename):
    url = f"http://{config['server_ip']}:{config['server_port']}/find"
    data = {"file_name": filename}
    try:
        response = requests.get(url, json=data)
        response.raise_for_status()
        print(response.json())
        return response.json().get("peers", [])
    except requests.RequestException as e:
        print(f"Error during find_file: {e}")
        return []

# Función para descargar un archivo desde otro peer
def download(config, filename):
    peers = find_file(config, filename)
    if not peers:
        print(f"File {filename} not found on any peer")
        return

    peer = peers[0]  # Seleccionar el primer peer que tiene el archivo
    peer_ip = peer["ip"]
    peer_port = peer["port"]
    save_path = os.path.join(config["directory"], filename)

    if download_file(peer_ip, peer_port, filename, save_path):
        load_files(config)

def download_file(peer_ip, peer_port, file_name, save_path):
    try:
        with grpc.insecure_channel(f"{peer_ip}:{peer_port}") as channel:
            stub = file_service_pb2_grpc.FileServiceStub(channel)
            request = file_service_pb2.FileRequest(file_name=file_name)
            response_iterator = stub.DownloadFile(request)

            # Verificar si se recibe algún dato antes de crear el archivo
            first_chunk = next(response_iterator)
            if first_chunk:
                with open(save_path, "wb") as file:
                    file.write(first_chunk.data)
                    for chunk in response_iterator:
                        file.write(chunk.data)
                print(f"File {file_name} downloaded to {save_path}")
                return True
            else:
                print(f"No data received for file {file_name}")
    except grpc.RpcError as e:
        print(f"gRPC error: {e}")
    except StopIteration:
        print(f"File {file_name} not found on peer {peer_ip}:{peer_port}")

# Función para cargar un archivo desde el explorador de archivos
def upload(config):
    root = tk.Tk()
    root.withdraw()  # Ocultar la ventana principal de Tkinter
    file_path = filedialog.askopenfilename()  # Abrir el explorador de archivos
    if file_path:
        try:
            shutil.copy(file_path, config["directory"])
            print(f"File {os.path.basename(file_path)} uploaded to {config['directory']}")
            load_files(config)  # Actualizar la lista de archivos en el servidor
        except Exception as e:
            print(f"Error uploading file: {e}")

# Función para eliminar un archivo del directorio compartido
def delete_file(config, filename):
    file_path = os.path.join(config["directory"], filename)
    if os.path.exists(file_path):
        try:
            os.remove(file_path)
            print(f"File {filename} deleted from {config['directory']}")
            load_files(config)  # Actualizar la lista de archivos en el servidor
        except Exception as e:
            print(f"Error deleting file: {e}")
    else:
        print(f"File {filename} does not exist in {config['directory']}")

# Función para listar todos los archivos compartidos por el peer
def list_files(config):
    files = get_files(config["directory"])
    print("Shared files:")
    for file in files:
        print(file)

# Función para listar todos los peers activos en el servidor
def list_active_peers(config):
    url = f"http://{config['server_ip']}:{config['server_port']}/active_peers"
    try:
        response = requests.get(url)
        response.raise_for_status()
        peers = response.json().get("peers", [])
        print("Active peers:")
        for peer in peers:
            print(peer)
    except requests.RequestException as e:
        print(f"Error listing active peers: {e}")

# Función para obtener una lista de todos los archivos disponibles en el servidor
def list_all_files(config):
    url = f"http://{config['server_ip']}:{config['server_port']}/all_files"
    try:
        response = requests.get(url)
        response.raise_for_status()
        files = response.json().get("files", [])
        print("All available files on the server:")
        for file in files:
            print(file)
    except requests.RequestException as e:
        print(f"Error listing all files: {e}")

def main():
    parser = argparse.ArgumentParser(description="Peer Service")
    parser.add_argument("action", choices=["login", "logout", "delete", "load_files", "find", "download", "upload", "delete_file", "list_files", "list_active_peers", "list_all_files"], help="Action to perform")
    parser.add_argument("--filename", help="File name to find, download, or delete")
    args = parser.parse_args()

    config = load_config()

    if args.action == "login":
        login(config)
    elif args.action == "logout":
        logout(config)
    elif args.action == "delete":
        delete_peer(config)
    elif args.action == "load_files":
        load_files(config)
    elif args.action == "find":
        if args.filename:
            find_file(config, args.filename)
        else:
            print("Filename required for find action")
    elif args.action == "download":
        if args.filename:
            download(config, args.filename)
        else:
            print("Filename required for download action")
    elif args.action == "upload":
        upload(config)
    elif args.action == "delete_file":
        if args.filename:
            delete_file(config, args.filename)
        else:
            print("Filename required for delete_file action")
    elif args.action == "list_files":
        list_files(config)
    elif args.action == "list_active_peers":
        list_active_peers(config)
    elif args.action == "list_all_files":
        list_all_files(config)

if __name__ == "__main__":
    main()