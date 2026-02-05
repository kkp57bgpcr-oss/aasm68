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

# 新接口的 Authorization (建议后期也放入 token.txt 管理)
AUTH_BEARER = "bearer eyJhbGciOiJIUzI1NiJ9.eyJwaG9uZSI6IisxOTM3ODg4NDgyNiIsIm9wZW5JZCI6Im95NW8tNHk3Wnd0WGlOaTVHQ3V3YzVVNDZJYk0iLCJpZENhcmRObyI6IjM3MDQ4MTE5ODgwODIwMzUxNCIsInVzZXJOYW1lIjoi6ams5rCR5by6IiwibG9naW5UaW1lIjoxNzY5NDE1NjYxMTk0LCJhcHBJZCI6Ind4ZjVmZDAyZDEwZGJiMjFkMiIsImlzcmVhbG5hbWUiOnRydWUsInNhYXNVc2VySWQiOm51bGwsImNvbXBhbnlJZCI6bnVsbCwiY29tcGFueVZPUyI6bnVsbH0.GwMYvckFHvFbhSi0NXpQDPiv9ZswUBAImN5bUipBla0"

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

# --- 身份证校验码算法 ---
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

def get_main_text(source, uid, pts):
    return (
        f"Welcome to use！\n\n"
        f"用户 ID: `{uid}`\n"
        f"当前余额: `{pts:.2f}积分`\n\n"
        f"使用帮助可查看使用教程\n"
        f"在线充值可支持24小时"
    )

# ================= 3. 核心核验逻辑 =================

# 接口 B: 单次二要素核验逻辑
def single_verify_2ys(chat_id, name, id_card, uid):
    url = "https://api.xhmxb.com/wxma/moblie/wx/v1/realAuthToken"
    headers = {
        "Authorization": AUTH_BEARER,
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 18_7 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 MicroMessenger/8.0.68(0x1800442a)",
        "Referer": "https://servicewechat.com/wxf5fd02d10dbb21d2/59/page-frame.html"
    }
    payload = {"name": name, "idCardNo": id_card}
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=10)
        if response.status_code == 200:
            result = response.json()
            if result.get("code") == 0 and result.get("success") is True:
                user_points[uid] -= 0.5
                save_points()
                res_text = (
                    f"姓名: **{name}**\n"
                    f"身份证: **{id_card}**\n"
                    f"结果: **二要素核验一致✅**\n\n"
                    f"已扣除 **0.5** 积分！\n"
                    f"当前积分余额：**{user_points[uid]:.2f}** 积分"
                )
            else:
                res_text = f"姓名: **{name}**\n身份证: **{id_card}**\n结果: **二要素验证失败❌**"
        elif response.status_code == 401:
            res_text = "⚠️ 接口授权失效，请联系管理员更新 Token。"
        else:
            res_text = f"⚠️ 请求异常，错误码: {response.status_code}"
    except:
        res_text = "❌ 网络连接失败，请稍后再试。"
    
    bot.send_message(chat_id, res_text, parse_mode='Markdown')

# 接口 A: 批量核验逻辑 (代码保持不变)
def run_batch_task(chat_id, msg_id, name, id_list, uid):
    headers = {"X-Token": CURRENT_X_TOKEN, "content-type": "application/json"}
    total, done = len(id_list), 0
    success_match, is_running, stop_signal = None, True, False

    def verify(id_no):
        nonlocal done, is_running, stop_signal, success_match
        if stop_signal: return
        try:
            payload = {"id_type": "id_card", "mobile": "15555555555", "id_no": id_no, "name": name}
            r = requests.post("https://wxxcx.cdcypw.cn/wechat/visitor/create", json=payload, headers=headers, timeout=5)
            if r.json().get("code") == 0:
                user_points[uid] -= 2.5
                save_points()
                success_match = (
                    f"✅ **核验成功！**\n\n"
                    f"**{name} {id_no}** 二要素核验一致✅\n\n"
                    f"已扣除 **2.5** 积分！\n"
                    f"当前积分余额：**{user_points[uid]:.2f}** 积分"
                )
                stop_signal, is_running = True, False
        except: pass
        finally: done += 1

    with ThreadPoolExecutor(max_workers=10) as executor:
        executor.map(verify, id_list)
    
    is_running = False
    try: bot.delete_message(chat_id, msg_id)
    except: pass
    bot.send_message(chat_id, success_match if success_match else "❌ **核验完成，未发现匹配结果。**", parse_mode='Markdown')

