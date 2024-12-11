import socket
import time
import json

SERVER_HOST = "127.0.0.1"
SERVER_PORT = 5001
BUFFER_SIZE = 1024  # 1KB
SEPARATOR = "<SEPARATOR>"
INPUT_FILE = "input.txt"
DOWNLOADED_FILE = "downloaded_files.txt"

client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

server_address = (SERVER_HOST, SERVER_PORT)

def receive_file_list(client_socket):
    """Nhận danh sách file từ server qua UDP."""
    # Nhận thông báo về số lượng gói tin
    data, server = client_socket.recvfrom(1024)
    message = data.decode()

    if message.startswith("PARTS:"):
        total_parts = int(message.split(":")[1])
        received_data = [""] * total_parts

        for _ in range(total_parts):
            part, server = client_socket.recvfrom(1024)
            idx, content = part.decode().split(":", 1)
            received_data[int(idx)] = content

        # Ghép dữ liệu
        full_data = "".join(received_data)
        file_list = json.loads(full_data)
        return file_list
    else:
        # Nhận một gói tin đơn giản
        return json.loads(message)

def get_files_to_download():
    try:
        with open(INPUT_FILE, "r") as file:
            files = []
            for line in file.readlines():
                if line.strip():
                    files.append(line.strip()) 
        return files
    except FileNotFoundError:
        print(f"[!] Không tìm thấy file {INPUT_FILE}. Đảm bảo file tồn tại.")
        return []

def get_downloaded_file():
    try:
        with open(DOWNLOADED_FILE, "r") as file:
            files = []
            for line in file.readlines():
                if line.strip():
                    files.append(line.strip())
            return files
    except FileNotFoundError:
        print(f"[!] Khong tim file {DOWNLOADED_FILE}")
        return []

def add_padding_to_length(length_str, total_length=50):
    # Nếu chiều dài của chuỗi nhỏ hơn total_length, thêm padding
    if len(length_str) < total_length:
        padding_length = total_length - len(length_str)
        length_str = length_str + '#' * padding_length  # Thêm byte padding
    return length_str

def send_filename_filesize(filename, filesize):
    mess = add_padding_to_length(filename + '##' + str(filesize))
    client_socket.sendto(mess.encode(), server_address)  

def get_filename_filesize(file):
    filename = ""
    i = 0
    while file[i] != ' ':
        filename += file[i]
        i += 1
    
    i += 3
    filesize = ""
    while file[i] != ' ':
        filesize += file[i]
        i += 1
    return filename, int(filesize)

def receive_file(filename, filesize):
    print(filesize)
    with open(filename, "wb") as file_obj:
        file_obj.write(b'\x00' * filesize)
        check_sum = 0
        while check_sum < filesize:
            mess1, addr = client_socket.recvfrom(30)
            mess1 = mess1.decode()
            byte_sent, addr = client_socket.recvfrom(1024)
            offset = ""
            i = 0
            while mess1[i] != '#':
                offset += mess1[i]
                i += 1

            offset = int(offset)
            print(offset)
            file_obj.seek(offset*BUFFER_SIZE)
            file_obj.write(byte_sent)
            check_sum += BUFFER_SIZE

def receive_file_udp(filename, size):
    data, server = client_socket.recvfrom(1024)
    message = data.decode()

    if message.startswith("FILE:"):
        total_parts = int(message.split(":")[1])
        received_data = [None] * total_parts

        for _ in range(total_parts):
            part, server = client_socket.recvfrom(1024 + 10)  # Dự phòng kích thước header
            idx, content = part.split(b":", 1)
            received_data[int(idx)] = content

        # Kết hợp dữ liệu và lưu thành file
        with open(filename, "wb") as file:
            for part in received_data:
                file.write(part)
        print(f"File saved to {filename}")

def handle():
    client_socket.sendto(b"0", server_address)
    file_list = receive_file_list(client_socket)
    list_namefile = []
    list_sizefile = []
    print("Cac file co the download tu server:")
    for file in file_list:
        print(file)
        name, size = get_filename_filesize(file)
        list_namefile.append(name)
        list_sizefile.append(size)

    downloaded_file =[]
    checked_file = []
    print("Nhap vao file input")
    while True:
        downloaded_file = get_downloaded_file()
        input_file = get_files_to_download()
        print(input_file)
        if input_file != []:
            for file in input_file:
                if file not in checked_file:
                    if file in list_namefile and file not in downloaded_file:
                        i = list_namefile.index(file)
                        send_filename_filesize(file, list_sizefile[i])
                        size = list_sizefile[i]
                        receive_file_udp(file, size)
                    elif file not in list_namefile:
                        print(f"[!] File {file} không tồn tại")
                    elif file in downloaded_file:
                        print(f"[!] File {file} đã tải xuống")
                    checked_file.append(file)
        time.sleep(5)
        print("Dang quet file input")



if __name__ == "__main__":
    handle()

