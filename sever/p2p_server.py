from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import json
import os
import uvicorn

app = FastAPI()

# Ruta del archivo JSON para almacenar la información de los peers
PEERS_FILE = "peers.json"

# Cargar información de los peers desde el archivo
def load_peers():
    if os.path.exists(PEERS_FILE):
        with open(PEERS_FILE, "r") as file:
            content = file.read().strip()
            if content:  # Check if the file is not empty
                return json.loads(content)
    return {}

# Guardar información de los peers en el archivo
def save_peers(peers):
    with open(PEERS_FILE, "w") as file:
        json.dump(peers, file, indent=4)

# Pydantic models for requests
class LoginRequest(BaseModel):
    peer_id: str
    ip: str
    port: int

class LogoutRequest(BaseModel):
    peer_id: str

class DeleteRequest(BaseModel):
    peer_id: str

class LoadFilesRequest(BaseModel):
    peer_id: str
    files: list

class FindFileRequest(BaseModel):
    file_name: str

# Ruta para login de peers
@app.post("/login")
def login(request: LoginRequest):
    peers = load_peers()
    peers[request.peer_id] = {"ip": request.ip, "port": request.port, "files": [], "active": True}
    save_peers(peers)
    return {"message": f"Peer {request.peer_id} está activo"}

# Ruta para logout de peers
@app.post("/logout")
def logout(request: LogoutRequest):
    peers = load_peers()
    if request.peer_id in peers:
        peers[request.peer_id]["active"] = False
        save_peers(peers)
        return {"message": f"Peer {request.peer_id} se ha desactivado"}
    raise HTTPException(status_code=404, detail="Peer no encontrado")

# Ruta para eliminar peers
@app.delete("/delete")
def delete_peer(request: DeleteRequest):
    peers = load_peers()
    if request.peer_id in peers:
        del peers[request.peer_id]
        save_peers(peers)
        return {"message": f"Peer {request.peer_id} ha sido eliminado"}
    raise HTTPException(status_code=404, detail="Peer no encontrado")

# Ruta para cargar archivos disponibles de un peer
@app.post("/load_files")
def load_files(request: LoadFilesRequest):
    peers = load_peers()
    if request.peer_id in peers:
        peers[request.peer_id]["files"] = request.files
        save_peers(peers)
        return {"message": f"Archivos del Peer {request.peer_id} actualizados"}
    raise HTTPException(status_code=404, detail="Peer no encontrado")

# Ruta para encontrar el archivo en los peers
@app.post("/find")
def find_file(request: FindFileRequest):
    peers = load_peers()
    result = []
    for peer_id, peer_info in peers.items():
        if request.file_name in peer_info["files"] and peer_info["active"]:
            result.append({"peer_id": peer_id, "ip": peer_info["ip"], "port": peer_info["port"]})

    if result:
        return {"peers": result}
    raise HTTPException(status_code=404, detail="Archivo no encontrado")

# Ruta para listar todos los peers activos
@app.get("/active_peers")
def list_active_peers():
    peers = load_peers()
    active_peers = {peer_id: info for peer_id, info in peers.items() if info["active"]}
    return {"peers": active_peers}

# Ruta para listar todos los archivos disponibles en el servidor
@app.get("/all_files")
def list_all_files():
    peers = load_peers()
    all_files = set()
    for peer_info in peers.values():
        all_files.update(peer_info["files"])
    return {"files": list(all_files)}

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=5050)