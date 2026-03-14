import re
import os
import subprocess
from datetime import datetime, timedelta
import pytz

# GANTI DENGAN PATH KE FILE PLAYLIST ABANG DI VPS
PLAYLIST_PATH = "/root/cocot/playlist.m3u"
# ESTIMASI DURASI LIVE (misal 3 jam, setelah itu dianggap selesai)
LIVE_DURATION_HOURS = 3 

def process_playlist():
    with open(PLAYLIST_PATH, 'r', encoding='utf-8') as f:
        content = f.read()

    # Kunci zona waktu ke WIB (Asia/Jakarta)
    tz_wib = pytz.timezone('Asia/Jakarta')
    now_wib = datetime.now(tz_wib)
    
    updated = False
    
    # Cari semua baris yang mengandung format "Upcoming" dan ambil jam serta nama event-nya
    # Pola: group-title="⏳ Upcoming",⏳ [HH:MM] Nama Event
    pattern = r'group-title="⏳ Upcoming",⏳ \[(\d{2}:\d{2})\] (.*)'
    
    for match in re.finditer(pattern, content):
        full_match = match.group(0)
        time_str = match.group(1) # Ambil jam, cth: 01:44
        event_name = match.group(2) # Ambil nama event, cth: New Zealand vs Fiji
        
        # Jadikan string jam tadi sebagai objek waktu untuk hari ini di WIB
        event_time = datetime.strptime(time_str, "%H:%M").replace(
            year=now_wib.year, month=now_wib.month, day=now_wib.day
        )
        event_time_wib = tz_wib.localize(event_time)
        
        # Logika Pengecekan: Apakah jam sekarang >= jam event DAN belum lewat durasi live?
        if now_wib >= event_time_wib and now_wib <= (event_time_wib + timedelta(hours=LIVE_DURATION_HOURS)):
            # Sulap string-nya jadi format Live Event
            new_str = f'group-title="🔴 Live Event",🔴 {event_name}'
            content = content.replace(full_match, new_str)
            updated = True
            print(f"Update ke Live: {event_name} (Jadwal: {time_str} WIB)")

    # Kalau ada perubahan, simpan (timpa) file m3u-nya
    if updated:
        with open(PLAYLIST_PATH, 'w', encoding='utf-8') as f:
            f.write(content)
        print("Playlist berhasil diperbarui dengan status Live terbaru.")
    
    return updated

def push_to_github():
    # Masuk ke folder repo dan push ke GitHub
    tz_wib = pytz.timezone('Asia/Jakarta')
    now_wib_str = datetime.now(tz_wib).strftime('%H:%M WIB')
    
    repo_dir = os.path.dirname(PLAYLIST_PATH)
    os.chdir(repo_dir)
    subprocess.run(["git", "add", "."], check=True)
    subprocess.run(["git", "commit", "-m", f"Auto-update Live Events - {now_wib_str}"], check=True)
    subprocess.run(["git", "push"], check=True)
    print("Perubahan berhasil di-push ke GitHub!")

if __name__ == "__main__":
    if process_playlist():
        push_to_github()
    else:
        print("Belum ada event baru yang masuk jam tayang.")
