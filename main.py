import customtkinter
from tkinter import filedialog
import os
import subprocess
import datetime
import threading
import re
import time
import sys

# Налаштування стилю
customtkinter.set_appearance_mode("dark")
customtkinter.set_default_color_theme("dark-blue")

def resource_path(relative_path):
    """ Отримує шлях до ресурсу, працює для dev і для Nuitka/PyInstaller """
    base_path = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)


app = customtkinter.CTk()
app.geometry("380x180")
app.resizable(False, False)
app.title(" MgTw2.4A Legacy")

icon_path = resource_path("image.ico")
if os.path.exists(icon_path):
    app.iconbitmap(icon_path)

# Отримуємо розміри екрана
sw = app.winfo_screenwidth()
sh = app.winfo_screenheight()

# X — залишаємо чітко по центру
x = (sw // 2) - (380 // 2)

# Y — зміщуємо в "зону комфортного погляду" (трохи вище центру)
y = int((sh / 2.5) - (180 / 2))

app.geometry(f"380x180+{x}+{y}")

# --- Системні функції ---

def get_duration(file_path, ffmpeg_path):
    if not os.path.exists(file_path): return 0
    CREATE_NO_WINDOW = 0x08000000
    cmd = [ffmpeg_path, "-i", file_path]
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,creationflags=CREATE_NO_WINDOW)
    match = re.search(r"Duration:\s(\d+):(\d+):(\d+\.\d+)", result.stderr)
    if match:
        h, m, s = map(float, match.groups())
        return h * 3600 + m * 60 + s
    return 0


def run_ffmpeg_with_progress(cmd, duration, start_val, end_val):
    CREATE_NO_WINDOW = 0x08000000
    process = subprocess.Popen(
        cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
        universal_newlines=True, encoding='utf-8', creationflags=CREATE_NO_WINDOW
    )

    for line in process.stdout:
        match = re.search(r"time=(\d+):(\d+):(\d+\.\d+)", line)
        if match and duration > 0:
            h, m, s = map(float, match.groups())
            current_time = h * 3600 + m * 60 + s
            step_p = min(current_time / duration, 1.0)
            total_p = start_val + (step_p * (end_val - start_val))
            progress_bar.set(total_p)
            app.update_idletasks()
    process.wait()


# --- Логіка інтерфейсу ---

def button_function():
    vF = filedialog.askopenfilename(filetypes=[("Video", ".mkv .mp4")])
    if vF:
        with open(r'DATA\Video.txt', 'wt', encoding='utf-8') as f: f.write(vF)
        print(f"--- Файл Video.txt успішно оновлено. Записано шлях: {vF} ---")


def open_file_audio():
    aF = filedialog.askopenfilename(filetypes=[("Audio", ".flac .ogg")])
    if aF:
        with open(r'DATA\Audio.txt', 'wt', encoding='utf-8') as f: f.write(aF)
        print(f"--- Файл Audio.txt успішно оновлено. Записано шлях: {aF} ---")



def start_thread():
    threading.Thread(target=obednannya, daemon=True).start()


def obednannya():
    ffmpeg_path = r'DATA\ffmpeg\ffmpeg.exe'

    try:
        with open(r'DATA\Video.txt', 'r', encoding='utf-8') as f:
            B1 = f.readline().strip()
        with open(r'DATA\Audio.txt', 'r', encoding='utf-8') as f:
            B2 = f.readline().strip()
    except:
        return
    if not os.path.exists(B1) or not os.path.exists(B2): return

    rGO.configure(state="disabled", text="Працюємо...")
    progress_bar.configure(progress_color="red")
    progress_bar.set(0)
    progress_bar.place(relx=0.5, rely=0.82, anchor=customtkinter.CENTER)

    os.makedirs(r'outFile', exist_ok=True)
    os.makedirs(r'DATA\cache', exist_ok=True)

    duration = get_duration(B1, ffmpeg_path)

    # ТУТ ДОДАНО СЕКУНДИ: %H-%M-%S
    now = datetime.datetime.now()
    timestamp = now.strftime("%Y-%m-%d_%H-%M-%S")

    B3 = fr'outFile/output_{timestamp}.mp4'
    B4 = fr'DATA\cache/temp_{timestamp}.m4a'  # Тимчасовий файл робимо унікальним

    # КРОК 1: Конвертація звуку (90% прогресу)
    cmd1 = [ffmpeg_path, "-y", "-i", B2, "-acodec", "aac", "-ab", "192k", "-ac", "2", B4]
    run_ffmpeg_with_progress(cmd1, duration, 0.0, 0.9)

    # КРОК 2: Зклеювання (10% прогресу)
    cmd2 = [
        ffmpeg_path, "-y", "-i", B1, "-i", B4,
        "-map", "0:v", "-map", "1:a", "-c:v", "copy", "-c:a", "copy",
        "-map_metadata", "-1", B3
    ]

    CREATE_NO_WINDOW = 0x08000000
    subprocess.run(cmd2, creationflags=CREATE_NO_WINDOW)

    path = r"outFile"
    os.startfile(path)

    # Плавна дотяжка до кінця
    curr = 0.9
    while curr < 1.0:
        curr += 0.02
        progress_bar.set(curr)
        app.update_idletasks()
        time.sleep(0.03)

    print(f"Збережено: {B3}")
    if os.path.exists(B4): os.remove(B4)
    rGO.configure(state="normal", text="Ну мо погнали!!")

    progress_bar.configure(progress_color="green")
    progress_bar.set(1.0)
# --- UI ---

oMKV = customtkinter.CTkButton(master=app, text="Відкрий >> MKV / MP4", command=button_function)
oMKV.place(relx=0.25, rely=0.35, anchor=customtkinter.CENTER)

oFLAC = customtkinter.CTkButton(master=app, text="Відкрий >> FLAC / OGG", command=open_file_audio)
oFLAC.place(relx=0.25, rely=0.65, anchor=customtkinter.CENTER)

rGO = customtkinter.CTkButton(master=app, text="Ну мо погнали!!", command=start_thread)
rGO.place(relx=0.75, rely=0.50, anchor=customtkinter.CENTER)

progress_bar = customtkinter.CTkProgressBar(master=app, width=300, progress_color="red")
progress_bar.set(0)

line = "+-=" * 20
customtkinter.CTkLabel(app, text_color="yellow", text=line).place(relx=0.5, rely=0.05, anchor="center")
customtkinter.CTkLabel(app, text_color="yellow", text=line).place(relx=0.5, rely=0.95, anchor="center")

app.mainloop()