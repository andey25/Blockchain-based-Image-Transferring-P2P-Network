from hashlib import sha256
from datetime import datetime
from time import time_ns, sleep
import struct
from uuid import uuid4
import threading

LOCK = threading.Lock()

class Transaction:
    """
    A transaction object that represents the transfer of an image from one user to another
    If sender and receiver is the same, it means that the image is mined by the user
    """
    def __init__(self, sender, receiver, image_id, timestamp = None):
        """
        sender: 32 byte hex
        receiver: 32 byte hex
        image_id: 64 byte (hash of the image)
        """
        self.sender = sender
        self.receiver = receiver
        self.image_id = image_id
        self.timestamp = timestamp if timestamp else time_ns()
        self.hash = sha256(self.to_struct()).hexdigest()

    @property
    def trx_time(self):
        """
        Returns the transaction time in a human readable format
        """
        return datetime.fromtimestamp(self.timestamp / 1e9)
    
    @staticmethod
    def from_struct(data):
        """
        Unpacks binary data and returns a Transaction object
        """
        sender, receiver, image_id, timestamp = struct.unpack('!32s32s64sQ', data)
        return Transaction(sender.decode(), receiver.decode(), image_id.decode(), timestamp)

    def to_struct(self):
        """
        Packs the transaction data into a binary fixed length format for sharing over the network
        """
        return struct.pack(
            '!32s32s64sQ', 
            self.sender.encode(), 
            self.receiver.encode(), 
            self.image_id.encode(), 
            self.timestamp
        )

    def __repr__(self):
        return f"0x{self.sender} -> 0x{self.receiver}: 0x{self.image_id} at {self.trx_time}"
    
class MerkleTree:
    """
    A merkle tree implementation for internal representation of transactions inside a block
    """

    def __init__(self, transactions):
        """
        transactions: list of Transaction objects. Can be empty
        """
        _transactions = [tx.hash for tx in transactions]
        
        # A 2D list where each element is a layer of the tree
        # The first layer is the list of transactions and the last layer is the root 
        self.tree = self.build_tree(_transactions)
    
    def build_tree(self, transactions):
        """
        Builds the merkle tree from the list of transactions
        """

        if len(transactions) == 0:
            # If there is no element, return an empty hash
            return [[sha256().hexdigest()]]
        
        tree = [transactions]

        while len(tree[-1]) > 1:
            _layer = tree[-1].copy()
            if len(_layer) % 2 != 0:
                _layer.append(_layer[-1]) # If the number of transactions is odd, duplicate the last transaction

            new_layer = []
            for i in range(0, len(_layer), 2):
                hasher = sha256()
                hasher.update(_layer[i].encode())
                hasher.update(_layer[i+1].encode())
                new_layer.append(hasher.hexdigest())
            tree.append(new_layer)
        return tree
    
    def add_transaction(self, transaction):
        """
        Adds a new transaction to the tree and rebuilds it
        """
        transactions = self.tree[0].copy()
        transactions.append(transaction.hash)
        self.tree = self.build_tree(transactions)
    
    def __repr__(self):
        str = ""
        for i, layer in enumerate(self.tree):
            str += f"Layer {i}: {layer}\n"
        return str
    
