[![Review Assignment Due Date](https://classroom.github.com/assets/deadline-readme-button-24ddc0f5d75046c5622901739e7c5dd533143b0c8e959d652212380cedb1ea36.svg)](https://classroom.github.com/a/-Lgd7v9y)
# CSEE 4119 Spring 2024, Class Project
## Team name: Solo
## Team members (name, GitHub username): Anik Dey (ad4215)
## 

# How to use

## Tracker
`tracker.py` needs to be running as a prequisite of the blockchain. Running `python3 tracker.py <port>` will start the tracker on the specified port.

```
$ python3 tracker.py 7000

Tracker is listening on 0.0.0.0:7000
```

Afterwards, the clients can be started.

## Client
`client.py` will be running to interact with the blockchain. `python3 client.py -h` will show the available options.

```
python3 client.py -h

usage: client.py [-h] port tracker_host tracker_port {cli,gui,both,none}

positional arguments:
  port                 Port to bind the client to
  tracker_host         Host of the tracker
  tracker_port         Port of the tracker
  {cli,gui}  Type of client (cli/gui)

options:
  -h, --help           show this help message and exit
```

`cli` option will run the client with an interactive CLI to interact with the blockchain. `gui` will run the client with the GUI. `both` will run the GUI and also keep the interactive CLI available. `none` is used when the client is only needed to mine blocks.

```
$ python3 client.py 7001 127.0.0.1 7000 cli (if the clients and tracker are run from the same device or the same cloud VM, the IP must be ## 127.0.0.1 as this is the loopback address) (Please do not try to use the exact same port in a very short period of time as it takes time to free the ports, use a different number)

Listening on :34237
Enter your username: testuser (give a name)
Logged in as, testuser
Connected to 0 peers.
No peers found. Creating a new blockchain.
Blockchain created. First block: 0x000439ef4a3a9bdcc34140d7087c338aa8cb07759c0616bb11c434b007ebd128
Enter command: 
```

The port number used as an argument is for the tracker only. Another listening port will be opened for the blockchain peers. That port number will be shown when the client is started.

## CLI Commands
- `create`: Creates a new NFT from a given file path. File path must be valid (checks are not implemented). When using CLI, the image must be saved in the same directory as the client file and the image path would look like <image_file_name>.<extension, i.e, jpeg, png>. Please make sure the path is valid.
- `transfer`: Transfers an NFT to another user. The command takes the image id (the hash of the image) and the recipient. The NFT must be owned by the user. If not, CLi will print an error message and return. However, recipient does not need to be a valid user. Any 32 byte hex string can be used as a recipient. The ids should not include 0x at the beginning.
- `me`: Shows the user's NFTs.
- `images`: Shows the list of all NFTs and their owners.
- `get`: Downloads the image of the given image id and saves it to the current directory. Image id must be valid (checks are not implemented).
- `chain`: Prints the blockchain in a somewhat human readable format.
- `exit`: Exits the CLI (However, some listening threads may still be running so the client might continue to run. Pressing `Ctrl+C` will stop the client).

## GUI Version

For GUI, there is no command line, except when transferring NFTs, the 'image id' and the 'recipient id' need to be input through the CLI. Unlike the CLI, the GUI enables to create or upload images from anywhere from the computer, the file does not need to be on the same directory, but for compuational resources, please upload low space photos to not make the process slow. you can uplaod it by pressing on the button "Create NFT", you can also exit the network by clicking "Exit". But when you click on the "Transfer NFT", please go check the command line interface where you started the GUI client from, you will see it's asking for the image id and the recipient id, give them the id hash values, it will transfer the NFT to the addressing recipient. 

## Testing on Google Cloud with Multiple VMs

When all the files are on one VM, it is the same thing as running them from your own computer. But when the IPs become different, you will have to do some additional rules. Suppose, the client is in VM1 and tracker is in VM2. Their port numbers are consecutively 2244 and 9991. Then, you will have to setup firewall rules for each VM. First of all, the VMs must allow HTTP and HTTPs connections which you can edit in the VM Edit settings. Then do the following:

### Firewall Rule for the Tracker:
Click CREATE FIREWALL RULE.
Enter the following settings:
Name: allow-tracker
Network: Choose the default or the specific VPC network your VMs are in.
Priority: 100 (or another number to determine precedence; lower numbers mean higher priority).
Direction of traffic: Ingress (incoming).
Action on match: Allow.
Targets: You can use apply-to-all.
Source filters: IP ranges ( put 0.0.0.0/0).
Protocols and ports: Specified protocols and ports. Enter tcp:9991.

### Create Firewall Rules for Each Client:
Repeat the process for each client. Here’s an example for one of the clients:

Click CREATE FIREWALL RULE.
Enter settings:
Name: allow-client-one
Network: Default or your specific network.
Priority: 100.
Direction of traffic: Ingress.
Action on match: Allow.
Targets: You can use apply-to-all.
Source filters: IP ranges (0.0.0.0/0).
Protocols and ports: tcp:2244 for the first client.

Then run the files from the respective VMs. Note: GUI cannot be run on VM as VM does not facilitate that, using a 'gui' argument can only be done from local terminal

