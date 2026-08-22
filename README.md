# SA-MP Boombox Discord Bot 🎵

Bot Discord ini dirancang khusus untuk komunitas SA-MP, membantu mendapatkan direct link `.mp3` dari video YouTube yang dapat langsung digunakan pada in-game boombox.

## Fitur Utama:
1. **`!bb [youtube link]`**: Mengonversi langsung dari URL YouTube.
2. **`!bb search [judul/artist]`**: Mencari lagu di YouTube dan mengonversi hasil pencarian teratas.
3. **Limitasi & Cooldown**: Terbatas maksimal 5 penggunaan per 35 detik per channel untuk menghindari spam.
4. **Auto-upload Top4Top**: Audio yang diunduh langsung diunggah ke `top4top.io` untuk mendapatkan direct link `mp3`, lalu otomatis dihapus dari server bot demi menghemat storage lokal.

## Persiapan Lokal
1. Pastikan Anda memiliki Python 3.8+ yang terinstal.
2. Instal FFmpeg pada OS Anda (Windows/Linux) dan pastikan path FFmpeg tersedia pada environment variables.
3. Instal dependencies menggunakan command:
   ```bash
   pip install -r requirements.txt
   ```
4. Buat file `.env` di folder yang sama (lihat contoh di `.env.example`) dan isi dengan Token Bot Anda:
   ```env
   DISCORD_TOKEN=TokenBotDiscordAnda
   ```
5. Jalankan bot:
   ```bash
   python bot.py
   ```

## Panduan Deployment ke Railway
Bot ini sudah siap untuk di-deploy ke Railway.
1. Buat project baru pada [Railway.app](https://railway.app/).
2. Sambungkan dengan repository GitHub yang berisi seluruh kode ini (atau upload manual).
3. **Penting! Aptfile**: File `Aptfile` sudah disertakan dan akan otomatis menginstal `ffmpeg` (dibutuhkan oleh `yt-dlp` untuk memproses file `.mp3` pada container Linux milik Railway).
4. Masuk ke tab **Variables** di Railway. Tambahkan variabel environment:
   - **Variable Name:** `DISCORD_TOKEN`
   - **Value:** (Token Bot Discord Anda)
5. Railway akan mendeteksi `requirements.txt` dan memulai build dengan Python.
6. Tunggu hingga deploy selesai dan bot Anda akan online.
# boombox-generate
