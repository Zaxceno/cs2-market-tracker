import random
import time
import json
import requests
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

# Notifikasi desktop lintas platform (Windows & Linux)
try:
    from plyer import notification
except ImportError:
    notification = None

console = Console()

# --- KONFIGURASI MEMBACA FILE JSON (Roadmap 1 & 2 Support) ---
try:
    with open("items.json", "r", encoding="utf-8") as file:
        raw_data = json.load(file)
        
        WATCH_LIST = []
        # Jika JSON menggunakan struktur kategori {"cases": [...], "stickers": [...]}
        if isinstance(raw_data, dict):
            for category_name, items in raw_data.items():
                for item in items:
                    item_entry = item.copy()
                    item_entry["category"] = category_name.upper()
                    WATCH_LIST.append(item_entry)
        # Jika JSON menggunakan struktur list biasa [{"name": "..."}, ...]
        elif isinstance(raw_data, list):
            for item in raw_data:
                item_entry = item.copy()
                item_entry["category"] = "GENERAL"
                WATCH_LIST.append(item_entry)

except FileNotFoundError:
    console.print("[red][!] File items.json tidak ditemukan! Gagal memulai tracker.[/red]")
    exit()
except json.JSONDecodeError:
    console.print("[red][!] Format items.json rusak atau tidak valid![/red]")
    exit()

CHECK_INTERVAL = 60  

def get_cs2_price(item_name):
    url = f"https://steamcommunity.com/market/priceoverview/?appid=730&currency=39&market_hash_name={item_name}"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
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
            notification.notify(
                title=title,
                message=message,
                app_name="CS2 Tracker",
                timeout=5
            )
        except Exception:
            pass

def main():
    console.print(Panel.fit("[bold green]CS2 Multi-Item Live Market Tracker Started[/bold green]", border_style="green"))
    console.print(f"[dim]Memantau {len(WATCH_LIST)} item sekaligus. (Tekan Ctrl+C untuk berhenti)[/dim]\n")
    
    notified_status = {item["name"]: False for item in WATCH_LIST}

    try:
        while True:
            table = Table(show_header=True, header_style="bold cyan")
            table.add_column("No", style="dim", width=4)
            table.add_column("Kategori", style="bold magenta")
            table.add_column("Item Market")
            table.add_column("Harga Saat Ini")
            table.add_column("Target Jual")
            table.add_column("Status")

            is_limited = False

            for idx, target_item in enumerate(WATCH_LIST, 1):
                item_name = target_item["name"]
                target_price = target_item["target"]
                category_name = target_item.get("category", "GENERAL")

                raw_price = get_cs2_price(item_name)

                if raw_price == "LIMITED":
                    is_limited = True
                    table.add_row(str(idx), category_name, item_name, "[yellow]LIMITED (429)[/yellow]", f"Rp {target_price:,}", "[yellow]Menunggu Reset...[/yellow]")
                    continue
                elif raw_price:
                    clean_str = raw_price.replace("Rp", "").replace(".", "").strip()
                    current_price = int(clean_str)

                    if current_price >= target_price:
                        status_str = "[green]Target Tercapai![/green]"
                        if not notified_status[item_name]:
                            msg = f"{item_name} menembus Rp {current_price:,}!"
                            send_desktop_notification("📈 Target Harga CS2 Tercapai!", msg)
                            notified_status[item_name] = True
                    else:
                        status_str = "[yellow]Hold / Belum Capai[/yellow]"
                        notified_status[item_name] = False

                    table.add_row(str(idx), category_name, item_name, f"Rp {current_price:,}", f"Rp {target_price:,}", status_str)
                else:
                    table.add_row(str(idx), category_name, item_name, "[red]Gagal Fetch[/red]", f"Rp {target_price:,}", "[red]Error Koneksi[/red]")

                # Jeda acak 3–7 detik antar item (Roadmap 3)
                waktu_jeda = random.randint(3, 7)
                time.sleep(waktu_jeda)

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