import requests
import time
import random
import os
import json
import threading
from datetime import datetime

# --- Configuration ---
TOKENS_FILE = "tokens.txt"
MESSAGE_CONTENT = "Hello from automated tool!"

# --- Colors for Terminal ---
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    # New colors for modern look
    PURPLE = '\033[35m'
    VIOLET = '\033[95m'
    RED = '\033[31m'
    LIGHT_RED = '\033[91m'

# Khóa để đồng bộ hóa việc in log ra màn hình
print_lock = threading.Lock()

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def log(message, type="info", token_id=""):
    timestamp = datetime.now().strftime("%H:%M:%S")
    prefix = f"[{token_id}] " if token_id else ""
    with print_lock:
        if type == "info":
            print(f"[{timestamp}] {prefix}{Colors.PURPLE}[INFO]{Colors.ENDC} {message}")
        elif type == "success":
            print(f"[{timestamp}] {prefix}{Colors.LIGHT_RED}[SUCCESS]{Colors.ENDC} {message}")
        elif type == "warn":
            print(f"[{timestamp}] {prefix}{Colors.WARNING}[WARN]{Colors.ENDC} {message}")
        elif type == "error":
            print(f"[{timestamp}] {prefix}{Colors.FAIL}[ERROR]{Colors.ENDC} {message}")

def load_list(filename):
    if not os.path.exists(filename):
        return []
    with open(filename, "r") as f:
        return [line.strip() for line in f if line.strip() and not line.startswith("#")]

