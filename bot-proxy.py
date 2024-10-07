import json
import time
import os
import random
import concurrent.futures
from datetime import datetime
import urllib.parse
import cloudscraper
from colorama import Fore, Style, init
from dateutil import parser
from dateutil.tz import tzutc
from pyfiglet import Figlet

init(autoreset=True)

def rgb_to_ansi(r, g, b):
    return f"\033[38;2;{r};{g};{b}m"

def interpolate_color(start_color, end_color, factor: float):
    return (
        int(start_color[0] + (end_color[0] - start_color[0]) * factor),
        int(start_color[1] + (end_color[1] - start_color[1]) * factor),
        int(start_color[2] + (end_color[2] - start_color[2]) * factor),
    )

def print_gradient_text(text, start_color, end_color):
    for i, char in enumerate(text):
        factor = i / len(text)
        r, g, b = interpolate_color(start_color, end_color, factor)
        print(rgb_to_ansi(r, g, b) + char, end="")
    print(Style.RESET_ALL)  # Reset colors after the text

class VooiDC:
    def __init__(self):
        self.base_headers = {
            "Accept": "application/json, text/plain, */*",
            "Accept-Encoding": "gzip, deflate, br",
            "Accept-Language": "vi-VN,vi;q=0.9,fr-FR;q=0.8,fr;q=0.7,en-US;q=0.6,en;q=0.5",
            "Content-Type": "application/json",
            "Origin": "https://app.tg.vooi.io",
            "Referer": "https://app.tg.vooi.io/",
            "Sec-Ch-Ua": '"Not/A)Brand";v="99", "Google Chrome";v="115", "Chromium";v="115"',
            "Sec-Ch-Ua-Mobile": "?0",
            "Sec-Ch-Ua-Platform": '"Windows"',
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-site",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36"
        }
        self.scraper = cloudscraper.create_scraper()
        self.access_token = None
        self.current_proxy = None

    start_color = (230, 230, 250)  # Lavender color for lighter purple
    end_color = (128, 0, 128)      # Purple

    def display_banner():
        custom_fig = Figlet(font='slant')
        os.system("cls" if os.name == "nt" else "clear")
        print('')
        print_gradient_text(custom_fig.renderText('PUTICOOL'), VooiDC.start_color, VooiDC.end_color)
        print(f"{Fore.GREEN}[+] Welcome & Enjoy Sir !{Fore.RESET}")
        print(f"{Fore.YELLOW}[+] Error? PM Telegram [https://t.me/NothingYub]{Fore.RESET}")
        print('')

    def set_proxy(self, proxy):
        self.current_proxy = proxy
        proxy_dict = {'http': proxy, 'https': proxy}
        self.scraper.proxies.update(proxy_dict)

    def check_proxy_ip(self):
        try:
            response = self.scraper.get('https://api.ipify.org?format=json', timeout=10)
            if response.status_code == 200:
                return response.json()['ip']
            else:
                return "Unknown"
        except Exception as e:
            self.log(f"Error checking proxy IP: {str(e)}", 'error')
            return "Error"

    def is_proxy_active(self, proxy):
        self.set_proxy(proxy)
        try:
            response = self.scraper.get('https://api.ipify.org?format=json', timeout=10)
            if response.status_code == 200:
                return True
        except Exception:
            return False
        return False

    def update_proxy_file(self, active_proxies):
        proxy_file = os.path.join(os.path.dirname(__file__), 'proxy.txt')
        with open(proxy_file, 'w', encoding='utf-8') as f:
            for proxy in active_proxies:
                f.write(f"{proxy}\n")
        self.log(f"Updated proxy.txt with {len(active_proxies)} active proxies.", 'success')

    def filter_active_proxies(self, proxies):
        active_proxies = []
        self.log("Checking proxies...", 'info')
        
        # Using multithreading to check proxies
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            future_to_proxy = {executor.submit(self.is_proxy_active, proxy): proxy for proxy in proxies}
            for future in concurrent.futures.as_completed(future_to_proxy):
                proxy = future_to_proxy[future]
                try:
                    if future.result():
                        self.log(f"Proxy {proxy} is active.", 'success')
                        active_proxies.append(proxy)
                    else:
                        self.log(f"Proxy {proxy} is inactive.", 'error')
                except Exception as e:
                    self.log(f"Error checking proxy {proxy}: {str(e)}", 'error')

        self.update_proxy_file(active_proxies)
        return active_proxies

    def get_headers(self):
        headers = self.base_headers.copy()
        if self.access_token:
            headers["Authorization"] = f"Bearer {self.access_token}"
        return headers

    def log(self, msg, type='info'):
        timestamp = datetime.now().strftime("%H:%M:%S")
        if type == 'success':
            print(f"[{timestamp}] [*] {Fore.GREEN}{msg}")
        elif type == 'custom':
            print(f"[{timestamp}] [*] {Fore.MAGENTA}{msg}")
        elif type == 'error':
            print(f"[{timestamp}] [!] {Fore.RED}{msg}")
        elif type == 'warning':
            print(f"[{timestamp}] [*] {Fore.YELLOW}{msg}")
        else:
            print(f"[{timestamp}] [*] {Fore.BLUE}{msg}")

    def countdown(self, seconds):
        for i in range(seconds, -1, -1):
            print(f"\r===== Waiting {i} seconds to continue the loop =====", end="", flush=True)
            time.sleep(1)
        print()

    def login_new_api(self, init_data):
        url = "https://api-tg.vooi.io/api/v2/auth/login"
        payload = {
            "initData": init_data,
            "inviterTelegramId": ""
        }

        try:
            response = self.scraper.post(url, json=payload, headers=self.get_headers())
            if response.status_code == 201:
                self.access_token = response.json()['tokens']['access_token']
                return {"success": True, "data": response.json()}
            else:
                return {"success": False, "error": 'Unexpected response status'}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def handle_autotrade(self):
        # Skipping full method code for brevity.
        pass

    def play_tapping_game(self):
        # Skipping full method code for brevity.
        pass

    def manage_tasks(self):
        # Skipping full method code for brevity.
        pass

    def main(self):
        data_file = os.path.join(os.path.dirname(__file__), 'data.txt')
        proxy_file = os.path.join(os.path.dirname(__file__), 'proxy.txt')

        with open(data_file, 'r', encoding='utf-8') as f:
            data = [line.strip() for line in f if line.strip()]

        with open(proxy_file, 'r', encoding='utf-8') as f:
            proxies = [line.strip() for line in f if line.strip()]

        # Step 1: Filter and update proxies
        active_proxies = self.filter_active_proxies(proxies)
        if not active_proxies:
            self.log("No active proxies found. Exiting...", 'error')
            return

        # Step 2: Process accounts using active proxies
        for i, (init_data, proxy) in enumerate(zip(data, active_proxies)):
            try:
                self.set_proxy(proxy)

                ip = self.check_proxy_ip()

                user_data = json.loads(urllib.parse.unquote(init_data.split('user=')[1].split('&')[0]))
                user_id = user_data['id']
                first_name = user_data['first_name']

                print(f"========== Account {i + 1} | {Fore.GREEN}{first_name} | IP: {ip} ==========")

                login_result = self.login_new_api(init_data)
                if login_result['success']:
                    self.log('Login successful!', 'success')
                    self.log(f"Name: {login_result['data']['name']}")
                    self.log(f"USD*: {login_result['data']['balances']['virt_money']}")
                    self.log(f"VT: {login_result['data']['balances']['vt']}")
                else:
                    self.log(f"Login failed: {login_result['error']}", 'error')

                self.countdown(20)

            except Exception as e:
                self.log(f"Error processing account {i + 1}: {str(e)}", 'error')
                continue

if __name__ == "__main__":
    VooiDC.display_banner()
    vooi_dc = VooiDC()
    vooi_dc.main()
