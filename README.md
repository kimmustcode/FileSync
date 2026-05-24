# FileSync

FileSync is a lightweight, socket-based tool designed to synchronize music files (specifically `.mp3`) between a host and a server. It efficiently identifies missing files on the server by comparing folder structures and then uploads only the necessary files.

## Features

- **Recursive Directory Sync**: Synchronizes entire directory trees.
- **Delta-Based Updates**: Only uploads files that are missing on the server.
- **Lightweight Communication**: Uses a custom socket protocol with JSON for metadata and raw bytes for file transfers.
- **Easy Configuration**: Simple Python scripts with minimal dependencies.

## Prerequisites

- Python 3.x

## Configuration

Before running the scripts, you need to configure the paths and IP addresses in both `host.py` and `server.py`.

### Server Configuration (`server.py`)
Edit the `MUSIC_PATH` variable to point to the directory where you want to store the synced music:
```python
MUSIC_PATH = "C:/Path/To/Your/Server/Music"
```

### Host Configuration (`host.py`)
1. Edit `musicFolder` to point to your local music directory:
   ```python
   musicFolder = Path('C:/Path/To/Your/Local/Music')
   ```
2. Set `serverip` to the local IP address of your server:
   ```python
   serverip = '192.168.1.X' 
   ```

## Usage

### 1. Start the Server
Run the server script on the machine that will receive the files:
```bash
python server.py
```
The server will start listening on port `8056`.

### 2. Run the Host
Run the host script on the machine containing the music you want to sync:
```bash
python host.py
```

The host will:
1. Scan its local directory.
2. Send the directory structure to the server.
3. Receive a list of missing files.
4. Upload each missing `.mp3` file to the server.

## How it Works

1. **Handshake**: The host connects to the server and sends a JSON map of its local directory structure (Message Type `0`).
2. **Difference Calculation**: The server compares the host's map with its own local directory and returns a JSON list of missing files.
3. **File Transfer**: The host iterates through the list of missing files and sends each one individually (Message Type `1`), prefixed with metadata (path and size).
4. **Reconstruction**: The server receives the files and recreates the directory structure as needed.

## Protocol Details

The tool uses a simple header-based protocol:
- **Header**: 5 bytes (`!BI`)
  - 1 byte: Message Type (`0` for JSON list, `1` for MP3)
  - 4 bytes: Data Length (Unsigned Int)
- **Payload**: The actual JSON metadata or file data.
