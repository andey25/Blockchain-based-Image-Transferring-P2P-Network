# Testing

This document provides information on how to test the system using CLI and GUI.

### Prerequisite

`tracker.py` needs to be running and its IP address should be known.

### Clients

After `tracker.py` is running, at least 1 client should be started and have the blockchain created before other clients can join. Otherwise, there will be issues receiving the blockchain and the later joining clients would have to restart.

## Test Cases
### Connection

Client 1

```bash
$ python3 client.py 5001 127.0.0.1 7000 cli

Listening on :37823
Enter your username: testuser
Logged in as, testuser
Connected to 0 peers.
No peers found. Creating a new blockchain.
Blockchain created. First block: 0x000b8c361c8039ea816998182d5f06807511926ad9eac56221f155d71bc4f4a9
Enter command: 
```

Client 2

```bash
$ python3 client.py 5002 127.0.0.1 7000 cli

Listening on :40529
Enter your username: testuser2 
Logged in as, testuser2
Connected to 1 peers.
Blockchain received. Last block: 0x000b8c361c8039ea816998182d5f06807511926ad9eac56221f155d71bc4f4a9
Enter command:
```

Client 3
    
```bash
$ python3 client.py 5000 127.0.0.1 7000 cli

Listening on :41209
Enter your username: testuser3
Logged in as, testuser3
Connected to 2 peers.
Blockchain received. Last block: 0x000b8c361c8039ea816998182d5f06807511926ad9eac56221f155d71bc4f4a9
```

The clients' `user_id`s can be found in the `tracker.py`'s console output. 

```bash
$ python3 tracker.py 7000

Tracker is listening on 0.0.0.0:7000
New connection from ('127.0.0.1', 5001)
{'user_id': '91373cabc1aa4119ad38ff9914e9420a', 'username': 'testuser', 'listen_port': 37823, 'active': True}
New connection from ('127.0.0.1', 5002)
{'user_id': '9cc819e686cc4d869b6f0455a7297f85', 'username': 'testuser2', 'listen_port': 40529, 'active': True}
New connection from ('127.0.0.1', 5000)
{'user_id': 'ce6c240e56c646ee8c70c6e114c2bb75', 'username': 'testuser3', 'listen_port': 41209, 'active': True}
```

### Mining

Next, we will create a new NFT and see the blockchain update.

Client 1

```
Enter command: create
Enter path to image: image.png
```

Any of the clients can be the first to mine the block. For this specific test case, it was Client 3.

Running `chain` command on Client 2 will show the updated blockchain.

```
Enter command: chain 
Number of Blocks: 2
Block: 0x000b8c361c8039ea816998182d5f06807511926ad9eac56221f155d71bc4f4a9
Timestamp: 2024-05-07 12:20:07.864343
Nonce: 0x406e6dae59ea43479e7eaaf859149a10
Merkle Root: 0xe3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855
Block: 0x000515ef9c1e6ad85bdae2170f1d5cb371b53708a2d65980fce0370c87422b75
Timestamp: 2024-05-07 13:18:46.161662
Nonce: 0x74025da38fc44b6ea83c93110a6eb805
Merkle Root: 0x5159bcbfcb0236000a81f9db465978596622bb8675033bdfa8464c4649d4213e
```

Running `me` command on Client 1 will show the NFTs owned by the user.

```
Enter command: me
User ID: 0x91373cabc1aa4119ad38ff9914e9420a, Username: testuser
Image ID: 0xaf65c9f5fcc16bf6328d300708fd58f22cb36c3173b8d00543c4ad089cf02be8
```

### Transfer

We will transfer the NFT from client 1 to client 2.

Client 1

```
Enter command: transfer
Enter image id: af65c9f5fcc16bf6328d300708fd58f22cb36c3173b8d00543c4ad089cf02be8
Enter recipient id: 9cc819e686cc4d869b6f0455a7297f85
Enter command: 
```

Running `me` command on Client 2 will show the NFTs owned by the user.

```
Enter command: me
User ID: 0x9cc819e686cc4d869b6f0455a7297f85, Username: testuser2
Image ID: 0xaf65c9f5fcc16bf6328d300708fd58f22cb36c3173b8d00543c4ad089cf02be8
```

`images` can be run on either of the client to verify-

```
Enter command: images
Image ID: 0xaf65c9f5fcc16bf6328d300708fd58f22cb36c3173b8d00543c4ad089cf02be8, Owner: 0x9cc819e686cc4d869b6f0455a7297f85
```