def get_headers(token):
    return {
        "Authorization": token,
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

def get_guilds(token):
    url = "https://discord.com/api/v9/users/@me/guilds"
    try:
        response = requests.get(url, headers=get_headers(token))
        if response.status_code == 200:
            return response.json()
    except:
        pass
    return []

def get_channels(token, guild_id):
    url = f"https://discord.com/api/v9/guilds/{guild_id}/channels"
    try:
        response = requests.get(url, headers=get_headers(token))
        if response.status_code == 200:
            return [c for c in response.json() if c['type'] == 0]
    except:
        pass
    return []

def get_private_channels(token):
    url = "https://discord.com/api/v9/users/@me/channels"
    try:
        response = requests.get(url, headers=get_headers(token))
        if response.status_code == 200:
            return response.json()
    except:
        pass
    return []

def send_message(token, channel_id, content):
    url = f"https://discord.com/api/v9/channels/{channel_id}/messages"
    payload = {"content": content}
    
    try:
        response = requests.post(url, headers=get_headers(token), data=json.dumps(payload))
        if response.status_code == 200 or response.status_code == 201:
            return True, response.json()
        elif response.status_code == 429:
            retry_after = response.json().get("retry_after", 5)
            time.sleep(retry_after)
            return send_message(token, channel_id, content)
        elif response.status_code == 403:
            return False, "Không có quyền gửi"
        elif response.status_code == 401:
            return False, "Invalid Token"
        else:
            return False, f"Lỗi {response.status_code}"
    except Exception as e:
        return False, str(e)

def process_token(token, content, send_to_guilds, send_to_dms, sleep_between_rounds):
    short_token = token[:10] + "..." + token[-5:] if len(token) > 20 else token
    
    while True:
        log(f"Bắt đầu chạy cho token: {short_token}", "info", short_token)
        
        # --- Xử lý Guilds ---
        if send_to_guilds:
            guilds = get_guilds(token)
            log(f"Tìm thấy {len(guilds)} servers.", "info", short_token)
            for guild in guilds:
                guild_name = guild.get('name', 'Unknown')
                channels = get_channels(token, guild['id'])
                if not channels: continue

                target_channels = [c for c in channels if 'general' in c['name'].lower() or 'chat' in c['name'].lower()]
                if not target_channels: target_channels = [channels[0]] 
                
                for channel in target_channels:
                    log(f"Gửi Server: {guild_name} > #{channel['name']}...", "info", short_token)
                    success, result = send_message(token, channel['id'], content)
                    if success: log(f"Thành công!", "success", short_token)
                    else: log(f"Thất bại: {result}", "error", short_token)
                    time.sleep(random.uniform(5, 7))

        # --- Xử lý DMs ---
        if send_to_dms:
            dms = get_private_channels(token)
            log(f"Tìm thấy {len(dms)} cuộc hội thoại DM.", "info", short_token)
            for dm in dms:
                recipients = ", ".join([u.get('username', 'Unknown') for u in dm.get('recipients', [])])
                log(f"Gửi DM: {recipients}...", "info", short_token)
                
                success, result = send_message(token, dm['id'], content)
                if success: log(f"Thành công!", "success", short_token)
                else: log(f"Thất bại: {result}", "error", short_token)
                time.sleep(random.uniform(5, 10))
        
        if sleep_between_rounds > 0:
            log(f"Hoàn thành lượt. Nghỉ {sleep_between_rounds} phút...", "info", short_token)
            time.sleep(sleep_between_rounds * 60)
        else:
            log(f"Hoàn thành lượt. Tự động dừng theo yêu cầu.", "info", short_token)
            break

def main():
    R = Colors.LIGHT_RED
    P = Colors.PURPLE
    C = Colors.OKCYAN
    G = Colors.OKGREEN
    W = Colors.WARNING
    B = Colors.BOLD
    E = Colors.ENDC
    K = Colors.RED

    while True:
        clear_screen()
        print(f"""
{K} ⠀⠀⠀⠈⠓⠶⣤⣀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠈⠻⢿⣶⣄⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⢠⣿⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠙⢿⣿⣤⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⢸⡇⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠙⢿⣿⣄⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⣼⣇⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠈⢻⣿⡀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀           
⣿⣿⠀⠀⠀⠀⠀⣤⣤⣶⣶⣶⣦⡄⠀⠀⢸⣿⡇⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀      Telegram: @kuina199⠀
⢻⣿⡀⠀⠀⢠⣾⣿⣿⣻⣿⣿⣿⣿⣷⡀⢸⣿⠇⠀⠀⠀⣰⣦⠀⠀⠀⠀⠀⠀     Disord: lvh.05
⠈⢿⣇⠀⠀⣿⣿⣿⣯⣿⣿⣿⣿⣿⣿⣷⣼⣿⠁⠀⠀⣸⣿⠏⠀⠀⠀⠀⠀⠀     Không Vi Phạm Pháp Luật
⠀⠸⣿⡄⠀⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⠀⠀⢠⣿⠏⠀⠀⠀⠀⠀⠀⠀
⠀⠀⢿⣿⣤⡘⣿⣿⣿⣿⣿⣿⣿⣿⢿⣿⣿⡿⠀⣰⣿⠏⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠈⠙⢿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣇⣴⡿⠟⠀⠀⣠⣤⣄⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠈⠙⠻⠿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣷⠿⠿⡿⠟⠋⠻⣿⣦⡀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⢀⣠⣶⣦⣽⣿⣿⣿⣿⣿⡿⠻⣷⣄⠀⠀⠀⠀⠈⠻⣿⣦
⠀⠀⠀⠀⠀⠀⠀⠀⣾⠟⠁⠈⠉⣸⣿⣿⣿⣿⣷⠀⠘⢿⣷⣄⠀⠀⠀⢀⣿⠟
⠀⠀⠀⠀⠀⠀⠀⢸⠃⠀⠀⠀⣰⡿⣻⡏⠙⠳⠃⠀⠀⠀⠙⢿⣿⣦⡴⠟⠁⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⣼⡟⢡⣿⠇⠀⠀⠀⠀⠀⠀⠀⠀⠘⢿⣿⡄⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⣴⣿⠋⠀⣼⡿⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠈⣿⣧⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⢠⣿⡇⠀⢸⣿⠃⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠸⣿⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⢸⣿⡆⠀⠀⣿⡆⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢹⡇⠀
⠀⠀⠀⠀⠀⠀⠀⠀⣸⣿⠀⠀⠀⣿⣧⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣷⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠘⣿⡀⠀⠀⠻⢿⣆⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣿⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠈⢧⠀⠀⠀⠈⠻⣧⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠈⠀⠀⠀⠀⠀⠈⢷⡀⠀⠀⠀⠀⠀⠀⠀⠀
""")

        tokens = load_list(TOKENS_FILE)
        if not tokens:
            log(f"Không tìm thấy token trong {TOKENS_FILE}", "error")
            input("Nhấn Enter để thử lại...")
            continue

        log(f"Đã nạp {len(tokens)} tokens.", "info")
        
        try:
            msg = input(f"{Colors.BOLD}Nhập nội dung tin nhắn: {Colors.ENDC}")
            content = msg if msg else MESSAGE_CONTENT

            send_to_guilds = input(f"{Colors.BOLD}Gửi vào Server? (y/n): {Colors.ENDC}").lower() == 'y'
            send_to_dms = input(f"{Colors.BOLD}Gửi vào DM? (y/n): {Colors.ENDC}").lower() == 'y'

            try:
                sleep_between_rounds = int(input(f"{Colors.BOLD}Nghỉ bao nhiêu phút giữa mỗi lượt? (0 để gửi 1 lần rồi dừng): {Colors.ENDC}"))
            except:
                sleep_between_rounds = 0
        except KeyboardInterrupt:
            print("\nĐang thoát...")
            break

        log("Đang khởi tạo các luồng chạy song song...", "info")
        
        threads = []
        for token in tokens:
            t = threading.Thread(target=process_token, args=(token, content, send_to_guilds, send_to_dms, sleep_between_rounds))
            t.start()
            threads.append(t)
            time.sleep(1)

        for t in threads:
            t.join()
        
        log("Tất cả tiến trình đã hoàn thành. Khởi động lại tool...", "success")
        time.sleep(2)

if __name__ == "__main__":
    main()
