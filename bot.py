"""
 ________  __                        __    __  __              __                _______                                                     __                    
/        |/  |                      /  |  /  |/  |            /  |              /       \                                                   /  |                   
$$$$$$$$/ $$ |____    ______        $$ | /$$/ $$/  _____  ____$$ |_______       $$$$$$$  | ______    ______    _______   ______   _______  _$$ |_    _______       
   $$ |   $$      \  /      \       $$ |/$$/  /  |/     \/    \$//       |      $$ |__$$ |/      \  /      \  /       | /      \ /       \ / $$   |  /       |      
   $$ |   $$$$$$$  |/$$$$$$  |      $$  $$<   $$ |$$$$$$ $$$$  |/$$$$$$$/       $$    $$//$$$$$$  |/$$$$$$  |/$$$$$$$/ /$$$$$$  |$$$$$$$  |$$$$$$/  /$$$$$$$/       
   $$ |   $$ |  $$ |$$    $$ |      $$$$$  \  $$ |$$ | $$ | $$ |$$      \       $$$$$$$/ $$ |  $$/ $$    $$ |$$      \ $$    $$ |$$ |  $$ |  $$ | __$$      \       
   $$ |   $$ |  $$ |$$$$$$$$/       $$ |$$  \ $$ |$$ | $$ | $$ | $$$$$$  |      $$ |     $$ |      $$$$$$$$/  $$$$$$  |$$$$$$$$/ $$ |  $$ |  $$ |/  |$$$$$$  |      
   $$ |   $$ |  $$ |$$       |      $$ | $$  |$$ |$$ | $$ | $$ |/     $$/       $$ |     $$ |       $$       |/     $$/ $$       |$$ |  $$ |  $$  $$//     $$/       
   $$/    $$/   $$/  $$$$$$$/       $$/   $$/ $$/ $$/  $$/  $$/ $$$$$$$/        $$/      $$/        $$$$$$$/ $$$$$$$/   $$$$$$$/ $$/   $$/    $$$$/ $$$$$$$/        
"""

import discord
from discord.ext import commands
import yt_dlp
import asyncio
import os
import aiohttp
from bs4 import BeautifulSoup
import re
import time
from collections import defaultdict
from dotenv import load_dotenv

# Load environment variables (useful for local testing)
load_dotenv()

# Setup Discord Intents
intents = discord.Intents.default()
intents.message_content = True
# Removed help_command=None so we can use standard help or override it properly
bot = commands.Bot(command_prefix="!", intents=intents)

# Override default help command to prevent conflict
bot.remove_command('help')

# Cooldown dictionary: {channel_id: [timestamps]}
channel_cooldowns = defaultdict(list)
COOLDOWN_LIMIT = 5
COOLDOWN_TIME = 35  # seconds

def check_cooldown(channel_id):
    now = time.time()
    # Filter timestamps older than COOLDOWN_TIME
    channel_cooldowns[channel_id] = [ts for ts in channel_cooldowns[channel_id] if now - ts < COOLDOWN_TIME]
    
    if len(channel_cooldowns[channel_id]) >= COOLDOWN_LIMIT:
        oldest_ts = channel_cooldowns[channel_id][0]
        remaining = int(COOLDOWN_TIME - (now - oldest_ts))
        return False, remaining
    
    # Add new execution timestamp
    channel_cooldowns[channel_id].append(now)
    return True, 0

async def upload_to_top4top(file_path):
    url = "https://top4top.io/"
    async with aiohttp.ClientSession() as session:
        # 1. Scraping the upload page to find form structure (file input name, hidden fields, action url)
        async with session.get(url) as resp:
            html = await resp.text()
            soup = BeautifulSoup(html, 'html.parser')
            form = soup.find('form', attrs={'enctype': 'multipart/form-data'})
            
            post_url = "https://top4top.io/index.php"
            file_input_name = "file_1_"
            
            if form:
                action = form.get('action')
                if action:
                    if action.startswith('http'):
                        post_url = action
                    else:
                        post_url = "https://top4top.io/" + action.lstrip('/')
                
                # find file input name
                file_input = form.find('input', type='file')
                if file_input and file_input.get('name'):
                    file_input_name = file_input.get('name')
            
        data = aiohttp.FormData()
        
        # Add hidden fields if they exist (sometimes required for CSRF or settings)
        if form:
            for hidden in form.find_all('input', type='hidden'):
                name = hidden.get('name')
                value = hidden.get('value', '')
                if name:
                    data.add_field(name, value)
                    
        # Add the mp3 file
        data.add_field(
            file_input_name, 
            open(file_path, 'rb'), 
            filename=os.path.basename(file_path), 
            content_type='audio/mpeg'
        )
        
        # Add submit button value
        submit_btn = form.find('input', type='submit') if form else None
        if submit_btn and submit_btn.get('name'):
            data.add_field(submit_btn.get('name'), submit_btn.get('value', 'Upload'))
        else:
            data.add_field('submit', 'Upload')
            
        # 2. Execute POST request
        async with session.post(post_url, data=data) as upload_resp:
            result_html = await upload_resp.text()
            
            # 3. Extract the direct .mp3 link from the response
            # Search via regex first for robust extraction
            match = re.search(r'https?://[a-zA-Z0-9\-\.]+\.top4top\.io/[a-zA-Z0-9_]+\.mp3', result_html)
            if match:
                return match.group(0)
            
            # Fallback: Find input elements containing .mp3 and top4top
            soup2 = BeautifulSoup(result_html, 'html.parser')
            for input_tag in soup2.find_all('input'):
                val = input_tag.get('value', '')
                if '.mp3' in val and 'top4top' in val:
                    return val
            
            raise Exception("Direct link MP3 tidak ditemukan. Top4Top mungkin gagal memproses file atau mengubah struktur website-nya.")

