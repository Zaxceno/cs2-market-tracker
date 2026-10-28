# CS2 Market Price Tracker

Sebuah Command Line Interface (CLI) berbasis Python untuk melacak harga item Counter-Strike 2 di Steam Community Market secara real-time. Proyek ini dirancang khusus untuk lingkungan Linux dengan mengintegrasikan antarmuka terminal dan sistem notifikasi desktop bawaan.

## Fitur Utama

* Real-time API Integration: Mengambil data harga langsung dari Steam Community Market menggunakan HTTP requests.
* Bypass Steam Rate Limits: Mengimplementasikan modifikasi User-Agent headers untuk menyimulasikan request dari browser Linux standar.
* Aesthetic TUI (Text User Interface): Output terminal dirender menggunakan library rich untuk menampilkan panel dan indikator status yang rapi.
* Native Linux Notifications: Mengeksekusi perintah notify-send secara internal melalui modul subprocess Python untuk memunculkan pop-up notifikasi di lingkungan desktop GNOME/Linux ketika harga mencapai target jual.

## Tech Stack

* Bahasa: Python 3
* Library Eksternal: requests (API handling), rich (Terminal UI)
* OS Integration: subprocess (Native OS command execution)

## Cara Menjalankan (Instalasi Lokal)

1. Clone repositori ini:
   ```bash
   git clone [https://github.com/Zaxceno/cs2-market-tracker.git](https://github.com/Zaxceno/cs2-market-tracker.git)
   cd cs2-market-tracker