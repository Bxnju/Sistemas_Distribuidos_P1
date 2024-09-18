import grpc
from concurrent import futures
import os
import sys
import json

sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', 'gRPC'))

import file_service_pb2_grpc
import file_service_pb2

# Archivo de configuración del peer
CONFIG_FILE = "config_peer_4.json"

# Cargar configuración del peer desde archivo
def load_config():
    with open(CONFIG_FILE, "r") as file:
        return json.load(file)

class FileServiceServicer(file_service_pb2_grpc.FileServiceServicer):
    def __init__(self, config):
        self.config = config

    def DownloadFile(self, request, context):
        try:
            file_path = os.path.join(self.config['directory'], request.file_name)
            print(f"Requested file: {request.file_name}")
            print(f"Full file path: {file_path}")
            
            if os.path.exists(file_path):
                print(f"File {file_path} found, starting download...")
                with open(file_path, "rb") as file:
                    while chunk := file.read(1024):
                        yield file_service_pb2.FileChunk(data=chunk)
            else:
                print(f"File {file_path} not found")
                context.set_details(f"File {request.file_name} not found in path {file_path}")
                context.set_code(grpc.StatusCode.NOT_FOUND)
        except Exception as e:
            print(f"Error while processing file {request.file_name}: {e}")
            context.set_details(f"Error while processing file {request.file_name}: {e}")
            context.set_code(grpc.StatusCode.INTERNAL)

def serve():
    config = load_config()
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    file_service_pb2_grpc.add_FileServiceServicer_to_server(FileServiceServicer(config), server)
    server.add_insecure_port(f'[::]:{config["port"]}')  # Usar el puerto del archivo de configuración
    server.start()
    print(f"Server started on port {config['port']}")
    server.wait_for_termination()

if __name__ == "__main__":
    serve()