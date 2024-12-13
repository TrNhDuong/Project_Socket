import socket
import time
import tqdm
import sys
import signal

SERVER_HOST = "127.0.0.1"
SERVER_PORT = 5001
BUFFER_SIZE = 1024  # 1KB
SEPARATOR = "<SEPARATOR>"
INPUT_FILE = "input.txt"
DOWNLOADED_FILE = "downloaded_files.txt"

client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

server_address = (SERVER_HOST, SERVER_PORT)

def receive_file_list(client_socket):
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
        print(full_data)
        file_list = full_data.split(',')
        return file_list
    else:
        # Nhận một gói tin đơn giản
        return message.split(',')

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

def send_filename_filesize(filename):
    mess = add_padding_to_length(filename + ',')
    client_socket.sendto(mess.encode(), server_address)  

def get_filename_filesize(file):
    filename, filesize = file.split(" - ")
    filesize, bytes = filesize.split(' ')
    return filename, int(filesize)

    
def receive_file(filename, size):
    total_received = 0
    with open(filename, "wb") as file_obj:
        file_obj.write(b'\x00' * size)
        while total_received < size:
            part, server = client_socket.recvfrom(1024 + 10)
            idx, content = part.split(b":", 1)
            file_obj.seek(int(idx)*BUFFER_SIZE)
            file_obj.write(content)
            total_received += len(content)
    if total_received == size:
        print(f"Đã nhận được đầy đủ {total_received} Bytes so với {size} Bytes")
    else:
        print(f"Nhận được {total_received} so với {size} Bytes")

def handle():
    client_socket.sendto(b"0", server_address)
    file_list = receive_file_list(client_socket)
    display = receive_file_list(client_socket)
    list_namefile = []
    list_sizefile = []
    print("Danh sách các file có thể download từ server:")
    for file in display:
        print(file)
        
    for file in file_list:
        name, size = get_filename_filesize(file)
        list_namefile.append(name)
        list_sizefile.append(size)

    downloaded_file =[]
    checked_file = []
    print("Nhập vào file Input")
    while True:
        downloaded_file = get_downloaded_file()
        input_file = get_files_to_download()
        if input_file != []:
            for file in input_file:
                if file not in checked_file:
                    if file in list_namefile and file not in downloaded_file:
                        print(file)
                        i = list_namefile.index(file)
                        send_filename_filesize(file)
                        size = list_sizefile[i]
                        receive_file(file, size)
                    elif file not in list_namefile:
                        print(f"[!] File {file} không tồn tại")
                    elif file in downloaded_file:
                        print(f"[!] File {file} đã tải xuống")
                    checked_file.append(file)
        time.sleep(5)
        print("Dang quet file input")

def handle_exit(signal_received, frame):
    print("\n[!] Ctrl + C được nhấn. Đang đóng kết nối...")
    if client_socket:
        try:
            client_socket.close()  # Đóng socket nếu đang kết nối
            print("[+] Kết nối đã được đóng.")
        except Exception as e:
            print(f"[!] Lỗi khi đóng socket: {e}")
    sys.exit(0)  # Thoát chương trình


# Gắn xử lý tín hiệu Ctrl + C
signal.signal(signal.SIGINT, handle_exit) 

if __name__ == "__main__":
    handle()

