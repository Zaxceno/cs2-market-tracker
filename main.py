import random
import time
import json
import requests
import threading
import tkinter as tk
from tkinter import ttk

# Menggunakan plyer untuk notifikasi desktop
try:
    from plyer import notification
except ImportError:
    notification = None

# --- KONFIGURASI MEMBACA FILE JSON ---
def load_watchlist():
    try:
        with open("items.json", "r", encoding="utf-8") as file:
            raw_data = json.load(file)
            watch_list = []
            
            if isinstance(raw_data, dict):
                for category_name, items in raw_data.items():
                    for item in items:
                        item_entry = item.copy()
                        item_entry["category"] = category_name.upper()
                        watch_list.append(item_entry)
            elif isinstance(raw_data, list):
                for item in raw_data:
                    item_entry = item.copy()
                    item_entry["category"] = "GENERAL"
                    watch_list.append(item_entry)
            return watch_list
    except Exception:
        return []

WATCH_LIST = load_watchlist()
CHECK_INTERVAL = 60  

def get_cs2_price(item_name):
    # Mengubah currency=39 (Qatari Riyal) menjadi currency=34 (Rupiah IDR)
    url = f"https://steamcommunity.com/market/priceoverview/?appid=730&currency=34&market_hash_name={item_name}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    }
    try:
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json()
            if data.get("success"):
                return data.get("lowest_price")
        elif response.status_code == 429:
            return "LIMITED"
    except Exception:
        return None
    return None

def send_desktop_notification(title, message):
    if notification:
        try:
            notification.notify(title=title, message=message, app_name="CS2 Tracker", timeout=5)
        except Exception:
            pass

class CS2TrackerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("CS2 Market Tracker - Desktop Edition")
        self.root.geometry("850x400")
        # Mengatur tema dasar aplikasi
        self.root.configure(bg="#1e1e1e")
        style = ttk.Style()
        style.theme_use("clam")
        
        # Desain Tabel (Treeview)
        style.configure("Treeview", background="#2d2d2d", foreground="white", fieldbackground="#2d2d2d", rowheight=25)
        style.configure("Treeview.Heading", background="#3c3c3c", foreground="white", font=('Arial', 10, 'bold'))
        style.map("Treeview", background=[("selected", "#005599")])

        # Label Judul
        self.title_label = tk.Label(root, text="📈 CS2 Live Market Tracker", font=("Arial", 16, "bold"), bg="#1e1e1e", fg="white")
        self.title_label.pack(pady=10)

        # Konfigurasi Kolom Tabel
        columns = ("no", "kategori", "item", "harga", "target", "status")
        self.tree = ttk.Treeview(root, columns=columns, show="headings", height=10)
        
        self.tree.heading("no", text="No")
        self.tree.heading("kategori", text="Kategori")
        self.tree.heading("item", text="Item Market")
        self.tree.heading("harga", text="Harga Saat Ini")
        self.tree.heading("target", text="Target Jual")
        self.tree.heading("status", text="Status")
        
        self.tree.column("no", width=40, anchor="center")
        self.tree.column("kategori", width=120, anchor="center")
        self.tree.column("item", width=220, anchor="w")
        self.tree.column("harga", width=120, anchor="center")
        self.tree.column("target", width=120, anchor="center")
        self.tree.column("status", width=180, anchor="center")
        
        self.tree.pack(fill=tk.BOTH, expand=True, padx=15, pady=5)

        # Label Status Real-time
        self.status_label = tk.Label(root, text="Menyiapkan sistem pemantauan...", font=("Arial", 10, "italic"), bg="#1e1e1e", fg="#00ff00")
        self.status_label.pack(pady=10)
        
        # Variabel sistem
        self.notified_status = {item["name"]: False for item in WATCH_LIST}
        self.running = True
        
        # Menjalankan mesin pencari harga di latar belakang agar GUI tidak lag
        self.thread = threading.Thread(target=self.fetch_prices)
        self.thread.daemon = True
        self.thread.start()

    def fetch_prices(self):
        while self.running:
            if not WATCH_LIST:
                self.update_status_text("Error: items.json kosong atau tidak valid!", "#ff4444")
                time.sleep(5)
                continue

            self.update_status_text("🔄 Sedang mengambil harga langsung dari server Steam...", "#ffb86c")
            
            # 1. Tampilkan semua item dengan status "Memuat..." terlebih dahulu
            current_data = []
            for idx, item in enumerate(WATCH_LIST, 1):
                cat = item.get("category", "GENERAL")
                current_data.append((idx, cat, item["name"], "Memuat...", f"Rp {item['target']:,}", "Menunggu server..."))
            
            self.root.after(0, self.update_treeview, list(current_data))

            is_limited = False

            # 2. Cek harga satu per satu dan langsung update baris tabelnya (Live Update)
            for idx, target_item in enumerate(WATCH_LIST, 1):
                item_name = target_item["name"]
                target_price = target_item["target"]
                category_name = target_item.get("category", "GENERAL")

                raw_price = get_cs2_price(item_name)
                
                if raw_price == "LIMITED":
                    is_limited = True
                    current_data[idx-1] = (idx, category_name, item_name, "LIMITED (429)", f"Rp {target_price:,}", "Menunggu Reset...")
                elif raw_price:
                    # Filter ajaib: membuang semua karakter selain angka (menghindari error ValueError)
                    clean_str = "".join(filter(str.isdigit, raw_price))
                    
                    # Cegah error jika hasil filter kosong
                    current_price = int(clean_str) if clean_str else 0

                    if current_price >= target_price:
                        status_str = "Tercapai!"
                        if not self.notified_status[item_name]:
                            msg = f"{item_name} menembus Rp {current_price:,}!"
                            send_desktop_notification("📈 Target Harga CS2 Tercapai!", msg)
                            self.notified_status[item_name] = True
                    else:
                        status_str = "Belum Capai"
                        self.notified_status[item_name] = False

                    current_data[idx-1] = (idx, category_name, item_name, f"Rp {current_price:,}", f"Rp {target_price:,}", status_str)
                else:
                    current_data[idx-1] = (idx, category_name, item_name, "Gagal Fetch", f"Rp {target_price:,}", "Error Koneksi")

                # Refresh tampilan tabel setiap kali 1 item selesai dicek
                self.root.after(0, self.update_treeview, list(current_data))

                if is_limited:
                    break # Hentikan pengecekan item lain jika sudah kena limit

                # Jeda antar item agar tidak diblokir Steam
                time.sleep(random.randint(3, 7))

            if is_limited:
                self.update_status_text("⚠️ Terdeteksi limit API Steam. Mode istirahat 60 detik aktif...", "#ff4444")
                time.sleep(60)
            else:
                self.update_status_text(f"✔️ Update selesai. Pengecekan berikutnya dalam {CHECK_INTERVAL} detik.", "#00ff00")
                time.sleep(CHECK_INTERVAL)

    def update_treeview(self, data):
        # Membersihkan tabel lama
        for row in self.tree.get_children():
            self.tree.delete(row)
        # Memasukkan baris data terbaru
        for row_data in data:
            self.tree.insert("", tk.END, values=row_data)

    def update_status_text(self, text, color):
        self.root.after(0, lambda: self.status_label.config(text=text, fg=color))

if __name__ == "__main__":
    # Inisialisasi jendela GUI utama
    root = tk.Tk()
    app = CS2TrackerGUI(root)
    # Menjaga jendela tetap terbuka
    root.mainloop()