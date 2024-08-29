This file describes the blockchain design, p2p protocol, the demo application design.

## Additional Features Included:
1. Multiple transactions inside a block
2. Combined approach of sha256 and uuid4 hashing algorithms to ensure absolute uniqueness in ids and handle collisions
3. GUI
5. Dynamic adjustment of mining difficulty based on the available computation power
6. Transaction verification using Merkle Tree

## General Overview:

Connection Phase:
Client connects to tracker and fetch the active peer list. When new client joins, tracker sends the old active client list to it. New client connects to the old active clients listening port, then provides its username, user_id, and own listening port port. Old client connects to the port and 2-way communication gets established.

Initiation Phase:
Client fetches the latest blockchain from the peers. If the first client to join, it will create the blockchain.

Mining:
If there is no transaction in the block, mining is not allowed. Mining starts after the first transaction arrives. If a new transaction comes, mining will stop temporarily, it will add the transaction to the Merkle Tree first, then will start mining again. That's how it facilitates multiple transactions.

Mining Difficulty:
At least 25 blocks needed. Per 25 blocks, the client is going to check how long it took to mine them. if average time < 5s, difficulty will increase by 1. If average time > 15, difficulty will decrease by 1.

Collision and Forking:
Suppose in (n+1)th block, some client receives two values, then it will check the mining timestamp. It will accept the one which got mined before, as there is a considerable time difference between two blocks being mined. Thus, fork will get resolved in the first branch.

Image Saving and Transfer:
If the user of a client uploads an image, the client will send other clients an uploaded image. If a new client joins and the user of the new client wants to open the image, the new client will request the peers for the image. If it does not exist among any of the existing peers, it will fail, If yes, it will show the image. 

Creation and Transfer:
if image hash already exists in the chain, it cannot be reuplaoded or recreated, assuring uniqueness of ownership. For transferring, the client must be the owner of the image, or else it cannot transfer. But the existence of recipient is not mandatory, if it is a valid hash, it will be enough. But transferring the images within the network is immediate and will show the change. 



## Tracker.py (Tracker of the P2P Network)

### Necessary Imports: socket, threading, struct, sys, time.sleep


The Tracker's role is to manage active users in the network and coordinating the exchange of user lists with new users.

### Arguments: 
Takes 2 arguments host and port, but host is not needed when running the file as the address was not bound to any specific ip.


### Main Features and Techniques
Socket Communication: Utilizes sockets for network communication.

Multithreading: Handles multiple connections simultaneously using threads.

Data Serialization: Uses the struct module to serialize and deserialize data for transmission.

User Management: Keeps track of active and inactive users, updating their status based on connection activity.

Connection Handling: Continuously accepts new connections and handles them in separate threads.

User List Sharing: Sends the list of currently active users to new connections to keep the network updated.

### Important Functions:

_init_:
Initializes the tracker by setting up a TCP socket with the specified host and port.
Configures the socket to reuse addresses, binds it, and starts listening for incoming connections.
Begins a new thread to handle the acceptance of connections concurrently.

accept_connections:
Runs in a loop to continuously accept incoming connections from users.
For each new connection, it spawns a new thread to handle the connection, allowing simultaneous management of multiple users.

send_active_users:
Prepares and sends a binary list of currently active users (excluding the requesting user) to the newly connected user.
Uses the struct module for packing user data into a binary format suitable for network transmission.

handle_connection:
Handles all aspects of a user's connection, including initial user identification and updating the user dictionary with their details.
Sends the list of active users to the newly connected user and continuously checks if the connection is still alive.
Marks users as inactive if the connection is closed, ensuring the user list remains accurate.

## Client.py
Takes 5 input arguments, host address, port, the tracker host, the tracker port, and client type (gui or cli) to run the program.

### Main Features and Techniques
Initialization:
Sets up sockets for communication with the tracker and peers.
Binds and listens on a port for incoming connections.
Connects to the tracker to register the client and retrieve the list of peers.
Starts threads to handle incoming connections and initiate mining.

Login and Peer Connection:
Logs into the tracker, sending user details and retrieving peers.
Connects to all retrieved peers in separate threads, ensuring concurrent connections.
Keeps track of connected peers and handles peer disconnections.

Blockchain Synchronization:
Retrieves the blockchain from peers.
If peers have different blockchains (forks), it waits and retries until consensus is achieved.
Maintains the blockchain state, allowing for fetching and updating blocks.

Handling Transactions and Blocks:
Manages the creation and broadcasting of transactions to peers.
Adds transactions to the current block and starts mining.
Receives new blocks from peers, validates them, and updates the blockchain.
Ensures the mining difficulty is adjusted based on the consensus among peers.

