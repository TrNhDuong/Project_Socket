import socket
import tqdm
import time
import threading
import signal
import sys


# Client configuration
SERVER_HOST = "127.0.0.1"
SERVER_PORT = 5001
BUFFER_SIZE = 1024
SEPARATOR = "<SEPARATOR>"
INPUT_FILE = "input.txt"  # File chứa danh sách các file cần tải
DOWNLOADED_FILE = "downloaded_files.txt"

client_socket = socket.socket()
display_list = []

def receive_file_list(client_socket):
    # Nhận độ dài danh sách file
    length_data = client_socket.recv(1024).decode()
    file_list_length = int(length_data)
    # Nhận danh sách file dạng chuỗi
    received_data = client_socket.recv(file_list_length).decode()
    # Phân tách chuỗi thành danh sách file (giả định phân tách bằng dấu phẩy)
    file_list = received_data.split(',') if received_data else []
    return file_list

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
    
def add_padding_to_length(length_str, total_length=100):
    """Thêm padding vào chuỗi chiều dài cho đủ tổng chiều dài `total_length`."""
    # Nếu chiều dài của chuỗi nhỏ hơn total_length, thêm padding
    if len(length_str) < total_length:
        padding_length = total_length - len(length_str)
        length_str = length_str + '#' * padding_length  # Thêm byte padding
    return length_str


def receive_chunk(client_socket, filename, start_end, i):
    start, end = start_end
    part_connect = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    part_connect.connect((SERVER_HOST, SERVER_PORT))
    # Gửi signal kiểm tra là tải chunk hay là kết nối mới
    part_connect.send("1".encode('utf-8'))

    # Gửi tên file muốn download, vị trí bắt đầu tải và dừng
    send_str = filename + "##" + f"{start}##{end}"
    # print(send_str)
    x = add_padding_to_length(send_str)
    part_connect.sendall(f"{x}".encode())

    # Nhận data từ server và tải dữ liệu về
    total_bytes = end - start
    total_received = 0
    if total_bytes > 0:
        progress = tqdm.tqdm(range(total_bytes), f"Tiến trình download chunk {i} {filename}", unit="B", unit_scale=True, unit_divisor=1024)
        with open(filename, "r+b") as file_obj:
            file_obj.seek(start)
            while total_received < total_bytes:
                bytes_read = part_connect.recv(min(BUFFER_SIZE, total_bytes - total_received))
                if not bytes_read:
                    break
                file_obj.write(bytes_read)
                total_received += len(bytes_read)
                progress.update(len(bytes_read))
                time.sleep(0.05)
            progress.close()
    part_connect.close()


# Hàm tải file về Client 
def receive_file(client_socket, filename, filesize):
    print(f"Receiving {filename}...")
    unit = int(filesize/4)
    length_of_chunk = [
        (0, unit),
        (unit, 2 * unit),
        (2 * unit, 3 * unit),
        (3 * unit, filesize)
    ]
    threads = []
    with open(filename, "wb") as file_obj:
        file_obj.write(b'\x00' * filesize)

    with open(DOWNLOADED_FILE, 'a') as file_obj:
        file_obj. write(filename + "\n")
    
    for i in range(len(length_of_chunk)):
        thread = threading.Thread(target=receive_chunk, args=(client_socket, filename, length_of_chunk[i], i))
        threads.append(thread)
    
    for thread in threads:
        thread.start()
    
    for thread in threads:
        thread.join()
    
# Hàm gửi danh sách file muốn download tới Server
def send_download_file_list(client_socket, wanted_files):
    # Gửi độ dài của danh sách file
    client_socket.send(f"{len(wanted_files)}".encode())
    # Gửi danh sách file
    client_socket.sendall(wanted_files.encode())


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

# Hàm kết nối tới Server
def connect_to_server():
    client_socket.connect((SERVER_HOST, SERVER_PORT))
    print(f"[+] Đã kết nối đến Server {SERVER_PORT}")
    client_socket.send("0".encode())
    # Nhận danh sách các file có thể download
    file_list = receive_file_list(client_socket)
    display_list = receive_file_list(client_socket)
    filename_list = []
    filesize_list = []
    print(f"Danh sách file có thể download từ Server: ")
    for file in display_list:
        print(file)

    for file in file_list:
        name, size = get_filename_filesize(file)
        filename_list.append(name)
        filesize_list.append(size)

    
    # Nhập danh sách các file muốn download
    print("Nhập danh sách file muốn download vào file input.txt")
    input_file = []
    # Nhận và tải các file
    checked_file = []
    downloaded_file = []
    while True:
        print("Đang quét file input")
        input_file = get_files_to_download()
        downloaded_file = get_downloaded_file()
        for file in input_file:
            if file not in checked_file:
                if file in filename_list and file not in downloaded_file:
                    i = filename_list.index(file)
                    size = filesize_list[i]
                    receive_file(client_socket, file, size)
                elif file not in filename_list:
                    print(f"[!] File {file} không tồn tại")
                elif file in downloaded_file:
                    print(f"[!] File {file} đã được tải")
                checked_file.append(file)
        time.sleep(5)

def handle_exit(signal_received, frame):
    """Hàm xử lý khi người dùng nhấn Ctrl + C."""
    print("\n[!] Ctrl + C được nhấn. Đang đóng kết nối...")
    client_socket.send(f"{len("close")}".encode())
    client_socket.send("close".encode())
    if client_socket:
        try:
            client_socket.close()  # Đóng socket nếu đang kết nối
            print("[+] Kết nối đã được đóng.")
        except Exception as e:
            print(f"[!] Lỗi khi đóng socket: {e}")
    sys.exit(0)  # Thoát chương trình


# Gắn xử lý tín hiệu Ctrl + C
signal.signal(signal.SIGINT, handle_exit)               

# Bắt đầu kết nối và tải file
if __name__ == "__main__":
    connect_to_server()