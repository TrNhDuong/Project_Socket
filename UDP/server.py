import socket
import os
import threading

SERVER_HOST = "127.0.0.1"
SERVER_PORT = 5001
PORT = [5002, 5003, 5004, 5005]
BUFFER_SIZE = 1024  # 1KB
SEPARATOR = "<SEPARATOR>"
FILE_DIRECTORY = "fordown\\"  # Thư mục chứa các file

display = []
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

def read_contain_file():
    with open("listfile.txt", "r") as file_obj:
        lines = []
        for line in file_obj.readlines():
            if line.strip():
                lines.append(line.strip())
    
    return lines

def convert_to(file_list):
    mess = ""
    for file in file_list:
        mess += file
        mess += ':'
    return mess

def send_file_list(server_socket, address, file_list):
    # Lấy danh sách file
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


def receive_namefile_filesize():
    data, addr = server_socket.recvfrom(100)
    data = data.decode()
    filename, support = data.split(',')
    return filename


def send_chunk_udp(address, parts, start, end, i):
    child_socket = socket.socket(socket.AFINET, socket.DGRAM)
    child_socket.bind((SERVER_HOST, PORT[i]))
    i = start
    while i < end:
        header = f"{i}:".encode()
        child_socket.sendto(header + parts[i], address)
        child_socket.settimeout(0.05)
        try:
            ACK = child_socket.recvfrom(1)
            if ACK.decode() == "1":
                i += 1
        except (child_socket.timeout, TimeoutError):
            continue
    child_socket.close()

        


def send_file_udp(filename, address): 
    try:
        with open(FILE_DIRECTORY + filename, "rb") as file:
            file_data = file.read()
        
        # Chia dữ liệu thành các phần nhỏ
        total_size = len(file_data)
        parts = [file_data[i:i + BUFFER_SIZE] for i in range(0, total_size, BUFFER_SIZE)]
        total_parts = len(parts)
        
        unit = int(total_parts/4)
        length_of_chunk = [(0,unit), (unit, 2*unit), (2*unit, 3*unit), (3*unit, total_parts)]

        threads = []
        for i in range(4):
            start, end = length_of_chunk[i]
            thread = threading.Thread(target=send_chunk_udp, args=(address, parts, start, end, i))
            threads.append(thread)

        for thread in threads:
            thread.start()

        for thread in threads:
            thread.join()
    except FileNotFoundError:
        print(f"File not found: {filename}")


def handle_client(addr):
    send_file_list(server_socket, addr, file_list)
    send_file_list(server_socket, addr, display)
    while True:
        filename = receive_namefile_filesize()
        print(filename)
        send_file_udp(filename, addr)


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