# ================= 4. 指令与消息处理 =================

@bot.message_handler(commands=['2ys'])
def cmd_2ys(message):
    if user_points.get(message.from_user.id, 0.0) < 0.5:
        return bot.reply_to(message, "积分不足 0.5，请先充值！")
    bot.send_message(message.chat.id, "💡 请输入：**姓名 身份证号**\n(例如：`刘思阳 130282200806250051`)", parse_mode='Markdown')

@bot.message_handler(commands=['pl'])
def pl_cmd(message):
    if user_points.get(message.from_user.id, 0.0) < 2.5: return bot.reply_to(message, "积分不足！")
    user_states[message.chat.id] = {'step': 'v_name'}
    bot.send_message(message.chat.id, "请输入姓名：")

@bot.message_handler(commands=['bq'])
def bq_cmd(message):
    if user_points.get(message.from_user.id, 0.0) < 0.5: return bot.reply_to(message, "积分不足！")
    user_states[message.chat.id] = {'step': 'g_card'}
    bot.send_message(message.chat.id, "请输入身份证号（未知用x）：")

@bot.message_handler(commands=['start'])
def start_cmd(message):
    uid = message.from_user.id
    if uid not in user_points: user_points[uid] = 0.0
    save_points()
    bot.send_message(message.chat.id, get_main_text(message, uid, user_points[uid]), 
                     parse_mode='Markdown', reply_markup=get_main_markup())

@bot.message_handler(func=lambda m: True)
def handle_all(message):
    uid, chat_id, text = message.from_user.id, message.chat.id, message.text.strip()
    
    # 1. 自动识别单次核验格式：姓名 身份证
    match_2ys = re.match(r'^([\u4e00-\u9fa5]{2,4})\s+(\d{17}[\dXx])$', text)
    if match_2ys:
        if user_points.get(uid, 0.0) < 0.5:
            return bot.reply_to(message, "积分不足 0.5！")
        name, id_card = match_2ys.groups()
        return single_verify_2ys(chat_id, name, id_card, uid)

    # 2. 状态机逻辑
    state = user_states.get(chat_id)
    if not state or text.startswith('/'): return

    if state['step'] == 'v_name':
        user_states[chat_id].update({'step': 'v_ids', 'name': text})
        bot.send_message(chat_id, f"✅ 姓名：{text}\n请发送身份证列表：")
    elif state['step'] == 'v_ids':
        ids = [i for i in re.findall(r'\d{17}[\dXx]', text) if len(i)==18]
        if ids:
            msg = bot.send_message(chat_id, "⌛ 正在批量核验...")
            threading.Thread(target=run_batch_task, args=(chat_id, msg.message_id, state['name'], ids, uid)).start()
        del user_states[chat_id]
    elif state['step'] == 'g_card':
        user_states[chat_id].update({'step': 'g_sex', 'card': text.lower()})
        bot.send_message(chat_id, "请输入性别 (男/女):")
    elif state['step'] == 'g_sex':
        user_points[uid] -= 0.5; save_points()
        base_17 = state['card'][:17]
        char_sets = [list(ch) if ch != 'x' else list("0123456789") for ch in base_17]
        if text == "男": char_sets[16] = [c for c in char_sets[16] if int(c)%2!=0]
        else: char_sets[16] = [c for c in char_sets[16] if int(c)%2==0]
        valid_ids = [s17 + get_id_check_code(s17) for s17 in ["".join(res) for res in itertools.product(*char_sets)]]
        generated_cache[uid] = valid_ids
        with open("铭.txt", "w") as f: f.write("\n".join(valid_ids))
        markup = types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("立即核验 (2.5积分)", callback_data="start_verify_flow"))
        bot.send_document(chat_id, open("铭.txt", "rb"), caption=f"✅ 生成成功！共 {len(valid_ids)} 个", reply_markup=markup)
        del user_states[chat_id]
    elif state['step'] == 'v_name_after_gen':
        if uid in generated_cache:
            msg = bot.send_message(chat_id, "⌛ 正在核验生成列表...")
            threading.Thread(target=run_batch_task, args=(chat_id, msg.message_id, text, generated_cache[uid], uid)).start()
        del user_states[chat_id]

@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    if call.data == "start_verify_flow":
        bot.send_message(call.message.chat.id, "请输入姓名:")
        user_states[call.message.chat.id] = {'step': 'v_name_after_gen'}
    # ... 其他回调逻辑省略，与之前一致 ...

if __name__ == '__main__':
    bot.infinity_polling()
