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

# 单次二要素固定 Token (接口 B)
AUTH_BEARER = "bearer eyJhbGciOiJIUzI1NiJ9.eyJwaG9uZSI6IisxOTM3ODg4NDgyNiIsIm9wZW5JZCI6Im95NW8tNHk3Wnd0WGlOaTVHQ3V3YzVVNDZJYk0iLCJpZENhcmRObyI6IjM3MDQ4MTE5ODgwODIwMzUxNCIsInVzZXJOYW1lIjoi6ams5rCR5by6IiwibG9naW5UaW1lIjoxNzY5NDE1NjYxMTk0LCJhcHBJZCI6Ind4ZjVmZDAyZDEwZGJiMjFkMiIsImlzcmVhbG5hbWUiOnRydWUsInNhYXNVc2VySWQiOm51bGwsImNvbXBhbnlJZCI6bnVsbCwiY29tcGFueVZPUyI6bnVsbH0.GwMYvckFHvFbhSi0NXpQDPiv9ZswUBAImN5bUipBla0"

bot = telebot.TeleBot(API_TOKEN)
user_points = {}
CURRENT_X_TOKEN = DEFAULT_TOKEN
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
    global CURRENT_X_TOKEN
    CURRENT_X_TOKEN = new_tk
    with open(TOKEN_FILE, 'w', encoding='utf-8') as f:
        f.write(new_tk)

def get_id_check_code(id17):
    factors = [7, 9, 10, 5, 8, 4, 2, 1, 6, 3, 7, 9, 10, 5, 8, 4, 2]
    rem_map = {0: '1', 1: '0', 2: 'X', 3: '9', 4: '8', 5: '7', 6: '6', 7: '5', 8: '4', 9: '3', 10: '2'}
    try:
        sum_val = sum(int(id17[i]) * factors[i] for i in range(17))
        return rem_map[sum_val % 11]
    except: return "X"

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
    return types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("⬅️ BACK", callback_data="back_to_main"))

def get_main_text(source, uid, pts):
    first_name = source.from_user.first_name if hasattr(source.from_user, 'first_name') else "User"
    username = f"@{source.from_user.username}" if hasattr(source.from_user, 'username') and source.from_user.username else "未设置"
    return (
        f"Admin[@aaSm68](https://t.me/aaSm68)\n\n"
        f"用户 ID: `{uid}`\n"
        f"用户名称: `{first_name}`\n"
        f"用户名: {username}\n"
        f"当前余额: `{pts:.2f}积分`\n\n"
        f"使用帮助可查看使用教程\n"
        f"在线充值可支持24小时\n"
        f"1 USDT = 1 积分"
    )

def get_ui_bar(done, total):
    percent = int(done / total * 100) if total > 0 else 0
    bar_len = 16
    filled = int(bar_len * done // total) if total > 0 else 0
    bar = "█" * filled + "░" * (bar_len - filled)
    return f"⌛ 开始核验...\n[{bar}] {done}/{total} {percent}%"

# ================= 3. 核验逻辑集成 =================

def single_verify_2ys(chat_id, name, id_card, uid):
    url = "https://api.xhmxb.com/wxma/moblie/wx/v1/realAuthToken"
    headers = {
        "Authorization": AUTH_BEARER,
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 18_7 like Mac OS X)",
        "Referer": "https://servicewechat.com/wxf5fd02d10dbb21d2/59/page-frame.html"
    }
    try:
        r = requests.post(url, headers=headers, json={"name": name, "idCardNo": id_card}, timeout=10)
        if r.status_code == 200 and r.json().get("success"):
            user_points[uid] -= 0.5; save_points()
            res = (f"姓名: **{name}**\n身份证: **{id_card}**\n结果: **二要素核验一致✅**\n\n"
                   f"已扣除 **0.5** 积分！\n当前积分余额：**{user_points[uid]:.2f}** 积分")
        else:
            res = f"姓名: **{name}**\n身份证: **{id_card}**\n结果: **二要素验证失败❌**"
    except: res = "❌ 接口请求失败"
    bot.send_message(chat_id, res, parse_mode='Markdown')

