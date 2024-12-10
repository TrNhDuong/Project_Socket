import socket
import os
import json
import threading

# Server configuration
SERVER_HOST = "0.0.0.0"
SERVER_PORT = 5001
BUFFER_SIZE = 1024  # 1KB
SEPARATOR = "<SEPARATOR>"
FILE_DIRECTORY = "fordown"  # Thư mục chứa các file

# Mảng chứa các địa chỉ đã kết nối
connected_addr = []
file_list = []

# Tạo socket server
server_socket = socket.socket()
server_socket.bind((SERVER_HOST, SERVER_PORT))
server_socket.listen(5)
print(f"[*] Đang lắng nghe tại {SERVER_HOST}:{SERVER_PORT}")

# Hàm lấy danh sách các file có thể tải được
def get_file_list():
    file_list = []
    if os.path.exists(FILE_DIRECTORY):
        for filename in os.listdir(FILE_DIRECTORY):
            file_path = os.path.join(FILE_DIRECTORY, filename)
            if os.path.isfile(file_path):
                filesize = os.path.getsize(file_path)
                # filesize_kb = filesize / 1024  # Chuyển byte thành KB
                file_list.append(f"{filename} - {filesize} byte")
    return file_list

# Hàm gửi danh sách các file muốn tải
def send_file_list(client_socket):
    """Gửi danh sách file dưới dạng JSON cho client."""
    # Lấy danh sách file
    file_list = get_file_list()
    # Chuyển mảng thành chuỗi JSON
    json_data = json.dumps(file_list)
    # Gửi độ dài của chuỗi JSON trước
    client_socket.send(f"{len(json_data)}".encode())
    # Gửi toàn bộ chuỗi JSON
    client_socket.sendall(json_data.encode())

# Hàm nhận tin nhắn từ Server
def receive_message(client_socket):
    # Nhận độ dài xâu trước
    message_length = int(client_socket.recv(1024).decode())
    # Nhận xâu có độ dài đã biết
    message = client_socket.recv(message_length).decode()
    return message

# Hàm gửi chunk tới Client
def send_chunk(client_socket, filename, start, end):
    with open(FILE_DIRECTORY + "\\" + filename, "rb") as file_obj:
        file_obj.seek(start)
        total_sent = 0
        while total_sent < (end - start):
            bytes_to_send = file_obj.read(BUFFER_SIZE)
            if not bytes_to_send:
                break
            client_socket.sendall(bytes_to_send)
            total_sent += len(bytes_to_send)
    file_obj.close()

# Hàm kiểm tra file tồn tại, đã tải hay không tồn tại
def send_file(client_socket, requested_file):
    file_path = os.path.join(FILE_DIRECTORY, requested_file)
    if os.path.exists(file_path) and os.path.isfile(file_path):
        filesize = os.path.getsize(file_path)
        client_socket.send(f"{requested_file}{SEPARATOR}{filesize}".encode())
        # print(f"[+] Đã gửi xong file: {requested_file}")
    else:
        client_socket.send("File not found".encode())
        print(f"[!] File {requested_file} không tồn tại trên server.")


def handle_client(client_socket, address):
    if address not in connected_addr:
        connected_addr.append(address)
    print(f"Nhận được kết nối từ {address}")
    
    # Gửi danh sách file cho client
    send_file_list(client_socket)
    message = receive_message(client_socket)
    if message == "close":
        print("[+]Client address ", address ," closed")


# Hàm tách tên file, byte bắt đầu, byte kết thúc
def split_name_start_end(message):
    name = ""
    i = 0
    while message[i] != '#':
        name += message[i]
        i += 1
    start = ""
    i += 2
    while message[i] != '#':
        start += message[i]
        i += 1
    end = ""
    i += 2
    while message[i] != '#':
        end += message[i]
        i += 1
    return name, int(start), int(end)

def connect_from_client(client_socket, address):
    signal = client_socket.recv(1).decode('utf-8')  # Chỉ nhận 1 byte

    if signal == "0":
        handle_client(client_socket, address)
    else:
        # Nhận xâu chứa tên file muốn tải, byte bắt đầu và kết thúc từ client
        mess = client_socket.recv(100).decode()
        filename, start, end = split_name_start_end(mess)
        send_chunk(client_socket, filename, start, end)
    client_socket.close()

# Vòng lặp chính của server
while True:
    client_socket, address = server_socket.accept()
    client = threading.Thread(target=connect_from_client, args=(client_socket, address))
    client.start()

# Đóng server socket (khi thoát)
server_socket.close()
