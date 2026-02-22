import telebot
import requests
import time
import re
import threading
import json
import os
import itertools
import binascii
import random
import concurrent.futures
import inspect  
import urllib.parse
import asyncio
import sms_list 
import sms_list_new
from sms_list import *
from Crypto.Cipher import DES3
from datetime import datetime
from telebot import types
from concurrent.futures import ThreadPoolExecutor
# 导入 Telethon 核心库
from telethon import TelegramClient, events

# 屏蔽 SSL 证书报警
from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

# ================= 1. 核心配置 =================
API_TOKEN = '8338893180:AAH-l_4m1-tweKyt92bliyk4fsPqoPQWzpU'
ADMIN_ID = 6649617045 
ADMIN_USERNAME = "@aaSm68"
POINTS_FILE = 'points.json'

# 二要素接口授权 Token
AUTH_BEARER = "bearer eyJhbGciOiJIUzI1NiJ9.eyJwaG9uZSI6IisxOTM3ODg4NDgyNiIsIm9wZW5JZCI6Im95NW8tNHk3Wnd0WGlOaTVHQ3V3YzVVNDZJYk0iLCJpZENhcmRObyI6IjM3MDQ4MTE5ODgwODIwMzUxNCIsInVzZXJOYW1lIjoi6ams5rCR5by6IiwibG9naW5UaW1lIjoxNzY5NDE1NjYxMTk0LCJhcHBJZCI6Ind4ZjVmZDAyZDEwZGJiMjFkMiIsImlzcmVhbG5hbWUiOnRydWUsInNhYXNVc2VySWQiOm51bGwsImNvbXBhbnlJZCI6bnVsbCwiY29tcGFueVZPUyI6bnVsbH0.GwMYvckFHvFbhSi0NXpQDPiv9ZswUBAImN5bUipBla0"

# --- 自动签到专用配置 ---
API_ID = 2040
API_HASH = "b18441a1ff607e10a989891a5462e627"
PHONE = '+243991464642'
SIGN_IN_BOTS = [
    {"name": "山东小纸条", "bot_username": "sdxhzbot", "command": "/qd"},
    {"name": "今日社工库", "bot_username": "jrsgk6_bot", "command": "/checkin"},
    {"name": "好望社工库", "bot_username": "haowangshegongkubot", "command": "/sign"},
    {"name": "优享", "bot_username": "youxs520_bot", "command": "/sign"},
    {"name": "云储", "bot_username": "yunchu_bot", "command": "/qd"},
    {"name": "mw社工库", "bot_username": "mwsgkbot", "command": "/qd"}
]
sign_in_status = {}

bot = telebot.TeleBot(API_TOKEN)
user_points = {}
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
    return pts

user_points = load_data()

def save_points():
    with open(POINTS_FILE, 'w') as f:
        json.dump({str(k): v for k, v in user_points.items()}, f)

# ================= 2. 自动签到引擎 (异步) =================

async def sign_in_engine():
    """Telethon 异步执行器"""
    # 优先加载 my_account.session
    client = TelegramClient("my_account", API_ID, API_HASH)
    await client.connect()
    
    if not await client.is_user_authorized():
        print("❌ 签到模块：账号未授权，请检查 session 文件。")
        return

    print("✅ 自动签到引擎已就绪...")
    while True:
        try:
            now = datetime.now()
            if now.hour in [12, 0]:
                for target in SIGN_IN_BOTS:
                    if target["bot_username"] not in sign_in_status or \
                       (time.time() - sign_in_status[target["bot_username"]].get("last", 0) > 3600):
                        await client.send_message(target["bot_username"], target["command"])
                        sign_in_status[target["bot_username"]] = {"last": time.time(), "success": True}
                        print(f"执行签到: {target['name']}")
                        await asyncio.sleep(5)
            await asyncio.sleep(60)
        except Exception as e:
            print(f"签到任务异常: {e}")
            await asyncio.sleep(30)

def start_async_loop():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(sign_in_engine())

# ================= 3. 原有业务逻辑 (保持不动) =================