def run_batch_task(chat_id, msg_id, name, id_list, uid):
    headers = {"X-Token": CURRENT_X_TOKEN, "content-type": "application/json"}
    total, done = len(id_list), 0
    success_match, is_running = None, True
    lock = threading.Lock()

    def progress_monitor():
        nonlocal done, is_running
        while is_running:
            time.sleep(3)
            with lock: current_done = done
            try: bot.edit_message_text(chat_id=chat_id, message_id=msg_id, text=get_ui_bar(current_done, total))
            except: pass

    threading.Thread(target=progress_monitor, daemon=True).start()

    def verify(id_no):
        nonlocal done, success_match, is_running
        if not is_running: return
        try:
            payload = {"id_type": "id_card", "mobile": "15555555555", "id_no": id_no, "name": name}
            r = requests.post("https://wxxcx.cdcypw.cn/wechat/visitor/create", json=payload, headers=headers, timeout=5)
            if r.json().get("code") == 0:
                with lock:
                    if is_running:
                        user_points[uid] -= 2.5; save_points()
                        success_match = (f"✅ **核验成功！**\n\n**{name} {id_no}** 二要素核验一致✅\n\n"
                                        f"已扣除 **2.5** 积分！\n当前积分余额：**{user_points[uid]:.2f}** 积分")
                        is_running = False
        except: pass
        finally:
            with lock: done += 1

    with ThreadPoolExecutor(max_workers=10) as ex:
        ex.map(verify, id_list)
    
    is_running = False
    try: bot.delete_message(chat_id, msg_id)
    except: pass
    bot.send_message(chat_id, success_match if success_match else "❌ **未发现匹配结果**", parse_mode='Markdown')

# ================= 4. 指令与消息处理 =================

@bot.message_handler(commands=['admin'])
def admin_cmd(message):
    if message.from_user.id != ADMIN_ID: 
        bot.reply_to(message, "🤡你没有权限使用该指令…")
        return
    bot.send_message(message.chat.id, "👑 **管理员控制台**\n\n`/add 用户ID 分数` (充值)\n`/set_token` (更换批量Token)", parse_mode='Markdown')

@bot.message_handler(commands=['add'])
def add_points_cmd(message):
    if message.from_user.id != ADMIN_ID: 
        bot.reply_to(message, "🤡你没有权限使用该指令…")
        return
    try:
        parts = message.text.split()
        if len(parts) != 3: raise ValueError
        tid, amt = int(parts[1]), float(parts[2])
        user_points[tid] = user_points.get(tid, 0.0) + amt
        save_points()
        bot.reply_to(message, f"✅ 已充值！\n用户 ID: `{tid}`\n当前余额: `{user_points[tid]:.2f}`")
    except:
        bot.reply_to(message, "**使用格式错误！**\n请发送：`/add 用户ID 积分`", parse_mode='Markdown')

@bot.message_handler(commands=['set_token'])
def set_token_cmd(message):
    if message.from_user.id != ADMIN_ID: 
        bot.reply_to(message, "🤡你没有权限使用该指令…")
        return
    msg = bot.reply_to(message, "**请输入X-Token：**")
    bot.register_next_step_handler(msg, lambda m: [save_token(m.text.strip()), bot.send_message(m.chat.id, "✅ Token已更新")])

@bot.message_handler(commands=['start'])
def start_cmd(message):
    uid = message.from_user.id
    if uid not in user_points: user_points[uid] = 0.0
    bot.send_message(message.chat.id, get_main_text(message, uid, user_points[uid]), parse_mode='Markdown', reply_markup=get_main_markup())

@bot.message_handler(commands=['pl'])
def pl_cmd(message):
    if user_points.get(message.from_user.id, 0.0) < 2.5: return bot.reply_to(message, "积分不足 2.5！")
    user_states[message.chat.id] = {'step': 'v_name'}
    bot.send_message(message.chat.id, "请输入姓名：")

@bot.message_handler(commands=['bq'])
def bq_cmd(message):
    if user_points.get(message.from_user.id, 0.0) < 0.5: return bot.reply_to(message, "积分不足 0.5！")
    user_states[message.chat.id] = {'step': 'g_card'}
    bot.send_message(message.chat.id, "请输入身份证号（未知用x）：")

@bot.message_handler(commands=['2ys'])
def cmd_2ys(message):
    if user_points.get(message.from_user.id, 0.0) < 0.5: return bot.reply_to(message, "积分不足 0.5！")
    bot.send_message(message.chat.id, "请输入**姓名 身份证号**", parse_mode='Markdown')

