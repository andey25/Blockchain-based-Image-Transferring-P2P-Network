import socket
import threading
import struct
import sys
from time import sleep

class Tracker:
    """
    Tracker keeps track of all active users and sends the list of to new users
    """
    def __init__(self, host, port):
        """
        Initialize the tracker
        :param host: The host to bind the tracker to 
        :param port: The port to bind the tracker to
        """
        self.host = host
        self.port = port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind((self.host, self.port))
        self.sock.listen()
        self.users = {}
        print(f"Tracker is listening on {self.sock.getsockname()[0]}:{self.port}")
        threading.Thread(target=self.accept_connections).start()

    def accept_connections(self):
        """
        Accepts incoming connections and creates a new thread to handle each connection
        """
        while True:
            conn, addr = self.sock.accept()
            threading.Thread(target=self.handle_connection, args=(conn, addr)).start()

    def send_active_users(self, conn, usr_addr):
        """
        Sends the list of active users to the new user
        :param conn: The connection to the new user
        :param usr_addr: The address of the new user (host, port)
        """
        data = b""
        count = 0
        for addr, user in self.users.items():
            # skip the user itself and inactive users            
            if addr == usr_addr or not user["active"]:
                continue
            count += 1
            ip, _ = addr
            port = user["listen_port"]
            user_id = user["user_id"]
            username = user["username"]
            data += struct.pack("!BBBBH32s32s", *map(int, ip.split(".")), port, user_id.encode(), username.encode())
        conn.sendall(
            struct.pack("!I", count) + data
        )

    def handle_connection(self, conn: socket.socket, addr):
        """
        Handles the connection from a new user
        """
        
        print(f"New connection from {addr}")
        try:
            if addr not in self.users:
                conn.sendall(struct.pack("!3s", "NEW".encode()))
            else:
                conn.sendall(struct.pack("!32s32s", self.users[addr]["user_id"].encode(), self.users[addr]["username"].encode()))

            res = conn.recv(66)
            user_id, username, listen_port = struct.unpack("!32s32sH", res)
            user_id = user_id.decode()
            username = username.decode().strip("\x00")
            self.users[addr] = {
                "user_id": user_id,
                "username": username,
                "listen_port": listen_port,
                "active": True
            }
            print(self.users[addr])
            self.send_active_users(conn, addr)
        
            while True:
                res = conn.recv(1) # This is to keep checking if the connection is still alive
                sleep(1)
                if res == b'': # Empty byte means connection is closed
                    self.users[addr]["active"] = False
                    print(f"Connection from {addr} closed")
                    break

        except (ConnectionAbortedError, ConnectionResetError):
            self.users[addr]["active"] = False
            print(f"Connection from {addr} closed")

if __name__ == "__main__":
    tracker = Tracker("", int(sys.argv[-1]) if len(sys.argv) > 1 else 5000)