class Block:
    """
    Representation of each block in the blockchain
    """
    def __init__(self, transactions, previous_hash: str = None, timestamp: int = None):
        """
        transactions: list of Transaction objects, can be empty
        previous_hash: 64 byte hex string
        timestamp: int, unix timestamp in nanoseconds
        """

        self.previous_hash = previous_hash
        self.transactions = transactions
        self.timestamp = timestamp if timestamp else time_ns()
        self.tree = MerkleTree(transactions)
        self.markle_root = self.tree.tree[-1][0]
        self.nonce = uuid4().hex
        self.hash = None
        self.stop = False
        self.mining_thread = None

    @property
    def block_time(self):
        return datetime.fromtimestamp(self.timestamp / 1e9)
    
    def hash_str(self):
        trx_num = len(self.transactions) # Transaction count is needed because number of transactions is not fixed
        header = struct.pack('!64sQ32sL', self.previous_hash.encode(), self.timestamp, self.nonce.encode(), trx_num)
        transactions = b''.join([tx.to_struct() for tx in self.transactions])
        return header + transactions
    
    def _hash(self):
        """
        Hashes the block with a nonce and returns the hash
        """
        string = self.hash_str()
        hasher = sha256(string)
        return hasher.hexdigest()
    
    def _mine(self, difficulty: int):
        """
        Starts mining a block with a given difficulty
        """
        # Nonce is a random 32 byte hex string
        # This was used so that all clients do not mine the same numbers
        self.nonce = uuid4().hex
        self.timestamp = time_ns()
        while self._hash()[:difficulty] != '0' * difficulty:
            self.nonce = uuid4().hex
            self.timestamp = time_ns()
            sleep(0.00001) # Sleep for a while to avoid CPU hogging
            if self.stop:
                break
        else:
            # Mining is successful, update the block with the data
            self.hash = self._hash()
            LOCK.acquire()
            self.stop = True
            self.mining_thread = None
            LOCK.release()
            return

    
    def mine(self, difficulty: int):
        """
        Wrapper function to start the mining thread
        """
        LOCK.acquire()
        self.mining_thread = threading.Thread(target=self._mine, args=(difficulty,))
        self.mining_thread.start()
        self.stop = False
        LOCK.release()
    
    def add_transaction(self, transaction: Transaction):
        """
        Adds a transaction to the internal merkle tree and updates the markle root
        """
        self.transactions.append(transaction)
        self.tree.add_transaction(transaction)
        self.markle_root = self.tree.tree[-1][0]

    def to_struct(self):
        """
        Packs the block data into a binary format for sharing over the network
        """
        trx_num = len(self.transactions) # Transaction count is needed because number of transactions is not fixed
        header = struct.pack('!64sQ64s32sL', self.previous_hash.encode(), self.timestamp, self.hash.encode(), self.nonce.encode(), trx_num)
        transactions = b''.join([tx.to_struct() for tx in self.transactions])
        return header + transactions
    
    def _stop(self):
        """
        Stops the mining thread
        """
        # acquire the lock and set the stop flag to True
        LOCK.acquire()
        self.stop = True
        if self.mining_thread:
            self.mining_thread.join()
            self.mining_thread = None
        LOCK.release()
    
    @staticmethod
    def from_struct(data):
        """
        Unpacks a given binary data and returns a Block object
        """
        previous_hash, timestamp, block_hash, nonce, trx_num = struct.unpack('!64sQ64s32sL', data[:172])
        previous_hash = previous_hash.decode()
        timestamp = timestamp
        nonce = nonce.decode()
        transactions = []
        for i in range(trx_num):
            trx = Transaction.from_struct(data[172 + i * 136:172 + (i+1) * 136])
            transactions.append(trx)
        block = Block(transactions, previous_hash, timestamp)
        block.nonce = nonce
        block.hash = block_hash.decode()
        return block
    
    @staticmethod
    def trx_num_from_struct(data):
        """
        Gets the number of transactions from the block header
        """
        _, _, _, _, trx_num = struct.unpack('!64sQ64s32sL', data)
        return trx_num        

    def __repr__(self):
        return f"Block: 0x{self.hash}\nTimestamp: {self.block_time}\nNonce: 0x{self.nonce}\nMerkle Root: 0x{self.markle_root}"