@bot.message_handler(func=lambda m: True)
def handle_all(message):
    uid, chat_id, text = message.from_user.id, message.chat.id, message.text.strip()
    if text.startswith('/'): return 
    match_2ys = re.match(r'^([\u4e00-\u9fa5]{2,4})\s+(\d{17}[\dXx])$', text)
    if match_2ys:
        if user_points.get(uid, 0.0) < 0.5: return bot.reply_to(message, "积分不足 0.5！")
        return single_verify_2ys(chat_id, *match_2ys.groups(), uid)
    
    state = user_states.get(chat_id)
    if not state: return

    if state['step'] == 'v_name':
        user_states[chat_id].update({'step': 'v_ids', 'name': text})
        bot.send_message(chat_id, f"✅ 记录姓名：{text}\n请发送身份证列表：")
    elif state['step'] == 'v_ids':
        ids = [i for i in re.findall(r'\d{17}[\dXx]', text) if len(i)==18]
        if ids:
            m = bot.send_message(chat_id, get_ui_bar(0, len(ids)))
            threading.Thread(target=run_batch_task, args=(chat_id, m.message_id, state['name'], ids, uid)).start()
        del user_states[chat_id]
    elif state['step'] == 'g_card':
        user_states[chat_id].update({'step': 'g_sex', 'card': text.lower()})
        bot.send_message(chat_id, "请输入性别 (男/女):")
    elif state['step'] == 'g_sex':
        # 修复此处的语法逻辑，确保三元运算和列表推导式正确
        user_points[uid] -= 0.5; save_points()
        base_17 = state['card'][:17]
        char_sets = [list(ch) if ch != 'x' else list("0123456789") for ch in base_17]
        
        # 修正性别过滤逻辑
        if text == "男":
            char_sets[16] = [c for c in char_sets[16] if int(c) % 2 != 0]
        else:
            char_sets[16] = [c for c in char_sets[16] if int(c) % 2 == 0]
            
        ids = [s17 + get_id_check_code(s17) for s17 in ["".join(res) for res in itertools.product(*char_sets)]]
        generated_cache[uid] = ids
        
        # 写入文件并发送
        with open("result.txt", "w", encoding="utf-8") as f:
            f.write("\n".join(ids))
            
        markup = types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("立即核验 (2.5积分)", callback_data="start_verify_flow"))
        with open("result.txt", "rb") as f:
            bot.send_document(chat_id, f, caption=f"✅ 生成成功！共 {len(ids)} 个", reply_markup=markup)
        del user_states[chat_id]
    elif state['step'] == 'v_name_after_gen':
        if uid in generated_cache:
            m = bot.send_message(chat_id, get_ui_bar(0, len(generated_cache[uid])))
            threading.Thread(target=run_batch_task, args=(chat_id, m.message_id, text, generated_cache[uid], uid)).start()
        del user_states[chat_id]

@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    uid, pts = call.from_user.id, user_points.get(call.from_user.id, 0.0)
    if call.data == "view_help":
        help_text = (
            "🛠️️使用帮助\n"
            "发送 /pl 进行批量二要素查询\n"
            "每次查询扣除 2.5 积分\n"
            "——————————————————\n"
            "发送 /bq 进行补齐身份证查询\n"
            "每次补齐扣除 0.5 积分\n"
            "——————————————————\n"
            "发送 /2ys 进行单次二要素核验\n"
            "每次核验扣除 0.5 积分"
        )
        bot.edit_message_text(help_text, call.message.chat.id, call.message.message_id, reply_markup=get_help_markup())
    elif call.data == "view_pay":
        bot.edit_message_text("🛍️ 请选择充值方式：\n1 USDT = 1 积分", call.message.chat.id, call.message.message_id, reply_markup=get_pay_markup())
    elif call.data == "back_to_main":
        bot.edit_message_text(get_main_text(call, uid, pts), call.message.chat.id, call.message.message_id, parse_mode='Markdown', reply_markup=get_main_markup())
    elif call.data == "start_verify_flow":
        bot.send_message(call.message.chat.id, "请输入姓名:"); user_states[call.message.chat.id] = {'step': 'v_name_after_gen'}

if __name__ == '__main__':
    # 启用异常重连，防止 Railway 环境下网络波动导致进程结束
    bot.infinity_polling(timeout=10, long_polling_timeout=5)
