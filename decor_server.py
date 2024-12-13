import tkinter as tk
from tkinter import ttk
import random

def update_content(listbox, content_list, prefix):
    """Cập nhật nội dung vào Listbox"""
    new_item = f"{prefix} {random.randint(1, 100)}"
    content_list.append(new_item)
    listbox.insert(tk.END, new_item)
    if len(content_list) > 50:  # Giới hạn số mục trong danh sách
        content_list.pop(0)
        listbox.delete(0)

def create_window():
    # Tạo cửa sổ chính
    window = tk.Tk()
    window.title("Cửa sổ với hai khung trượt")
    window.geometry("500x300")

    # Tạo danh sách lưu nội dung
    current_connections = []
    connection_history = []

    # Tạo khung trượt cho "Các kết nối hiện tại"
    frame_current = ttk.Frame(window, relief="ridge", borderwidth=2)
    frame_current.place(x=50, y=50, width=300, height=100)

    scrollbar_current = ttk.Scrollbar(frame_current, orient="vertical")
    scrollbar_current.pack(side="right", fill="y")

    listbox_current = tk.Listbox(frame_current, yscrollcommand=scrollbar_current.set)
    listbox_current.pack(side="left", fill="both", expand=True)

    scrollbar_current.config(command=listbox_current.yview)

    # Thêm tiêu đề cho "Các kết nối hiện tại"
    label_current = tk.Label(window, text="Các kết nối hiện tại", bg="white", font=("Arial", 12, "bold"))
    label_current.place(x=260, y=30)

    # Tạo khung trượt cho "Lịch sử kết nối"
    frame_history = ttk.Frame(window, relief="ridge", borderwidth=2)
    frame_history.place(x=50, y=200, width=300, height=100)

    scrollbar_history = ttk.Scrollbar(frame_history, orient="vertical")
    scrollbar_history.pack(side="right", fill="y")

    listbox_history = tk.Listbox(frame_history, yscrollcommand=scrollbar_history.set)
    listbox_history.pack(side="left", fill="both", expand=True)

    scrollbar_history.config(command=listbox_history.yview)

    # Thêm tiêu đề cho "Lịch sử kết nối"
    label_history = tk.Label(window, text="Lịch sử kết nối", bg="white", font=("Arial", 12, "bold"))
    label_history.place(x=275, y=180)

    def update_lists():
        update_content(listbox_current, current_connections, "Kết nối")
        update_content(listbox_history, connection_history, "Lịch sử")
        window.after(2000, update_lists)  # Cập nhật mỗi 2 giây

    # Bắt đầu cập nhật nội dung
    update_lists()

    # Chạy vòng lặp chính
    window.mainloop()

# Gọi hàm để tạo cửa sổ
create_window()