def cp_query_logic(chat_id, car_no, uid):
    url = f"http://zgzapi.idc.cn.com/车档.php?key=体验卡&cph={urllib.parse.quote(car_no)}"
    try:
        response = requests.get(url, timeout=15)
        response.encoding = 'utf-8'
        raw_res = response.text.strip()
        if raw_res and "未找到" not in raw_res and "错误" not in raw_res:
            user_points[uid] -= 2.5; save_points()
            message = (f"车牌查询结果:\n\n车牌号：{car_no}\n详细信息：\n{raw_res}\n\n已扣除 2.5 积分！\n当前余额: {user_points[uid]:.2f}")
        else:
            message = (f"车牌查询结果:\n\n未匹配到有效车档信息。\n\n查询无结果，未扣除积分。\n当前余额: {user_points[uid]:.2f}")
        bot.send_message(chat_id, message)
    except Exception as e: bot.send_message(chat_id, f"⚠️ 车档接口请求失败: {str(e)}")

def xiaowunb_query_logic(chat_id, id_number, uid):
    base_url = "http://xiaowunb.top/cyh.php"
    params = {"sfz": id_number}
    try:
        response = requests.get(base_url, params=params, timeout=10); response.encoding = 'utf-8'
        raw_text = response.text.strip()
        phones = re.findall(r'1[3-9]\d{9}', raw_text)
        if phones:
            user_points[uid] -= 1.5; save_points()
            unique_phones = list(dict.fromkeys(phones))
            phone_list_str = "".join([f"{idx}、{p}\n" for idx, p in enumerate(unique_phones, 1)])
            result_body = f"匹配到 {len(unique_phones)} 个有效手机号:\n{phone_list_str}"
            cost_str = f"已扣除 1.5 积分！"
        else: result_body = "未匹配到有效手机号\n"; cost_str = "查询无结果，未扣除积分。"
        bot.send_message(chat_id, f"身份证查询结果:\n\n{result_body}\n{cost_str}\n当前余额: {user_points[uid]:.2f}")
    except Exception as e: bot.send_message(chat_id, f"❌ 接口请求失败: {e}")

def query_3ys_logic(chat_id, name, id_card, phone, uid):
    url = "http://xiaowunb.top/3ys.php"
    params = {"name": name, "sfz": id_card, "sjh": phone}
    try:
        response = requests.get(url, params=params, timeout=15); response.encoding = 'utf-8'
        user_points[uid] -= 0.05; save_points()
        clean_res = re.sub(r'小无 API.*?官方客服:@\w+', '', response.text.strip(), flags=re.DOTALL).strip()
        res_status = "三要素核验成功✅" if ("成功" in clean_res or "一致" in clean_res) else "三要素核验失败❌"
        bot.send_message(chat_id, f"名字：{name}\n手机号：{phone}\n身份证：{id_card}\n结果：{res_status}\n\n已扣除 0.05 积分！\n当前积分余额：{user_points[uid]:.2f}")
    except Exception as e: bot.send_message(chat_id, f"⚠️ 系统异常: {str(e)}")

def single_verify_2ys(chat_id, name, id_card, uid):
    url = "https://api.xhmxb.com/wxma/moblie/wx/v1/realAuthToken"
    headers = {"Authorization": AUTH_BEARER, "Content-Type": "application/json", "User-Agent": "Mozilla/5.0"}
    try:
        r = requests.post(url, headers=headers, json={"name": name, "idCardNo": id_card}, timeout=10)
        user_points[uid] -= 0.01; save_points()
        res_type = "二要素核验一致✅" if r.json().get("success") else f"二要素验证失败 ❌"
        bot.send_message(chat_id, f"姓名: **{name}**\n身份证: **{id_card}**\n结果: **{res_type}**\n\n已扣除 **0.01** 积分！\n当前余额：**{user_points[uid]:.2f}**", parse_mode='Markdown')
    except Exception as e: bot.send_message(chat_id, f"❌ 接口请求失败: {str(e)}")

# ================= 4. UI与菜单逻辑 =================

def get_id_check_code(id17):
    factors = [7, 9, 10, 5, 8, 4, 2, 1, 6, 3, 7, 9, 10, 5, 8, 4, 2]
    rem_map = {0: '1', 1: '0', 2: 'X', 3: '9', 4: '8', 5: '7', 6: '6', 7: '5', 8: '4', 9: '3', 10: '2'}
    try: return rem_map[sum(int(id17[i]) * factors[i] for i in range(17)) % 11]
    except: return "X"

