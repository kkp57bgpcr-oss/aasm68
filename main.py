import telebot # 确保是小写
import requests
import time
import re
import threading
import json
import os
import itertools
from datetime import datetime, timedelta
from telebot import types
from concurrent.futures import ThreadPoolExecutor

# ================= 1. 核心配置 =================
API_TOKEN = '8338893180:AAH-l_4m1-tweKyt92bliyk4fsPqoPQWzpU'
ADMIN_ID = 6649617045 
ADMIN_USERNAME = "@aaSm68"
POINTS_FILE = 'points.json'
TOKEN_FILE = 'token.txt'
SVIP_FILE = 'svip.json' # 新增：SVIP数据文件
DEFAULT_TOKEN = "eyJhbGciOiJIUzUxMiIsInR5cCI6IkpXVCJ9.eyJ1c2VySWQiOiIyNDkyNDYiLCJpYXQiOjE3Mzg1MDMxMTcsImV4cCI6MTczODY3NTkxN30.i9w1G8Y2mU5R5cCI6IkpXVCJ9" 

bot = telebot.TeleBot(API_TOKEN)
user_states = {}
generated_cache = {} 
TOTAL_QUERIES = 0

def load_data():
    pts, svip = {}, {}
    if os.path.exists(POINTS_FILE):
        try:
            with open(POINTS_FILE, 'r') as f:
                data = json.load(f)
                pts = {int(k): v for k, v in data.items()}
        except: pass
    if os.path.exists(SVIP_FILE):
        try:
            with open(SVIP_FILE, 'r') as f:
                svip = json.load(f)
        except: pass
    tk = DEFAULT_TOKEN
    if os.path.exists(TOKEN_FILE):
        try:
            with open(TOKEN_FILE, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                if content: tk = content
        except: pass
    return pts, svip, tk

user_points, svip_users, CURRENT_X_TOKEN = load_data()

def save_points():
    with open(POINTS_FILE, 'w') as f:
        json.dump({str(k): v for k, v in user_points.items()}, f)

def save_svip():
    with open(SVIP_FILE, 'w') as f:
        json.dump(svip_users, f)

def save_token(new_tk):
    with open(TOKEN_FILE, 'w', encoding='utf-8') as f:
        f.write(new_tk)

# 检查是否为有效SVIP
def is_svip(uid):
    uid_str = str(uid)
    if uid_str in svip_users:
        expiry = datetime.strptime(svip_users[uid_str], '%Y-%m-%d %H:%M:%S')
        if expiry > datetime.now():
            return True
    return False

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
    return f"⌛ 开始核验...\n[{bar}] {done}/{total} {percent}%"

# --- 核心核验逻辑 ---
def run_batch_task(chat_id, msg_id, name, id_list, uid):
    global CURRENT_X_TOKEN, TOTAL_QUERIES
    TOTAL_QUERIES += 1
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
                status_line = "👤 用户状态：SVIP 会员" if is_svip(uid) else "👤 用户状态：普通用户"
                success_match = (
                    f"✅ 核验成功！\n\n"
                    f"{name} {id_no} 二要素核验一致✅\n\n"
                    f"{status_line}"
                )
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
    if uid not in user_points:
        user_points[uid] = 0
        save_points()
    user_states[message.chat.id] = {'step': 'v_name'}
    pts = user_points.get(uid, 0)
    status = "SVIP 会员" if is_svip(uid) else "普通用户"
    menu_text = (
        f"👋 **欢迎使用铭核验机器人**\n\n"
        f"💰 积分: `{pts}`\n"
        f"🌟 身份: `{status}`\n"
        f"💸 核验: `100`\n"
        f"🛠 生成: `50`\n"
        f"👤 管理员: {ADMIN_USERNAME}\n\n"
        f"📢 **当前模式：核验模式**\n请输入姓名开始，或发送 /gen 切换。"
    )
    bot.send_message(message.chat.id, menu_text, parse_mode='Markdown')

@bot.message_handler(commands=['admin'])
def admin_cmd(message):
    if message.from_user.id != ADMIN_ID:
        bot.reply_to(message, "🚫 **权限拒绝**")
        return
    admin_text = (
        f"👑 **管理员控制台**\n\n"
        f"👥 总用户数: {len(user_points)}\n"
        f"📊 总查询数: {TOTAL_QUERIES}\n\n"
        f"💡 管理指令：\n"
        f"`/add 用户ID 分数` (充值积分)\n"
        f"`/svip 用户ID 天数` (授权SVIP)"
    )
    bot.send_message(message.chat.id, admin_text, parse_mode='Markdown')

@bot.message_handler(commands=['svip'])
def add_svip(message):
    if message.from_user.id != ADMIN_ID: return
    try:
        parts = message.text.split()
        target_id, days = parts[1], int(parts[2])
        expiry_date = (datetime.now() + timedelta(days=days)).strftime('%Y-%m-%d %H:%M:%S')
        svip_users[str(target_id)] = expiry_date
        save_svip()
        bot.reply_to(message, f"✅ 授权成功！\n用户: `{target_id}`\n级别: `SVIP 会员`\n到期时间: `{expiry_date}`", parse_mode='Markdown')
    except:
        bot.reply_to(message, "❌ 格式错误：`/svip 用户ID 天数`")

@bot.message_handler(commands=['add'])
def add_points(message):
    if message.from_user.id != ADMIN_ID: return
    try:
        parts = message.text.split()
        tid, amt = int(parts[1]), int(parts[2])
        user_points[tid] = user_points.get(tid, 0) + amt
        save_points()
        bot.reply_to(message, f"✅ 充值成功！用户 `{tid}` 余额: `{user_points[tid]}`")
    except:
        bot.reply_to(message, "❌ 格式错误：`/add 用户ID 积分`")

@bot.message_handler(commands=['gen'])
def gen_cmd(message):
    user_states[message.chat.id] = {'step': 'g_card'}
    bot.send_message(message.chat.id, f"🛠 **进入生成模式**\n请输入身份证补全号:")

@bot.message_handler(func=lambda m: True)
def handle_all_messages(message):
    uid, chat_id, text = message.from_user.id, message.chat.id, message.text.strip()
    if text.startswith('/'): return
    state = user_states.get(chat_id)
    if not state: return

    if state['step'] == 'v_name':
        user_states[chat_id].update({'step': 'v_ids', 'name': text})
        bot.send_message(chat_id, f"✅ 已记录姓名：`{text}`\n请发送身份证：")
        
    elif state['step'] == 'v_ids':
        v_ids = [i for i in re.findall(r'\d{17}[\dXx]', text) if is_valid_id(i)]
        if v_ids:
            if is_svip(uid) or user_points.get(uid, 0) >= 100:
                if not is_svip(uid): # 只有非SVIP扣分
                    user_points[uid] -= 100
                    save_points()
                msg = bot.send_message(chat_id, get_ui_bar(0, len(v_ids)))
                threading.Thread(target=run_batch_task, args=(chat_id, msg.message_id, state['name'], v_ids, uid)).start()
            else:
                bot.send_message(chat_id, "❌ 积分不足（需100积分）。")
        del user_states[chat_id]

    elif state['step'] == 'g_card':
        user_states[chat_id].update({'step': 'g_sex', 'card': text.lower()})
        bot.send_message(chat_id, "请输入性别 (男/女):")

    elif state['step'] == 'g_sex':
        if not is_svip(uid) and user_points.get(uid, 0) < 50:
            bot.send_message(chat_id, "❌ 积分不足（需50积分）。")
            return
        char_sets = [list(ch) if ch != 'x' else list("0123456789") for ch in state['card']]
        if text == "男": char_sets[16] = ["1", "3", "5", "7", "9"]
        elif text == "女": char_sets[16] = ["0", "2", "4", "6", "8"]
        ids = [num for res in itertools.product(*char_sets) if is_valid_id(num := "".join(res))][:5000]
        if ids:
            if not is_svip(uid):
                user_points[uid] -= 50
                save_points()
            generated_cache[uid] = ids 
            with open("铭.txt", "w") as f: f.write("\n".join(ids))
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton(f"🚀 立即核验 (SVIP免积分)", callback_data="start_verify_flow"))
            bot.send_document(chat_id, open("铭.txt", "rb"), caption=f"✅ 生成成功！共 `{len(ids)}` 个", reply_markup=markup)
        del user_states[chat_id]

    elif state['step'] == 'v_name_after_gen':
        if uid in generated_cache:
            if not is_svip(uid):
                user_points[uid] -= 100
                save_points()
            msg = bot.send_message(chat_id, get_ui_bar(0, len(generated_cache[uid])))
            threading.Thread(target=run_batch_task, args=(chat_id, msg.message_id, text, generated_cache[uid], uid)).start()
        del user_states[chat_id]

@bot.callback_query_handler(func=lambda call: call.data == "start_verify_flow")
def callback_start_verify(call):
    bot.send_message(call.message.chat.id, "👤 请输入姓名:")
    user_states[call.message.chat.id] = {'step': 'v_name_after_gen'}
    bot.answer_callback_query(call.id)

if __name__ == '__main__':
    bot.infinity_polling()
