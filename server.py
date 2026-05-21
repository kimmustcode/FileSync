import socket
import json
import struct
import os 

MUSIC_PATH = "YOUR MUSIC PATH ON SERVER"

def receive_exact(conn, num_bytes):
    buffer = b''
    while len(buffer) < num_bytes:
        chunk = conn.recv(num_bytes - len(buffer))
        if not chunk:
            raise ConnectionError("Socket closed prematurely.")
        buffer += chunk
    return buffer

def findDiff(hostDict, serverDict, path=""): 
    mismatches = []
    
    server_children = {child['name']: child for child in serverDict.get('children', [])}
    
    for host_item in hostDict.get('children', []):
        name = host_item['name']
        current_path = f"{path}/{name}" if path else name
        
        if host_item['type'] == 'directory':
            server_item = server_children.get(name)

            if not server_item or server_item['type'] != 'directory':
                server_item = {'name': name, 'type': 'directory', 'children': []}
            
            sub_mismatches = findDiff(host_item, server_item, current_path)
            mismatches.extend(sub_mismatches)
            
        elif host_item['type'] == 'file' and name.lower().endswith('.mp3'):
            if name not in server_children or server_children[name]['type'] != 'file':
                mismatches.append({"path": current_path, "reason": "missing", "type": "file"})
                
    return mismatches

TYPE_MUSIC_LIST = 0
TYPE_MP3 = 1

def start_server(host='0.0.0.0', port=8056):
    if not os.path.exists(MUSIC_PATH):
        print(f"WARNING: MUSIC_PATH '{MUSIC_PATH}' does not exist. Created an empty directory structure for comparison.")
    
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        s.bind((host, port))
        s.listen()
        print(f"Server listening on {host}:{port}")
        
        while True:
            try:
                conn, addr = s.accept()
                try:
                    with conn:
                        print(f"Connected by {addr}")
                        
                        header = receive_exact(conn, 5)
                        msg_type, data_len = struct.unpack('!BI', header)
                        
                        if msg_type == TYPE_MUSIC_LIST:
                            json_bytes = receive_exact(conn, data_len)
                            host_dict = json.loads(json_bytes.decode('utf-8'))
                            
                            print("Calculating differences...")
                            server_state = path_to_dict(MUSIC_PATH)
                            differences = findDiff(host_dict, server_state)
                            
                            diff_json_bytes = json.dumps(differences).encode('utf-8')
                            length_prefix = struct.pack('!I', len(diff_json_bytes))
                            conn.sendall(length_prefix + diff_json_bytes)
                            print(f"Sent {len(differences)} mismatches to host.")

                        elif msg_type == TYPE_MP3:
                            meta_bytes = receive_exact(conn, data_len)
                            meta = json.loads(meta_bytes.decode('utf-8'))
                            
                            file_path = os.path.join(MUSIC_PATH, meta['path'])
                            file_size = meta['size']
                            
                            os.makedirs(os.path.dirname(file_path), exist_ok=True)
                            
                            print(f"Receiving file: {meta['path']} ({file_size} bytes)")
                            with open(file_path, 'wb') as f:
                                remaining = file_size
                                while remaining > 0:
                                    chunk_size = min(remaining, 4096)
                                    chunk = conn.recv(chunk_size)
                                    if not chunk:
                                        break
                                    f.write(chunk)
                                    remaining -= len(chunk)
                            print(f"Successfully saved {meta['path']}")

                except Exception as e:
                    print(f"Error handling connection from {addr}: {e}")
                
                print("Waiting for next connection...")
            except KeyboardInterrupt:
                print("\nServer shutting down.")
                break
            except Exception as e:
                print(f"Critical server error: {e}")

def path_to_dict(path): 
    name = os.path.basename(path)

    if not os.path.exists(path):
        return {"name": name, "type": "directory", "children": []}

    if os.path.isfile(path):
        return {"name": name, "type": "file"}
        
    if os.path.isdir(path):
        return {
            "name": name,
            "type": "directory",
            "children": [path_to_dict(os.path.join(path, x)) for x in os.listdir(path)]
        }


start_server()
