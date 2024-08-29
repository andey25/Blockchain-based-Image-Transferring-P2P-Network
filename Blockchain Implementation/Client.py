import socket
from uuid import uuid4
import struct
import threading
import random
from blockchain import Blockchain, Block, Transaction
import sys
from time import sleep
from enum import Enum
from hashlib import sha256
import customtkinter
from PIL import Image, ImageTk
import tkinter as tk
from tkinter import filedialog
import io
import os
from argparse import ArgumentParser


class MessageType(str, Enum):
    """
    Enum for message types to be used as headers
    """
    BLOCKCHAIN_REQUESTED = "SBC"
    NEW_BLOCK = "NBL"
    NEW_TRANSACTION = "NTR"
    NEW_DIFFICULTY = "NDF"
    NEW_IMAGE = "SIM"
    GET_IMAGE = "GIM"
    ALL_OK = "AOK"
    FAILURE = "FLR"
    END = "END"

class Client:
    def __init__(self, host, port, tracker_host, tracker_port, client_type=""):
        """
        Initialize the client
        :param host: The host to bind the client to
        :param port: The port to bind the client to
        :param tracker_host: The host of the tracker
        :param tracker_port: The port of the tracker
        """

        # Setup the socket to the tracker
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        # Setup the listener socket
        self.listener_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.listener_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        
        self.running = True

        self.listener_sock.bind((host, 0))
        self.listener_sock.listen()
        self.listen_port = self.listener_sock.getsockname()[1]
        
        # diffs is for a consensus on the difficulty
        self.diffs = {}
        # storage stores the image data
        self.storage = {}

        print(f"Listening on {host}:{self.listen_port}")
        
        # Connect to the tracker, login and connect to peers
        self.sock.bind((host, port))
        self.sock.connect((tracker_host, tracker_port))
        self.login()
        self.get_peers()
        self.connect_to_peers()
        
        # Start listening for incoming connections
        threading.Thread(target=self.handle_connections).start()
        
        # Get the blockchain from the peers
        self.get_blockchain()
        self.current_block = Block([], self.blockchain.last_hash)
        
        # Start the mining thread (It does not necessarily mine)
        threading.Thread(target=self.mine).start()
        
        if client_type == "gui":
            self.frontend()
        elif client_type == "cli":
            self.cli()
        # elif client_type == "both":
        #     threading.Thread(target=self.frontend).start()
        #     self.cli()

        # The above 3 lines have been commented out because of MacOs's infrastructure. Mac might run into 
        # certain threading issues that linux does not. This code is totally functional to run both GUI and CLI
        # at the same time, but not on mac, on Linux. If you have Linux, you can uncomment the 3 lines and 
        # use the client type positional argument "both" when running client.py.
        
        else:
            while True:
                sleep(1)        
    
    def cli(self):
        while True:
            command = input("Enter command: ")
            if command == "exit":
                self.running = False
                sys.exit(0)
            elif command == "create":
                image_path = input("Enter path to image: ")
                with open(image_path, "rb") as f:
                    image_data = f.read()
                self.create_nft(image_data)
            elif command == "transfer":
                image_id = input("Enter image id: ")
                recipient_id = input("Enter recipient id: ")
                self.transfer_nft(image_id, recipient_id)
            elif command == "get":
                image_id = input("Enter image id: ")
                image_data = self.get_image(image_id)
                if image_data:
                    with open(f"{image_id}", "wb") as f:
                        f.write(image_data)
                else:
                    print("Image not found.")
            elif command == "chain":
                print(self.blockchain)
            elif command == "images":
                for image in self.blockchain.all_images():
                    print(f"Image ID: 0x{image}, Owner: 0x{self.blockchain.find_owner(image)}")
            elif command == "me":
                print(f"User ID: 0x{self.user_id}, Username: {self.username}")
                for image in self.blockchain.find_images(self.user_id):
                    print(f"Image ID: 0x{image}")
            else:
                print("Unknown command.")
                
    def login(self):
        """
        Connect to the tracker
        """
        # Get the first chunk of data
        data = self.sock.recv(64)
        if data == b"NEW":
            # If user is not in the database
            self.user_id = uuid4().hex
            self.username = input("Enter your username: ")
        else:
            # If user is found in the database
            user_id, username = struct.unpack("!32s32s", data)
            self.user_id = user_id.decode()
            self.username = username.decode().strip("\x00")
            confirm = input(f"Welcome back, {self.username}. Is this you? (Y[es]/N[o]): ")
            while confirm.lower() not in ["y", "n", "yes", "no"]:
                confirm = input("Please enter Y[es]/N[o]: ")
            if confirm.lower() in ["n", "no"]:
                self.user_id = uuid4().hex
                self.username = input("Enter your username: ")

        # Send the tracker the data about listening port and confirm user_id and username
        self.sock.sendall(struct.pack("!32s32sH", self.user_id.encode(), self.username.encode(), self.listen_port))            
        print(f"Logged in as, {self.username}")

    def get_peers(self):
        """
        Get the list of peers from the tracker
        """

        data = self.sock.recv(4)
        count = struct.unpack("!I", data)[0]
        self.peers = {}
        for _ in range(count):
            data = self.sock.recv(70)
            ip = ".".join(map(str, struct.unpack("!BBBB", data[:4])))
            port, user_id, username = struct.unpack("!H32s32s", data[4:])
            user_id = user_id.decode().strip("\x00")
            username = username.decode().strip("\x00")
            self.peers[(ip, port)] = {
                "user_id": user_id,
                "username": username
            }

    def connect_to_peers(self):
        """
        Connects to all the peers received from the tracker
        Blocks until all connections are established or failed
        """
        threads = []
        for peer in self.peers:
            t = threading.Thread(target=self.connect_to_peer, args=(peer,))
            t.start()
            threads.append(t)
        for thread in threads:
            thread.join()
        
        print(f"Connected to {len(self.peers)} peers.")

    def connect_to_peer(self, peer):
        """
        Threaded function to connect to a peer
        """
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.connect(peer)
        # Sends the user_id, username and listen_port to the peer and waits for acknowledgment
        sock.sendall(struct.pack("!32s32sH", self.user_id.encode(), self.username.encode(), self.listen_port))
        data = sock.recv(3)
        try:
            if data == MessageType.ALL_OK.encode():
                # Store the connection if the peer acknowledges
                self.peers[peer]["sock"] = sock
            else:
                # Remove the peer in case of any failure
                self.peers.pop(peer)
                sock.close()
        except (ConnectionAbortedError, ConnectionResetError):
            # Remove the peer if it is disconnected
            self.peers.pop(peer)
    
    def handle_connections(self):
        """
        Accepts incoming connections and creates a new thread to handle each connection
        """
        while True:
            self.listener_sock.settimeout(2)
            try:
                conn, addr = self.listener_sock.accept()
                threading.Thread(target=self.handle_connection, args=(conn, addr)).start()
            except socket.timeout:
                if not self.running:
                    return

    def send_message(self, peer, message):
        """
        Sends a message to a peer and removes the peer if the connection is closed
        """
        try:
            self.peers[peer]["sock"].sendall(message)
        except (ConnectionAbortedError, ConnectionResetError):
            self.peers.pop(peer)

    def broadcast(self, message, exclude=None):
        """
        Broadcasts a message to all peers except the excluded one
        """
        for peer in self.peers:
            if peer == exclude:
                continue
            threading.Thread(target=self.send_message, args=(peer, message)).start()

    def handle_connection(self, conn, addr):
        """
        Handles the connection from a new user
        """
        # First receive the data from the new user
        data = conn.recv(66)
        user_id, username, listen_port = struct.unpack("!32s32sH", data)
        user_id = user_id.decode().strip("\x00")
        username = username.decode().strip("\x00")

        # If this user is connecting back to client's listening port after
        # client has connected to the user's listening port, then ignore
        if (new_adrr := (addr[0], listen_port)) not in self.peers:
            self.peers[(addr[0], listen_port)] = {
                "user_id": user_id,
                "username": username
            }
            threading.Thread(target=self.connect_to_peer, args=(new_adrr,)).start()
        
        # Send acknowledgment to the new user and continues listening
        try:
            conn.sendall(MessageType.ALL_OK.encode())
            while True:
                if not self.running:
                    return
                
                data = conn.recv(3) # Receive the message type header

                if data == MessageType.BLOCKCHAIN_REQUESTED.encode():
                    conn.sendall(self.blockchain.to_struct() + MessageType.END.encode())
                    continue

                if data == MessageType.NEW_TRANSACTION.encode():
                    data = b''
                    while not data.endswith(MessageType.END.encode()):
                        data += conn.recv(1024)
                    transaction = Transaction.from_struct(data[:-3])
                    self.add_transaction(transaction)
                    continue

                if data == MessageType.NEW_BLOCK.encode():
                    data = b''
                    while not data.endswith(MessageType.END.encode()):
                        data += conn.recv(1024)
                    block = Block.from_struct(data[:-3])
                    success = self.receive_block(block)
                    if success:
                        conn.sendall(MessageType.ALL_OK.encode())
                    else:
                        conn.sendall(MessageType.FAILURE.encode())
                    continue

                if data == MessageType.NEW_IMAGE.encode():
                    data = b''
                    while not data.endswith(MessageType.END.encode()):
                        data += conn.recv(1024)
                    image_id = data[:64].decode()
                    image_data = data[64:-3]
                    self.receive_image(image_id, image_data)
                    continue

                if data == MessageType.GET_IMAGE.encode():
                    image_id = conn.recv(64).decode()
                    if image_id in self.storage:
                        conn.sendall(self.storage[image_id] + MessageType.END.encode())
                    else:
                        conn.sendall(MessageType.FAILURE.encode())
                    continue

                if data == MessageType.NEW_DIFFICULTY.encode():
                    data = conn.recv(2)
                    difficulty = struct.unpack("!H", data)[0]
                    self.update_difficulty(difficulty)
                    continue

                if data == b"":
                    print(f"Connection from {addr} closed")
                    break

                print(f"Unknown message {data} received from {addr}")

        except (ConnectionAbortedError, ConnectionResetError):
            print(f"Connection from {addr} closed")
            self.peers.pop(addr)
            conn.close()
    
    def get_blockchain(self):
        """
        Get the blockchain from the peers. The blockchain fetch works in a consensus manner.
        If there is no peer, then client will create a new one
        If there is only one peer, then client will fetch the blockchain from that peer
        If there is more than one peer, then client will select two random peers and fetch the blockchain from them
            If the blockchains received are different, it means that there is a possible fork. Client will wait for 2 seconds and try again
        If the blockchains received are the same, then client will use that blockchain
        """

        if not self.peers:
            print("No peers found. Creating a new blockchain.")
            self.blockchain = Blockchain(3)
            print(f"Blockchain created. First block: 0x{self.blockchain.last_hash}")
            return
        
        if len(self.peers) == 1:
            peers = list(self.peers.keys())
        else:
            peers = random.sample(list(self.peers.keys()), 2)
        chains = set()

        for peer in peers:
            self.send_message(peer, MessageType.BLOCKCHAIN_REQUESTED.encode())
            data = b''
            while not data.endswith(MessageType.END.encode()):
                data += self.peers[peer]["sock"].recv(1024)
            
            chains.add(data)
        
        if len(chains) != 1:
            sleep(2) # Wait till other peers have sorted out the blockchain
            self.get_blockchain()
        
        self.blockchain = Blockchain.from_struct(chains.pop())
        print(f"Blockchain received. Last block: 0x{self.blockchain.last_hash}")

    def save_image(self, image_data):
        """
        Saves the image data, broadcasts the image to all peers and returns the image id
        """
        image_id = sha256(image_data).hexdigest()
        self.storage[image_id] = image_data
        self.broadcast(MessageType.NEW_IMAGE.encode() + image_id.encode() + image_data + MessageType.END.encode())
        return image_id
    
    def get_image(self, image_id):
        """
        Given an image id, fetches the image data

        First, it checks if the image is already stored in the client's storage
        If not, client picks a random peer and requests the image data
            Client continues to ask other peers until it finds the image data or all peers are exhausted
        """
        if image_id in self.storage:
            return self.storage[image_id]
        
        peers = list(self.peers.keys())
        random.shuffle(peers)
        for peer in peers:
            conn = self.peers[peer]["sock"]
            conn.sendall(MessageType.GET_IMAGE.encode() + image_id.encode())
            data = conn.recv(3)

            if data == MessageType.FAILURE.encode():
                continue

            image_data = data

            while not image_data.endswith(MessageType.END.encode()):
                image_data += conn.recv(1024)
            self.storage[image_id] = image_data

            return image_data

        return None
    
    def add_transaction(self, transaction, own=False):
        """
        Adds a transaction to the current block and starts mining
        Optionally sends the transaction to all peers if applicable
        """
        if not self.current_block.stop and len(self.current_block.transactions) > 0: # If the block is already mining
            self.current_block._stop()
            
        self.current_block.add_transaction(transaction)
        self.current_block.mine(self.blockchain.difficulty)
        
        if own:
           self.broadcast(MessageType.NEW_TRANSACTION.encode() + transaction.to_struct() + MessageType.END.encode())

    def create_nft(self, image_data):
        """
        Given the image data, creates an NFT and adds it to the blockchain
        """
        image_hash = sha256(image_data).hexdigest()
        for image in self.blockchain.all_images():
            if image_hash == image:
                print(f"Image is already owned by 0x{self.blockchain.find_owner(image_hash)}.")
                return False
            
        image_id = self.save_image(image_data)
        transaction = Transaction(self.user_id, self.user_id, image_id)
        self.add_transaction(transaction, True)
        return True
        

    def transfer_nft(self, image_id, recipient_id):
        """
        Given the image id and recipient id, transfers the NFT to the recipient
        Client must be the owner of the NFT to transfer it
        """

        if self.blockchain.find_owner(image_id) != self.user_id:
            print(f"The image is owned by 0x{self.blockchain.find_owner(image_id)}")
            return False
        
        transaction = Transaction(self.user_id, recipient_id, image_id)
        self.add_transaction(transaction, True)
        return True

    def send_block(self, block):
        """
        Utility function to broadcast a block to all peers
        """
        message = MessageType.NEW_BLOCK.encode() + block.to_struct() + MessageType.END.encode()
        results = {"success": 0, "failure": 0}
        for peer in self.peers:
            self.peers[peer]["sock"].sendall(message)
            data = self.peers[peer]["sock"].recv(3)
            if data == MessageType.ALL_OK.encode():
                results["success"] += 1
            else:
                results["failure"] += 1

        if results["success"] < results["failure"]:
            self.get_blockchain()


    def update_difficulty(self, difficulty = None):
        """
        Utility function to run everytime a new block is mined or received
        This checks whether the difficulty will be updated or not
        """

        if difficulty is None:
            changed, difficulty = self.blockchain.adjust_difficulty()
            if not changed:
                return
            self.broadcast(MessageType.NEW_DIFFICULTY.encode() + struct.pack("!H", difficulty))
        
        self.diffs[difficulty] = self.diffs.get(difficulty, 0) + 1
        if self.diffs[difficulty] > len(self.peers) // 2:
            self.blockchain.difficulty = difficulty
            self.diffs = {}

    def receive_block(self, block):
        """
        Receives a block from a peer and adds it to the blockchain
        """
        if self.blockchain.add_block(block):
            self.current_block._stop()
            self.current_block = Block([], self.blockchain.last_hash)
            self.update_difficulty()
            return True
        else:
            return False
        
    def receive_image(self, image_id, image_data):
        """
        Receives an image from a peer and stores it
        """

        self.storage[image_id] = image_data
        return True
        
    def mine(self):
        """
        Threaded function to check for mined block. This does not mine a block
        but rather updates difficulty, sends mined blocks to other users etc
        """
        while True:
            if self.current_block.hash:
                print("Block mined.")
                mine_success = self.blockchain.add_block(self.current_block)
                if not mine_success:
                    self.get_blockchain()
                    continue
                self.send_block(self.current_block)
                self.current_block = Block([], self.blockchain.last_hash)
                self.update_difficulty()
            sleep(0.01)
            if not self.running:
                for peer in self.peers:
                    try:
                        self.peers[peer]["sock"].close()
                    except:
                        pass
    
    def create_image(self):

        cwd = os.getcwd()

        file_path = filedialog.askopenfilename(
            title="Select an Image",
            filetypes=[
                ("PNG Files", "*.png"),
                ("JPG Files", "*.jpg"),
                ("JPEG FIles", "*.jpeg")
            ],
            initialdir= cwd + "/images"
        )
        
        if file_path:
            with open(file_path, 'rb') as file:
                image_data = file.read()
            success = self.create_nft(image_data)
            
        else:
            raise Exception
        
    def transfer_image(self):
        image_id = input("Enter image id: ")
        recipient_id = input("Enter recipient id: ")
        success = self.transfer_nft(image_id, recipient_id)
       
        
    def frontend(self):
        interface = customtkinter.CTk()
        interface.title("Anik's Blockchain Network")
        interface.geometry("900x650")
        interface_background = "#20232A"
        interface.configure(bg=interface_background)

        interface.grid_columnconfigure(1, weight=1)
        interface.grid_rowconfigure(1, weight=1)

        # Welcome Frame
        welcome_label = customtkinter.CTkLabel(interface, text=f"Welcome, {self.username} (ID: 0x{self.user_id})!", font=('Arial', 20))
        welcome_label.grid(row=0, column=0, columnspan=3, pady=(20, 20), sticky="ew")

        def terminate():
            self.running = False
            interface.destroy()
            interface.quit()

        def refresh_peers():
            if not self.running:
                interface.destroy()
                interface.quit()
                return
            
            number_users_label.configure(text=f"Active peers: {len(self.peers)}")  
            user_list.delete(0, tk.END)  
            for _, user_info in self.peers.items():
                user_list.insert(tk.END, user_info["username"]) 
            interface.after(250, refresh_peers)

        # Frame1 for Actions
        frame1 = customtkinter.CTkFrame(interface, width=200, corner_radius=10, bg_color=interface_background)
        frame1.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")
        frame1.grid_rowconfigure(4, weight=1)

        nft_create_button = customtkinter.CTkButton(frame1, text="Create NFT", command=self.create_image)
        nft_create_button.grid(row=1, column=0, pady=10, padx=10, sticky="ew")

        nft_transfer_button = customtkinter.CTkButton(frame1, text="Transfer NFT", command=self.transfer_image)
        nft_transfer_button.grid(row=2, column=0, pady=10, padx=10, sticky="ew")

        terminate_button = customtkinter.CTkButton(frame1, text="Exit", command=terminate)
        terminate_button.grid(row=3, column=0, pady=10, padx=10, sticky="ew")

        # Frame2 for Image Display
        frame2 = customtkinter.CTkFrame(interface, width=500, corner_radius=10, bg_color=interface_background)
        image_filter = customtkinter.CTkSegmentedButton(frame2, values=["Owned", "All"], font=('Arial', 16))
        image_filter.grid(row=0, column=0, padx=20, pady=10, sticky="nsew")
        image_filter.set("Owned") # Default to 'Owned'

        frame2.grid(row=1, column=1, padx=10, pady=10, sticky="nsew")
        frame2.grid_rowconfigure(1, weight=1)
        frame2.grid_columnconfigure(0, weight=1)

        img_canvas = tk.Canvas(frame2)
        img_canvas.grid(row=1, column=0, sticky="nsew")

        img_scrollbar = customtkinter.CTkScrollbar(frame2, command=img_canvas.yview)
        img_scrollbar.grid(row=1, column=1, sticky="ns")

        def adjust_canvas(event):
            canvas_width = event.width
            img_canvas.itemconfig("container", width=canvas_width)

        img_canvas.bind("<Configure>", adjust_canvas)

        img_frame = customtkinter.CTkFrame(img_canvas)
        img_canvas.create_window((0, 0), window=img_frame, anchor='nw')

        # Frame3 for User List
        frame3 = customtkinter.CTkFrame(interface, width=200, corner_radius=10, bg_color=interface_background)
        frame3.grid(row=1, column=2, padx=10, pady=10, sticky="ns")
        number_users_label = customtkinter.CTkLabel(frame3, text="Active peers: 0", fg_color="#404040", text_color="#FFFFFF", height=25, font=('Arial', 15))
        number_users_label.grid(row=0, column=0, sticky="nsew", pady=10, padx=10)

        user_list = tk.Listbox(frame3, bg="#333333", fg="white", borderwidth=0, highlightthickness=0, selectbackground="#4e5a65", font=('Arial', 15))
        user_list.grid(row=1, column=0, sticky="nsew", pady=10, padx=10)

        img_canvas.configure(yscrollcommand=img_scrollbar.set)

        def screenshow():
            img_canvas.update_idletasks()
            canvas_width = img_canvas.winfo_width()

            for widget in img_frame.winfo_children():
                widget.destroy()

            image_stack = []
            for image in self.blockchain.all_images():
                user_name = f"0x{self.blockchain.find_owner(image)}"
                image_id = f"0x{image}"
                image_data = self.get_image(image)
                if image_data:
                    img = Image.open(io.BytesIO(image_data))
                    image_stack.insert(0, (user_name, image_id, img))

            row = 0
            selected_filter = image_filter.get()
            i = 0
            for (user_name, image_id, img) in image_stack:
                if selected_filter == "Owned" and user_name != f"0x{self.user_id}":
                    continue

                if i == 0:
                    img_canvas.grid()

                col = i % 2

                scaled_width = canvas_width // 2 - 30
                scaled_height = int((scaled_width / img.width) * img.height)
                img = img.resize((scaled_width, scaled_height), Image.LANCZOS)
                tk_thumb = ImageTk.PhotoImage(img)

                thumbnail_label = tk.Label(img_frame, image=tk_thumb)
                thumbnail_label.image = tk_thumb
                thumbnail_label.grid(row=row, column=col, padx=10, pady=10)

                owner_label = tk.Label(img_frame, text=f"Owner: {user_name}           Image ID: {image_id}",
                                    bg="#DBDBDB", fg="#3B8ED0", font=('Arial', 12, "bold"))
                owner_label.grid(row=row + 1, column=col, sticky="ew", padx=10)
                i += 1
                if col == 1:
                    row += 2

            img_canvas.configure(scrollregion=img_canvas.bbox('all'))  # Update scroll region after changes

            if i == 0:
                img_canvas.grid_remove()

            interface.after(1000, screenshow)

        screenshow()
        refresh_peers()
        interface.mainloop()

if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument("port", type=str, help="Port to bind the client to")
    parser.add_argument("tracker_host", type=str, help="Host of the tracker")
    parser.add_argument("tracker_port", type=str, help="Port of the tracker")
    parser.add_argument("client_type", type=str, help="Type of client (cli/gui)", choices=["cli", "gui"], default="none")
    args = parser.parse_args()
    client = Client("", int(args.port), args.tracker_host, int(args.tracker_port), args.client_type)
