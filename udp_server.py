import socket
import os
import json

SERVER_HOST = "127.0.0.1"
SERVER_PORT = 5001
BUFFER_SIZE = 1024  # 1KB
SEPARATOR = "<SEPARATOR>"
FILE_DIRECTORY = "fordown\\"  # Thư mục chứa các file

file_list = []
server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server_socket.bind((SERVER_HOST, SERVER_PORT))

def get_file_list():
    file_list = []
    if os.path.exists(FILE_DIRECTORY):
        for filename in os.listdir(FILE_DIRECTORY):
            file_path = os.path.join(FILE_DIRECTORY, filename)
            if os.path.isfile(file_path):
                filesize = os.path.getsize(file_path)
                # filesize_kb = filesize / 1024  # Chuyển byte thành KB
                file_list.append(f"{filename} - {filesize} Bytes")
    return file_list

def convert_to(file_list):
    mess = ""
    for file in file_list:
        mess += file
        mess += ':'
    return mess

def send_file_list(server_socket, address):
    """Gửi danh sách file dưới dạng JSON qua UDP."""
    # Lấy danh sách file
    file_list = get_file_list()
    # Chuyển mảng thành chuỗi JSON
    json_data = json.dumps(file_list)
    # Kiểm tra kích thước dữ liệu
    max_packet_size = 1024  # Giới hạn kích thước gói tin
    data_length = len(json_data)
    
    if data_length <= max_packet_size:
        # Gửi một gói tin nếu dữ liệu nhỏ
        server_socket.sendto(json_data.encode(), address)
    else:
        # Chia dữ liệu thành nhiều phần
        parts = [json_data[i:i+max_packet_size] for i in range(0, data_length, max_packet_size)]
        total_parts = len(parts)

        # Gửi số lượng gói tin trước
        server_socket.sendto(f"PARTS:{total_parts}".encode(), address)

        # Gửi từng phần với số thứ tự
        for idx, part in enumerate(parts):
            packet = f"{idx}:{part}".encode()  # Thêm chỉ số gói tin
            server_socket.sendto(packet, address)

def add_padding_to_length(length_str, total_length=20):
    """Thêm padding vào chuỗi chiều dài cho đủ tổng chiều dài `total_length`."""
    # Nếu chiều dài của chuỗi nhỏ hơn total_length, thêm padding
    if len(length_str) < total_length:
        padding_length = total_length - len(length_str)
        length_str = length_str + '#' * padding_length  # Thêm byte padding
    return length_str

def receive_namefile_filesize():
    data, addr = server_socket.recvfrom(100)
    data = data.decode()
    filename = ""
    i = 0
    while data[i] != '#':
        filename += data[i]
        i += 1
    i += 2
    filesize = ""
    while data[i] != '#':
        filesize += data[i]
        i += 1

    return filename, int(filesize)

def send_file(filename, filesize, addr):
    i = 0
    with open(FILE_DIRECTORY + "\\" + filename, "rb") as file_obj:
        total_sent = 0
        size = filesize
        while total_sent < size:
            byte_read = file_obj.read(BUFFER_SIZE)
            header = add_padding_to_length(str(i))
            server_socket.sendto(header.encode(), addr)
            server_socket.sendto(byte_read, addr)
            total_sent += BUFFER_SIZE
            i += 1
    
def send_file_udp(filename, filesize, address):  
    try:
        with open(FILE_DIRECTORY + filename, "rb") as file:
            file_data = file.read()
        
        # Chia dữ liệu thành các phần nhỏ
        total_size = len(file_data)
        parts = [file_data[i:i + BUFFER_SIZE] for i in range(0, total_size, BUFFER_SIZE)]
        total_parts = len(parts)
        
        # Gửi thông báo số lượng gói tin
        server_socket.sendto(f"FILE:{total_parts}".encode(), address)

        # Gửi từng phần dữ liệu với số thứ tự
        for idx, part in enumerate(parts):
            header = f"{idx}:".encode()  # Header chứa số thứ tự
            server_socket.sendto(header + part, address)
    except FileNotFoundError:
        print(f"File not found: {filename}")

file_list = get_file_list()

def handle_client(addr):
    send_file_list(server_socket, addr)
    while True:
        filename, filesize = receive_namefile_filesize()
        print(filename)
        send_file_udp(filename, filesize, addr)
        # data, addr = server_socket.recvfrom(1024)
        # print(f"Received '{data.decode()}' from {addr}")
        # server_socket.sendto(b"Hello, Client!", addr)

if __name__ == "__main__":
    data, addr = server_socket.recvfrom(1)
    if data.decode() == "0":
        print(f"[+] Connection form {addr}")
        handle_client(addr)