Image Management:
Saves and broadcasts image data (NFTs) to peers.
Retrieves image data from peers when requested, ensuring data is available across the network.

Mining:
Continuously checks for mined blocks, broadcasts them to peers, and updates the blockchain.
Adjusts the mining difficulty based on the blockchain's state and peer consensus.

Fork Handling:
The get_blockchain method handles forks by fetching blockchains from multiple peers.
If different blockchains are received, it waits and retries to achieve agreement.
This ensures the client adopts the correct and consistent blockchain from the network.

Mining Difficulty Adjustment (additional feature):
The update_difficulty method adjusts the mining difficulty based on the number of peers and their feedback.
Difficulty is broadcasted to peers to ensure uniform mining conditions across the network.
Ensures the blockchain remains balanced in terms of block production time.

Multiple Transactions (additional feature):
The add_transaction method manages adding transactions to the current block and starts mining if applicable.
Transactions are broadcasted to peers, ensuring they are aware of new transactions.
Handles multiple transactions efficiently and prevents conflicts.

Graphical User Interface (additional feature):
The frontend method initializes a GUI using customtkinter for user interaction.
Provides features for creating and transferring NFTs through the interface.
Displays the list of active peers and the user's NFTs.
The GUI includes functionalities for selecting images, displays owned and all images, and updates the user interface dynamically.

<img width="1512" alt="Screenshot 2024-05-08 at 2 58 34 AM" src="https://github.com/csee4119-spring-2024/project-amethyst/assets/160454001/3221433d-01a7-4a14-af14-ed7c02e73daa">


## Blockchain.py:

### Main Features and Techniques

Hashing Algorithms (additional feature):
Uses SHA-256 for creating unique and secure hash values for transactions and blocks.
Combines SHA-256 with UUID4 to ensure that each nonce is unique, enhancing the security of the mining process.
Generates block hashes by combining transaction data, previous hash, nonce, and timestamp, ensuring the integrity and immutability of each block.

Merkle Tree (additional feature):
Utilizes a Merkle tree to efficiently and securely summarize all transactions in a block.
The root of the Merkle tree (Merkle root) is included in the block header to ensure data integrity.

Transaction Management:
Transactions represent the transfer of an image from one user to another.
Each transaction includes a sender, receiver, image ID, timestamp, and hash.

Mining and Difficulty Adjustment (addiotional feature):
Blocks are mined by finding a nonce that produces a hash with a specified number of leading zeros, determined by the difficulty level.
The mining difficulty is adjusted based on the average time taken to mine recent blocks, ensuring the network maintains a consistent block generation rate.

### Important Functions
_init_:
Initializes the blockchain with a given difficulty and an optional list of blocks.
Creates the genesis block if the chain is empty.

create_genesis_block:
Creates the first block in the blockchain (genesis block) with a predefined low difficulty level.
Mines the genesis block to initialize the blockchain.

add_block:
Validates and adds a new block to the blockchain if it meets the criteria (correct previous hash and valid proof of work).
Ensures that only valid blocks are added to maintain the integrity of the blockchain.
Recalculates the block's hash and compares it to the stored hash, ensuring no tampering has occurred.
Checks if the new block's previous hash matches the last block in the chain.
Verifies that the block meets the current difficulty requirement.
Handles potential forks by comparing timestamps of conflicting blocks and accepting the earlier mined block.

adjust_difficulty:
Adjusts the mining difficulty based on the average time taken to mine the last 25 blocks.
Increases or decreases the difficulty to maintain an average block generation time within a target range.

to_struct and from_struct:
Serializes the blockchain into a binary format for efficient network transmission.
Deserializes the binary data back into a blockchain object, facilitating data exchange between peers.

find_images and all_images:
Retrieves all images owned by a specific user or all images in the blockchain, respectively.
Useful for querying the blockchain to determine asset ownership and availability.

find_owner:
Given an image ID, returns the current owner of the image by scanning the blockchain transactions.
Provides a mechanism for verifying asset ownership within the network.


## Advantages of the Developed System:

Robust Transaction and Block Management: The system efficiently handles multiple transactions within a block, ensuring seamless and secure transaction processing using SHA-256 and UUID4 for hashing, and a Merkle tree for transaction verification.

Dynamic Mining Difficulty Adjustment: Adjusts the mining difficulty based on the computational power and average block mining time, ensuring optimal performance and network stability.

Fork Resolution and Blockchain Consistency: The system effectively resolves forks by accepting the block mined earlier based on timestamps, maintaining a consistent and reliable blockchain.

User-Friendly Interface: Provides a comprehensive GUI for easy interaction, enabling users to create, transfer, and view NFTs, and manage their blockchain activities visually.