def get_main_markup():
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(types.InlineKeyboardButton("使用帮助", callback_data="view_help"), types.InlineKeyboardButton("在线充值", callback_data="view_pay"))
    return markup

def get_pay_markup():
    admin_url = f"https://t.me/{ADMIN_USERNAME.replace('@', '')}"
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(types.InlineKeyboardButton("USDT 充值", url=admin_url), types.InlineKeyboardButton("OkPay 充值", url=admin_url), types.InlineKeyboardButton("RMB 充值", url=admin_url), types.InlineKeyboardButton("🔙", callback_data="back_to_main"))
    return markup

def get_help_markup():
    return types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("🔙", callback_data="back_to_main"))

def get_main_text(source, uid, pts):
    first_name = source.from_user.first_name if hasattr(source.from_user, 'first_name') else "User"
    username = f"@{source.from_user.username}" if hasattr(source.from_user, 'username') and source.from_user.username else "未设置"
    return (f"Admin@铭\n\n用户 ID: `{uid}`\n用户名称: `{first_name}`\n用户名: {username}\n当前余额: `{pts:.2f}积分`\n\n使用帮助可查看使用教程\n在线充值可支持24小时\n1 USDT = 1 积分")

# ================= 5. 短信测压与指令处理 (保持不动) =================

def get_all_senders():
    all_funcs = []
    excludes = ['generate_random_user_agent', 'replace_phone_in_data', 'platform_request_worker', 'send_minute_request', 'get_current_timestamp']
    for name, obj in inspect.getmembers(sms_list):
        if inspect.isfunction(obj) and name not in excludes:
            try:
                sig = inspect.signature(obj)
                if len(sig.parameters) >= 1: all_funcs.append(obj)
            except: pass
    if hasattr(sms_list_new, 'NEW_PLATFORMS'):
        for name, func in sms_list_new.NEW_PLATFORMS:
            if func not in all_funcs: all_funcs.append(func)
    return all_funcs

@bot.message_handler(commands=['sms'])
def sms_bomb_cmd(message):
    uid = message.from_user.id
    if user_points.get(uid, 0.0) < 3.5: return bot.reply_to(message, "积分不足(3.5)")
    parts = message.text.split()
    if len(parts) < 2: return bot.reply_to(message, "用法: `/sms 手机号`")
    target = parts[1]
    if not (len(target) == 11 and target.isdigit()): return bot.reply_to(message, "⚠️ 手机号格式错误")
    all_funcs = get_all_senders()
    bot.reply_to(message, f"🎯 **接口装载：{len(all_funcs)}个**\n正在轰炸 `{target}`...", parse_mode='Markdown')
    user_points[uid] -= 3.5; save_points()
    def do_bomb():
        random.shuffle(all_funcs)
        with concurrent.futures.ThreadPoolExecutor(max_workers=100) as executor:
            for func in all_funcs: executor.submit(func, target)
        bot.send_message(message.chat.id, f"✅ 目标 `{target}` 任务执行完毕")
    threading.Thread(target=do_bomb).start()

# ================= 6. /ml 自动签到管理 =================

@bot.message_handler(commands=['ml'])
def sign_manage_menu(message):
    if message.from_user.id != ADMIN_ID: return
    text = "🤖 **自动签到管理系统**\n\n📋 **任务列表:**\n"
    for i, b in enumerate(SIGN_IN_BOTS, 1):
        status = "✅" if sign_in_status.get(b['bot_username'], {}).get("success") else "⏳"
        text += f"{i}. {b['name']} (@{b['bot_username']}) {status}\n"
    text += "\n✨ **管理指令:**\n/list - 详细名单\n/add_bot 名称 @用户名 指令\n/del_bot @用户名\n/sign_now - 立即执行签到"
    bot.reply_to(message, text, parse_mode='Markdown')

@bot.message_handler(commands=['add_bot'])
def add_sign_bot(message):
    if message.from_user.id != ADMIN_ID: return
    parts = message.text.split(maxsplit=3)
    if len(parts) < 4: return bot.reply_to(message, "用法: /add_bot 名称 @用户名 指令")
    SIGN_IN_BOTS.append({"name": parts[1], "bot_username": parts[2].replace("@",""), "command": parts[3]})
    bot.reply_to(message, f"✅ 已添加: {parts[1]}")

