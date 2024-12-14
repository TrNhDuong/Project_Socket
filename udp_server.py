import socket
import os
import struct

SERVER_HOST = "127.0.0.1"
SERVER_PORT = 5001
BUFFER_SIZE = 1024  # 1KB
FILE_DIRECTORY = "fordown\\"  # Thư mục chứa các file

server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server_socket.bind((SERVER_HOST, SERVER_PORT))

display = []
file_list = []

def get_file_list():
    file_list = []
    if os.path.exists(FILE_DIRECTORY):
        for filename in os.listdir(FILE_DIRECTORY):
            file_path = os.path.join(FILE_DIRECTORY, filename)
            if os.path.isfile(file_path):
                filesize = os.path.getsize(file_path)
                file_list.append(f"{filename} - {filesize} Bytes")
    return file_list

def read_contain_file():
    with open("listfile.txt", "r") as file_obj:
        lines = []
        for line in file_obj.readlines():
            if line.strip():
                lines.append(line.strip())
    
    return lines


def send_file_list(server_socket, address, file_list):
    # Chuyển mảng thành chuỗi, các file cách nhau bởi dấu ','
    file_list_data = ','.join(file_list)
    # Kiểm tra kích thước dữ liệu
    max_packet_size = 1024  # Giới hạn kích thước gói tin
    data_length = len(file_list_data)
    
    if data_length <= max_packet_size:
        # Gửi một gói tin nếu dữ liệu nhỏ
        server_socket.sendto(file_list_data.encode(), address)
    else:
        # Chia dữ liệu thành nhiều phần
        parts = [file_list_data[i:i+max_packet_size] for i in range(0, data_length, max_packet_size)]
        total_parts = len(parts)

        # Gửi số lượng gói tin trước
        server_socket.sendto(f"PARTS:{total_parts}".encode(), address)

        # Gửi từng phần với số thứ tự
        for idx, part in enumerate(parts):
            packet = f"{idx}:{part}".encode()  # Thêm chỉ số gói tin
            server_socket.sendto(packet, address)

def receive_namefile():
    lenName, addr = server_socket.recvfrom(4)
    lenName = struct.unpack('!I', lenName)[0]
    filename, saddr = server_socket.recvfrom(lenName)
    filename = filename.decode()
    return filename

def send_file_udp(filename, address): 
    try:
        with open(FILE_DIRECTORY + filename, "rb") as file_obj:
            data = file_obj.read()
            total = len(data)
            total_sent = 0
            i = 0
            while total_sent < total:
                bytes_sent = data[total_sent:total_sent + BUFFER_SIZE]
                header = struct.pack('!I', i)
                server_socket.sendto(header + bytes_sent, address)
                server_socket.settimeout(5)
                try:
                    ACK, add = server_socket.recvfrom(1)
                    if ACK.decode() == "1":
                        total_sent += len(bytes_sent)
                        i += 1
                except (server_socket.timeout, TimeoutError):
                    continue
    except FileNotFoundError:
        print(f"File not found: {filename}")


def handle_client(addr):
    send_file_list(server_socket, addr, file_list)
    send_file_list(server_socket, addr, display)
    while True:
        server_socket.settimeout(5)
        try:
            filename = receive_namefile()
            send_file_udp(filename, addr)
        except TimeoutError:
            continue
        

if __name__ == "__main__":
    display = read_contain_file()
    file_list = get_file_list()
    print("Các file có thể download trên Server: " )
    for file in display:
        print(file)
    data, addr = server_socket.recvfrom(1)
    if data.decode() == "0":
        print(f"[+] Message form {addr}")
        handle_client(addr)

server_socket.close()





