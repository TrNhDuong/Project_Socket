import socket
import os
import tqdm
import json
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

client_socket = socket.socket()
downloaded_file = []

def receive_file_list(client_socket):
    """Nhận danh sách file từ server."""
    # Nhận độ dài chuỗi JSON
    json_length = int(client_socket.recv(1024).decode())
    # Nhận chuỗi JSON
    json_data = client_socket.recv(json_length).decode()
    # Chuyển chuỗi JSON thành danh sách
    file_list = json.loads(json_data)
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

def add_padding_to_length(length_str, total_length=100):
    """Thêm padding vào chuỗi chiều dài cho đủ tổng chiều dài `total_length`."""
    # Nếu chiều dài của chuỗi nhỏ hơn total_length, thêm padding
    if len(length_str) < total_length:
        padding_length = total_length - len(length_str)
        length_str = length_str + '#' * padding_length  # Thêm byte padding
    return length_str


def receive_chunk(client_socket, filename, start_end):
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
    total_bytes = 0
    if end - start > 0:
        progress = tqdm.tqdm(range(end-start), f"Đang nhận 1 chunk {filename}", unit="B", unit_scale=True, unit_divisor=1024)
        with open(filename, "r+b") as file_obj:
            file_obj.seek(start)
            while total_bytes < (end - start):
                bytes_read = part_connect.recv(min(BUFFER_SIZE, end - start - total_bytes))
                if not bytes_read:
                    break
                file_obj.write(bytes_read)
                total_bytes += len(bytes_read)
                if len(bytes_read) < BUFFER_SIZE:
                    progress.update(end - start - progress.n)
                    break
                progress.update(len(bytes_read))
                time.sleep(0.05)
            progress.close()
    part_connect.close()


# Hàm tải file về Client 
def receive_file(client_socket, filename, filesize):
    print(f"Receiving {filename}...")
    unit = filesize // (BUFFER_SIZE * 4) * BUFFER_SIZE
    length_of_chunk = [
        (0, unit),
        (unit, 2 * unit),
        (2 * unit, 3 * unit),
        (3 * unit, filesize)
    ]
    threads = []
    with open(filename, "wb") as file_obj:
        file_obj.write(b'\x00' * filesize)

    for i in range(len(length_of_chunk)):
        thread = threading.Thread(target=receive_chunk, args=(client_socket, filename, length_of_chunk[i]))
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

# Hàm kết nối tới Server
def connect_to_server():
    client_socket.connect((SERVER_HOST, SERVER_PORT))
    print(f"[+] Đã kết nối đến Server {SERVER_PORT}")
    client_socket.send("0".encode())
    # Nhận danh sách các file có thể download
    file_list = receive_file_list(client_socket)
    print(f"Danh sách file có thể download từ Server: ")
    for file in file_list:
        print(file)
    
    # Nhập danh sách các file muốn download
    print("Nhập danh sách file muốn download vào file input.txt")
    wanted_files = []
    sended_file = []
    # Nhận và tải các file
    send_file = []
    downloaded_file = []
    while True:
        print("Đang quét file input")
        send_file = []
        wanted_files = get_files_to_download()
        for file in wanted_files:
            if file in sended_file:
                continue
            else:
                send_file.append(file)
                sended_file.append(file)
        # print(send_file)
        if send_file != []:
            send_download_file_list(client_socket, ','.join(send_file))
            for file in send_file:
                data = client_socket.recv(BUFFER_SIZE).decode()
                # print(data)
                if data != "sended" and data != "File not found":
                    filename, filesize = data.split(SEPARATOR)
                    # print(filename)
                    filesize = int(filesize)
                    receive_file(client_socket, filename, filesize)
                    print("Đã nhận file " + filename, filesize)
                    downloaded_file.append(file)
                elif data == "sended":
                    print("File " + filename + " đã tải")
                elif data == "File not found":
                    print("File khong ton tai")
        time.sleep(5)
                

# Bắt đầu kết nối và tải file
if __name__ == "__main__":
    request = input("Bạn có muốn kết nối với Server không(Y/N): ")
    if request == "Y":
        connect_to_server()