@bot.message_handler(commands=['del_bot'])
def del_sign_bot(message):
    if message.from_user.id != ADMIN_ID: return
    parts = message.text.split()
    if len(parts) < 2: return bot.reply_to(message, "用法: /del_bot @用户名")
    target = parts[1].replace("@", "")
    global SIGN_IN_BOTS
    SIGN_IN_BOTS = [b for b in SIGN_IN_BOTS if b['bot_username'] != target]
    bot.reply_to(message, f"🗑️ 已移除: @{target}")

# ================= 7. 指令分发逻辑 =================

@bot.message_handler(commands=['cyh', '3ys', 'admin', 'add', 'start', 'bq', '2ys', 'cp'])
def handle_commands(message):
    uid, chat_id = message.from_user.id, message.chat.id
    cmd = message.text.split()[0][1:]
    if cmd in ['add', 'admin'] and uid != ADMIN_ID: return bot.reply_to(message, "🤡你没有权限使用该指令…")
    if cmd == 'start':
        if uid not in user_points: user_points[uid] = 0.0
        bot.send_message(chat_id, get_main_text(message, uid, user_points[uid]), parse_mode='Markdown', reply_markup=get_main_markup())
    elif cmd == 'add' and uid == ADMIN_ID:
        try:
            p = message.text.split(); tid, amt = int(p[1]), float(p[2])
            user_points[tid] = user_points.get(tid, 0.0) + amt; save_points()
            bot.reply_to(message, f"✅ 已充值！当前余额: `{user_points[tid]:.2f}`")
        except: pass
    elif cmd == 'cyh':
        if user_points.get(uid, 0.0) < 1.5: return bot.reply_to(message, "积分不足！")
        user_states[chat_id] = {'step': 'cyh_id'}; bot.send_message(chat_id, "请输入要查询的身份证号：")
    elif cmd == '3ys':
        if user_points.get(uid, 0.0) < 0.05: return bot.reply_to(message, "积分不足！")
        user_states[chat_id] = {'step': 'v_3ys'}; bot.send_message(chat_id, "请输入姓名 手机号 身份证")
    elif cmd == 'bq':
        if user_points.get(uid, 0.0) < 0.1: return bot.reply_to(message, "积分不足！")
        user_states[chat_id] = {'step': 'g_card'}; bot.send_message(chat_id, "请输入身份证号（未知用x）：")
    elif cmd == '2ys':
        if user_points.get(uid, 0.0) < 0.01: return bot.reply_to(message, "积分不足！")
        user_states[chat_id] = {'step': 'v_2ys'}; bot.send_message(chat_id, "请输入姓名 身份证")
    elif cmd == 'cp':
        if user_points.get(uid, 0.0) < 2.5: return bot.reply_to(message, "积分不足(2.5)")
        user_states[chat_id] = {'step': 'v_cp'}; bot.send_message(chat_id, "请输入要查询的车牌号：")