### Download
On either client, `get` can be used and the image will be downloaded to the current directory.

```
Enter command: get 
Enter image id: af65c9f5fcc16bf6328d300708fd58f22cb36c3173b8d00543c4ad089cf02be8
```

A file named `af65c9f5fcc16bf6328d300708fd58f22cb36c3173b8d00543c4ad089cf02be8` will be seen on running the `ls` command.

### Exit
For the Clients, `exit` command can be used. And if they are still running, `Ctrl+C` can be used to stop them gracefully. 



### GUI Test Cases

Similar test cases were conducted using the GUI as well. And some test cases involved some clients using the 'gui' argument and some clients using the 'cli'. 

One example test Case given below.

### Connection

Client 1

```bash
$ python3 client.py 5020 127.10.0.1 6009 gui

Listening on :37823
Enter your username: testuser
Logged in as, testuser
Connected to 0 peers.
No peers found. Creating a new blockchain.
Blockchain received. Last block: 0x0004cef686e0c1f213b4fda00ae391511f37905d03147694f458c16c8a95f921
Enter command: 
```

Client 2

```bash
$ python3 client.py 5021 127.10.0.1 6009 cli

Listening on :40529
Enter your username: testuser2 
Logged in as, testuser2
Connected to 1 peers.
Blockchain received. Last block: 0x0004cef686e0c1f213b4fda00ae391511f37905d03147694f458c16c8a95f921
Enter command:
```

Then using the GUI's 'Create NFT' option, this image was uploaded. 

![image1](https://github.com/csee4119-spring-2024/project-amethyst/assets/160454001/41a36fcb-cd9c-46eb-8042-9523f3f2e0dd)

Then using the 'Transfer NFT' option, the image was transferred to the CLI client, for which you need the image id and the recipient's id and you can insert them in the GUI client's command line interface. Then the photo/NFT was transferred to the CLI client. Below are some photos of the GUI interfaces before and after the transfer and a photo of the command line interface of the CLI client. 

<img width="1512" alt="Screenshot 2024-05-08 at 4 21 17 AM" src="https://github.com/csee4119-spring-2024/project-amethyst/assets/160454001/3b8fdf04-a170-4ec2-9038-e8225100312b">

<img width="1512" alt="Screenshot 2024-05-08 at 4 23 24 AM" src="https://github.com/csee4119-spring-2024/project-amethyst/assets/160454001/1837ddd9-f1a9-4d67-bb37-ba8faaee17a2">

The image's ownership was transferred to the CLI client, as a reason, the GUI client's owned folder is empty.

Below is the command line interface of the CLI client. 

<img width="841" alt="Screenshot 2024-05-08 at 5 14 23 AM" src="https://github.com/csee4119-spring-2024/project-amethyst/assets/160454001/de55c732-b347-48d5-9d24-7d67958b0257">

As you can see, the CLI client became the owner of the image in the last command. 



Besides, the test cases mentioned above, there were other test cases conducted:

1. Using multiple VMs
2. Using combination of CLI and GUI clients, some test case with all GUI or CLI clients, some test case with a mix
3. Fork Handling
4. Ownership (trying to transfer images owned by others or creating a same NFT causes errors as NFT owner is unique. If an NFT has already been created (uploaded) by a client, it cannot be uploaded by the other clients and we conducted multiple test cases for that to ensure). Example test case photos below.
<img width="725" alt="Screenshot 2024-05-08 at 5 24 40 AM" src="https://github.com/csee4119-spring-2024/project-amethyst/assets/160454001/6a1a4460-94bb-4278-ad6a-d22185620bd2">
<img width="788" alt="Screenshot 2024-05-08 at 5 24 47 AM" src="https://github.com/csee4119-spring-2024/project-amethyst/assets/160454001/2dd67661-50e9-46f7-9869-e03d752948ec">

You can see the second client got denied as the NFT was already owned.

 5. Transaction verification using merkle root
 6. Previous hash mismatching and block verification
 7. Mining difficulty adjustment
 8. Multiple Transactions

And the project successfuly passed all test cases. You can test case 7 and 8 by increasing the mining difficulty, right now it is 3. That's why transfers happen in a second, but you can increase that 4 or 5. It will make the mining take more time, and while mining for one block is still ongoing for high mining diffculty, you can add multiple blocks to mine at once, allowing multiple transactions. 

 