class Blockchain:
    """
    Representation of the blockchain that holds all the blocks
    """
    def __init__(self, difficulty: int = 4, chain=list()):
        """
        Creates a new blockchain object
        difficulty: int, mining difficulty, default is 4
        chain: list of Block objects, default is empty
        """
        self.difficulty = difficulty
        self.chain: list[Block] = chain
        if not chain:
            self.create_genesis_block()

    def create_genesis_block(self):
        genesis = Block([], '0' * 64) # Genesis block cannot have a tranasction or previous hash
        genesis.mine(3) # Mining difficulty is kept low for the genesis block
        while not genesis.stop:
            sleep(0.0001) # Sleep for a while to avoid CPU hogging
            pass
        self.chain.append(genesis)

    def add_block(self, block: Block):
        """
        Checks a block and adds it to the chain if it is valid
        """
        block_hash = block._hash()
        if block_hash != block.hash:
            # If the block hash is not the same as the hash generated by the block
            print(block_hash, block.hash)
            return False
        
        if len(self.chain) > 1 and block.previous_hash == self.chain[-2].hash:
            # If the block hash a previous hash that is the block before the last one,
            # we accept the one that was mined earlier
            if self.chain[-1].timestamp < block.timestamp:
                return False
            self.chain[1] = block
            return True

        if block.previous_hash != self.chain[-1].hash or block.hash[:self.difficulty] != '0' * self.difficulty:
            # If the previous hash does not match or the block hash does not meet the difficulty requirement
            return False
        
        self.chain.append(block)
        return True
    
    def adjust_difficulty(self):
        """
        Helper function to check if the diffculty needs to be adjusted
        returns True, new_difficulty if the difficulty is adjusted
        return False, old_difficulty if the difficulty is not adjusted
        """
        # check the last 25 blocks
        # if the average time is less than 5 seconds, increase the difficulty by 1
        # if the average time is greater than 15 seconds, decrease the difficulty by 1
        if len(self.chain) < 25:
            return False, self.difficulty
        last_25 = self.chain[-25:]
        times = [block.timestamp for block in last_25]
        avg_time = (times[-1] - times[0]) / 25
        diff = self.difficulty
        if avg_time < 5:
            diff += 1
            return True, diff
        elif avg_time > 15:
            self.difficulty -= 1
            return True, diff
        return False, self.difficulty

    @property
    def last_hash(self):
        return self.chain[-1].hash

    def to_struct(self):
        """
        Packs the blockchain data into a binary format
        """
        meta = struct.pack('!HL', self.difficulty, len(self.chain))
        return meta + b''.join([block.to_struct() for block in self.chain])
    
    @staticmethod
    def from_struct(data):
        """
        Unpacks the binary data and returns a Blockchain object
        """
        chain = []
        difficulty, block_num = struct.unpack('!HL', data[:6])
        data = data[6:]
        for _ in range(block_num):
            block_header = data[:172]
            data = data[172:]
            trx_num = Block.trx_num_from_struct(block_header)
            trx_num = int(trx_num)
            block = Block.from_struct(block_header + data[:trx_num * 136])
            data = data[trx_num * 136:]
            chain.append(block)
        bc = Blockchain(difficulty, chain)
        bc.chain = chain
        return bc
    
    def find_images(self, user_id: str):
        """
        Returns all the images that are owned by a user
        """
        images = []
        for block in self.chain:
            for trx in block.transactions:
                if trx.receiver == user_id:
                    images.append(trx.image_id)
        return images
    
    def all_images(self):
        """
        Returns all images that are in the blockchain
        """
        images = set()
        for block in self.chain:
            for trx in block.transactions:
                images.add(trx.image_id)
        return list(images)
    
    def find_owner(self, image_id: str):
        """
        Given an image id, returns the owner of the image
        """
        for block in self.chain[::-1]:
            for trx in block.transactions:
                if trx.image_id == image_id:
                    return trx.receiver
        return None

    def __repr__(self):
        string = "Number of Blocks: {}\n".format(len(self.chain))
        for block in self.chain:
            string += f"{block}\n"
        return string


if __name__ == "__main__":
    txs = [Transaction(uuid4().hex, uuid4().hex, sha256(str(i).encode()).hexdigest()) for i in range(10)]
    print(Transaction.from_struct(txs[0].to_struct()))
    chain = Blockchain(3)
    block1 = Block(txs, chain.last_hash)
    block1.mine(3)

    while not block1.stop:
        sleep(0.001)
        pass
    txs = [Transaction(uuid4().hex, uuid4().hex, sha256(str(i).encode()).hexdigest()) for i in range(10)]
    block2 = Block(txs, block1.hash)
    block2.mine(3)
    while not block2.stop:
        sleep(0.001)
        pass
    print("Block 1")
    print(block1)
    print("====================================\nBlock 2")
    print(block2)
    print("====================================")
    print(chain.add_block(block1))
    print(chain.add_block(block2))
    print("Chain Original: ")
    print(chain)
    print("===================================\nChain Struct: ")
    chain2 = Blockchain.from_struct(chain.to_struct()).to_struct() == chain.to_struct()
    print(chain2)