@bot.message_handler(func=lambda m: True)
def handle_all(message):
    uid, chat_id, text = message.from_user.id, message.chat.id, message.text.strip()
    if text.startswith('/'): return 
    
    if chat_id not in user_states or not user_states[chat_id].get('step'):
        if re.match(r'^[京津沪渝冀豫云辽黑湖南皖鲁新苏浙赣鄂桂甘晋蒙陕吉闽贵粤青藏川宁琼]{1}[A-Z]{1}[A-Z0-9]{5,6}$', text.upper()):
            if user_points.get(uid, 0.0) < 2.5: return bot.reply_to(message, "❌ 积分不足")
            return cp_query_logic(chat_id, text.upper(), uid)
        parts = re.split(r'[,，\s\n]+', text)
        if len(parts) >= 3:
            n, p, i = None, None, None
            for x in parts:
                if not n and re.match(r'^[\u4e00-\u9fa5]{2,4}$', x): n = x
                elif not p and re.match(r'^1[3-9]\d{9}$', x): p = x
                elif not i and re.match(r'^[\dXx]{15}$|^[\dXx]{18}$', x): i = x.upper()
            if n and p and i:
                if user_points.get(uid, 0.0) < 0.05: return bot.reply_to(message, "❌ 积分不足")
                return query_3ys_logic(chat_id, n, i, p, uid)
        if len(parts) == 2:
            n, i = None, None
            for x in parts:
                if not n and re.match(r'^[\u4e00-\u9fa5]{2,4}$', x): n = x
                elif not i and re.match(r'^[\dXx]{15}$|^[\dXx]{18}$', x): i = x.upper()
            if n and i:
                if user_points.get(uid, 0.0) < 0.01: return bot.reply_to(message, "❌ 积分不足")
                return single_verify_2ys(chat_id, n, i, uid)
        if re.match(r'^\d{17}[\dXx]$|^\d{15}$', text):
            if user_points.get(uid, 0.0) < 1.5: return bot.reply_to(message, "❌ 积分不足")
            return xiaowunb_query_logic(chat_id, text, uid)

    state = user_states.get(chat_id)
    if not state: return
    step = state['step']
    if step == 'v_cp': del user_states[chat_id]; cp_query_logic(chat_id, text.upper(), uid)
    elif step == 'cyh_id': del user_states[chat_id]; xiaowunb_query_logic(chat_id, text, uid)
    elif step == 'g_card': user_states[chat_id].update({'step': 'g_sex', 'card': text.lower()}); bot.send_message(chat_id, "请输入性别 (男/女):")
    elif step == 'g_sex':
        user_points[uid] -= 0.1; save_points(); base_17 = state['card'][:17]
        char_sets = [list(ch) if ch != 'x' else list("0123456789") for ch in base_17]
        if text == "男": char_sets[16] = [c for c in char_sets[16] if int(c) % 2 != 0]
        else: char_sets[16] = [c for c in char_sets[16] if int(c) % 2 == 0]
        ids = [s17 + get_id_check_code(s17) for s17 in ["".join(res) for res in itertools.product(*char_sets)]]
        with open("铭.txt", "w", encoding="utf-8") as f: f.write("\n".join(ids))
        with open("铭.txt", "rb") as f: bot.send_document(chat_id, f, caption=f"✅ 生成成功！")
        del user_states[chat_id]

# ================= 8. 回调处理与启动 =================

@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    uid, pts = call.from_user.id, user_points.get(call.from_user.id, 0.0)
    if call.data == "view_help":
        # 恢复完整详细的帮助文本
        help_text = (
            "🛠️️使用帮助\n"
            "短信测压\n"
            "发送 /sms 手机号\n"
            "每次消耗 3.5 积分\n"
            "——————————————————\n"
            "补齐身份证\n"
            "发送 /bq 进行操作\n"
            "每次补齐扣除 0.1 积分\n"
            "——————————————————\n"
            "名字-身份证核验（企业级）\n"
            "全天24h秒出 毫秒级响应\n"
            "发送 /2ys 进行核验\n"
            "每次核验扣除 0.01 积分\n"
            "——————————————————\n"
            "名字-手机号-身份证核验（企业级）\n"
            "全天24h秒出 毫秒级响应\n"
            "发送 /3ys 进行核验\n"
            "每次核验扣除 0.05 积分\n"
            "——————————————————\n"
            "车牌号查询\n"
            "发送 /cp 进行查询\n"
            "全天24h秒出 假1赔10000\n"
            "每次查询扣除 2.5 积分 空不扣除积分\n"
            "——————————————————\n"
            "常用号查询\n"
            "发送 /cyh 进行查询\n"
            "全天24h秒出 假1赔10000\n"
            "每次查询扣除 1.5 积分 空不扣除积分"
        )
        bot.edit_message_text(help_text, call.message.chat.id, call.message.message_id, reply_markup=get_help_markup())
    elif call.data == "view_pay":
        bot.edit_message_text("🛍️ 请选择充值方式：\n1 USDT = 1 积分", call.message.chat.id, call.message.message_id, reply_markup=get_pay_markup())
    elif call.data == "back_to_main":
        bot.edit_message_text(get_main_text(call, uid, pts), call.message.chat.id, call.message.message_id, parse_mode='Markdown', reply_markup=get_main_markup())

if __name__ == '__main__':
    threading.Thread(target=start_async_loop, daemon=True).start()
    print("Bot 正在运行 (已加载自动签到模块及完整帮助)...")
    bot.infinity_polling(timeout=10, long_polling_timeout=5)
