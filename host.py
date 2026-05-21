import socket 
from pathlib import Path 
import json 
import os
import struct

musicFolder = Path('HOST MUSIC PATH')

serverip = 'YOUR SERVERS LOCAL IP' 
port = 8056 

def receive_exact(conn, num_bytes):
    buffer = b''
    while len(buffer) < num_bytes:
        chunk = conn.recv(num_bytes - len(buffer))
        if not chunk:
            raise ConnectionError("Socket closed prematurely.")
        buffer += chunk
    return buffer

TYPE_MUSIC_LIST = 0
TYPE_MP3 = 1

def sendJson(): 
    musicList = path_to_dict(musicFolder)

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.connect((serverip, port))

        json_bytes = json.dumps(musicList).encode('utf-8')
        header = struct.pack('!BI', TYPE_MUSIC_LIST, len(json_bytes))
        s.sendall(header + json_bytes)
        print("JSON structure successfully sent. Waiting for server to calculate differences...")

        header = receive_exact(s, 4)
        data_len = struct.unpack('!I', header)[0]
        diff_json_bytes = receive_exact(s, data_len)
        differences = json.loads(diff_json_bytes.decode('utf-8'))

        print("\nFiles to sync (received from server):")
        if not differences:
            print("No differences found. Everything is up to date!")
        else:
            for diff in differences:
                print(f"- {diff['path']} ({diff['reason']})")

        return differences

def sendMissingSongs(differences):
    for diff in differences:
        if diff['reason'] == 'missing':
            rel_path = diff['path']
            full_path = musicFolder / rel_path

            if not full_path.exists():
                print(f"Error: {full_path} not found on host.")
                continue

            print(f"Uploading: {rel_path}")

            file_size = os.path.getsize(full_path)
            meta = json.dumps({"path": rel_path, "size": file_size}).encode('utf-8')

            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect((serverip, port))

                header = struct.pack('!BI', TYPE_MP3, len(meta))
                s.sendall(header + meta)

                # Send File Data
                with open(full_path, 'rb') as f:
                    while True:
                        chunk = f.read(4096)
                        if not chunk:
                            break
                        s.sendall(chunk)

            print(f"Finished uploading {rel_path}")

def path_to_dict(path): 
    name = os.path.basename(path)

    if os.path.isfile(path):
        return {"name": name, "type": "file"}
        
    if os.path.isdir(path):
        return {
            "name": name,
            "type": "directory",
            "children": [path_to_dict(os.path.join(path, x)) for x in os.listdir(path)]
        }

if __name__ == "__main__":
    diffs = sendJson()
    if diffs:
        sendMissingSongs(diffs)
