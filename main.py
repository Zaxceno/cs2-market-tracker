import time
import requests
import subprocess
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

console = Console()

# --- KONFIGURASI DAFTAR ITEM ---
# Kamu bisa menambahkan berapa pun item dan target harganya di sini!
WATCH_LIST = [
    {"name": "Dreams & Nightmares Case", "target": 12000},
    {"name": "Recoil Case", "target": 4000},
    {"name": "Fracture Case", "target": 3500},
]

# Jeda waktu antar pengecekan seluruh item (dalam detik). 
# Diubah jadi 60 detik atau lebih agar sangat aman dari limit Steam.
CHECK_INTERVAL = 60  

def get_cs2_price(item_name):
    url = f"https://steamcommunity.com/market/priceoverview/?appid=730&currency=39&market_hash_name={item_name}"
    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
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

def send_gnome_notification(title, message):
    subprocess.run(["notify-send", "-a", "CS2 Tracker", "-u", "normal", title, message])

def main():
    console.print(Panel.fit("[bold green]CS2 Multi-Item Live Market Tracker Started[/bold green]", border_style="green"))
    console.print(f"[dim]Memantau {len(WATCH_LIST)} item sekaligus. (Tekan Ctrl+C untuk berhenti)[/dim]\n")
    
    # Dictionary untuk mencatat status notifikasi masing-masing item agar tidak spam
    notified_status = {item["name"]: False for item in WATCH_LIST}

    try:
        while True:
            # Membuat tabel TUI untuk menampung banyak item sekaligus
            table = Table(show_header=True, header_style="bold cyan")
            table.add_column("No", style="dim", width=4)
            table.add_column("Item Market")
            table.add_column("Harga Saat Ini")
            table.add_column("Target Jual")
            table.add_column("Status")

            is_limited = False

            for idx, target_item in enumerate(WATCH_LIST, 1):
                item_name = target_item["name"]
                target_price = target_item["target"]

                raw_price = get_cs2_price(item_name)

                if raw_price == "LIMITED":
                    is_limited = True
                    table.add_row(str(idx), item_name, "[yellow]LIMITED (429)[/yellow]", f"Rp {target_price:,}", "[yellow]Menunggu Reset...[/yellow]")
                    continue
                elif raw_price:
                    clean_str = raw_price.replace("Rp", "").replace(".", "").strip()
                    current_price = int(clean_str)

                    if current_price >= target_price:
                        status_str = "[green]Target Tercapai![/green]"
                        if not notified_status[item_name]:
                            msg = f"{item_name} menembus Rp {current_price:,}!"
                            send_gnome_notification("📈 Target Harga CS2 Tercapai!", msg)
                            notified_status[item_name] = True
                    else:
                        status_str = "[yellow]Hold / Belum Capai[/yellow]"
                        notified_status[item_name] = False

                    table.add_row(str(idx), item_name, f"Rp {current_price:,}", f"Rp {target_price:,}", status_str)
                else:
                    table.add_row(str(idx), item_name, "[red]Gagal Fetch[/red]", f"Rp {target_price:,}", "[red]Error Koneksi[/red]")

                # Jeda kecil 2-3 detik ANTAR ITEM agar Steam tidak memblokir IP-mu
                time.sleep(2)

            # Bersihkan terminal dan cetak tabel rangkumannya secara rapi
            console.clear()
            console.print(Panel.fit("[bold green]CS2 Multi-Item Live Market Tracker[/bold green]", border_style="green"))
            console.print(table)

            if is_limited:
                console.print("\n[yellow][!] Terdeteksi limit API Steam. Mode jeda diperpanjang selama 60 detik...[/yellow]")
                time.sleep(60)
            else:
                console.print(f"\n[dim]Memperbarui ulang dalam {CHECK_INTERVAL} detik... (Tekan Ctrl+C untuk keluar)[/dim]")
                time.sleep(CHECK_INTERVAL)

    except KeyboardInterrupt:
        console.print("\n[bold red]Tracker dihentikan oleh pengguna.[/bold red]")

if __name__ == "__main__":
    main()