@bot.event
async def on_ready():
    print(f'✅ Login berhasil sebagai {bot.user}')
    if not os.path.exists('downloads'):
        os.makedirs('downloads')
    # Set custom presence
    await bot.change_presence(activity=discord.Game(name="!bb help | SA-MP Boombox"))

@bot.command(name='bb')
async def bb_command(ctx, *, query: str = None):
    if not query:
        await ctx.send("ℹ️ **Cara Penggunaan:**\n- `!bb [youtube link]` - Untuk convert link YouTube.\n- `!bb search [judul lagu/artist]` - Untuk mencari dan convert lagu.")
        return

    # Check Rate Limit (Channel-based)
    allowed, remaining = check_cooldown(ctx.channel.id)
    if not allowed:
        await ctx.send(f"⏳ **Cooldown Aktif!** Mohon tunggu **{remaining} detik** sebelum menggunakan command ini lagi di channel ini.")
        return

    is_search = False
    if query.lower().startswith('search '):
        query = query[7:] # Remove 'search ' from string
        is_search = True
        
    status_msg = await ctx.send(f"🔄 Sedang memproses {'pencarian' if is_search else 'link'}: `{query}` ...")
    
    loop = asyncio.get_event_loop()
    
    def download_audio():
        opts = {
            'format': 'bestaudio/best',
            'outtmpl': 'downloads/%(id)s.%(ext)s',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'cookiefile': 'cookies.txt', # 👈 INI YANG DITAMBAHKAN BIAR GAK MINTA LOGIN
            'quiet': True,
            'noplaylist': True
        }
        # If it's a search, use ytsearch1 to get the first result
        search_query = f"ytsearch1:{query}" if is_search else query
        
        with yt_dlp.YoutubeDL(opts) as ydl:
            info = ydl.extract_info(search_query, download=True)
            if 'entries' in info:
                # It's a search result list, get the first entry
                info = info['entries'][0]
            
            title = info.get('title', 'Unknown Title')
            filename = ydl.prepare_filename(info)
            # Replace the original extension with .mp3 because ffmpeg changes it
            base, _ = os.path.splitext(filename)
            mp3_filename = base + '.mp3'
            
            return title, mp3_filename

    try:
        title, file_path = await loop.run_in_executor(None, download_audio)
    except Exception as e:
        await status_msg.edit(content=f"❌ **Gagal mengunduh audio:**\n```\n{str(e)}\n```")
        return
        
    await status_msg.edit(content=f"⬆️ Berhasil mengunduh **{title}**. Mengunggah ke Top4Top...")
    
    try:
        direct_link = await upload_to_top4top(file_path)
        await status_msg.edit(content=f"✅ **Selesai!**\n🎵 Judul: **{title}**\n🔗 Direct Link MP3: {direct_link}\n\n*Link ini bisa langsung kamu gunakan di in-game boombox.*")
    except Exception as e:
        await status_msg.edit(content=f"❌ **Gagal mengunggah ke Top4Top:**\n```\n{str(e)}\n```")
    finally:
        # Storage Cleanup - Immediately remove local file
        if os.path.exists(file_path):
            os.remove(file_path)
            
@bot.command(name='help')
async def help_command(ctx):
    help_text = """
**🤖 SA-MP Boombox Bot**
Bot ini akan membantu kamu membuat direct link `.mp3` dari YouTube.

**Commands:**
`!bb [youtube link]` - Convert video dari link YouTube.
`!bb search [judul/artist]` - Mencari video di YouTube dan langsung convert.

**Info Limitasi:**
- Maksimal penggunaan adalah 5 kali per 35 detik untuk setiap channel.
- File audio langsung diunggah ke *Top4Top* dan dihapus dari server lokal bot untuk menghemat storage.
"""
    await ctx.send(help_text)

if __name__ == '__main__':
    # Pastikan file .env memiliki variabel DISCORD_TOKEN
    token = os.getenv("DISCORD_TOKEN")
    if not token:
        print("❌ ERROR: DISCORD_TOKEN tidak ditemukan. Harap set token di file .env atau environment variable (khusus deployment).")
    else:
        bot.run(token)
