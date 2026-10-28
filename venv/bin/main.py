import requests
import subprocess
from rich.console import Console
from rich.panel import Panel

console = Console()

# --- KONFIGURASI ---
# Nama case yang ingin dipantau (harus sama persis dengan URL Steam)
ITEM_NAME = "Dreams & Nightmares Case"
TARGET_PRICE = 12000  # Set target harga (misal: notif jika harga tembus Rp 12.000)

def get_cs2_price(item_name):
    url = f"https://steamcommunity.com/market/priceoverview/?appid=730&currency=39&market_hash_name={item_name}"
    
    # Tambahkan headers agar Steam mengira ini adalah browser Chrome di OS Linux
    headers = {
        "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    with console.status(f"[cyan]Mengambil data {item_name} dari Steam Market..."):
        try:
            # Sisipkan headers=headers di sini
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                data = response.json()
                if data.get("success"):
                    return data.get("lowest_price")
                else:
                    console.print("[red]Item tidak ditemukan atau nama salah.[/red]")
            elif response.status_code == 429:
                console.print("[yellow]Terkena limit API Steam (Terlalu banyak request). Coba lagi nanti.[/yellow]")
            else:
                console.print(f"[red]Gagal menembak API. Status Code: {response.status_code}[/red]")
        except Exception as e:
            console.print(f"[red]Error koneksi: {e}[/red]")
    return None

def send_gnome_notification(title, message):
    # Menjalankan perintah notify-send murni milik Linux
    subprocess.run(["notify-send", "-a", "CS2 Tracker", "-u", "normal", title, message])

def main():
    console.print(Panel.fit("[bold green]CS2 Market Tracker Started[/bold green]", border_style="green"))
    
    raw_price = get_cs2_price(ITEM_NAME)
    
    if raw_price:
        # Steam merespons dengan string seperti "Rp 11.500"
        # Kita perlu membersihkan teksnya agar bisa dikalkulasi sebagai angka (Integer)
        clean_price_str = raw_price.replace("Rp", "").replace(".", "").strip()
        current_price = int(clean_price_str)
        
        console.print(f"Harga saat ini: [bold yellow]Rp {current_price:,}[/bold yellow]")
        console.print(f"Target jual   : [bold cyan]Rp {TARGET_PRICE:,}[/bold cyan]")
        
        if current_price >= TARGET_PRICE:
            msg = f"Waktunya jual! Harga {ITEM_NAME} menembus Rp {current_price:,}"
            console.print(f"[bold green]{msg}[/bold green]")
            # Tembak notifikasi ke desktop GNOME
            send_gnome_notification("📈 Harga CS2 Naik!", msg)
        else:
            console.print("[dim]Harga belum mencapai target. Hold dulu.[/dim]")

if __name__ == "__main__":
    main()