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
from telethon import TelegramClient, events, errors

# 屏蔽 SSL 证书报警
from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

# ================= 1. 核心配置 =================
API_TOKEN = '8338893180:AAH-l_4m1-tweKyt92bliyk4fsPqoPQWzpU'
ADMIN_ID = 6649617045 
ADMIN_USERNAME = "@aaSm68"
POINTS_FILE = 'points.json'
AUTH_BEARER = "bearer eyJhbGciOiJIUzI1NiJ9.eyJwaG9uZSI6IisxOTM3ODg4NDgyNiIsIm9wZW5JZCI6Im95NW8tNHk3Wnd0WGlOaTVHQ3V3YzVVNDZJYk0iLCJpZENhcmRObyI6IjM3MDQ4MTE5ODgwODIwMzUxNCIsInVzZXJOYW1lIjoi6ams5rCR5by6IiwibG9naW5UaW1lIjoxNzY5NDE1NjYxMTk0LCJhcHBJZCI6Ind4ZjVmZDAyZDEwZGJiMjFkMiIsImlzcmVhbG5hbWUiOnRydWUsInNhYXNVc2VySWQiOm51bGwsImNvbXBhbnlJZCI6bnVsbCwiY29tcGFueVZPUyI6bnVsbH0.GwMYvckFHvFbhSi0NXpQDPiv9ZswUBAImN5bUipBla0"

# --- 自动签到配置 ---
API_ID = 2040
API_HASH = "b18441a1ff607e10a989891a5462e627"
SIGN_IN_BOTS = [
    {"name": "山东小纸条", "bot_username": "sdxhzbot", "command": "/qd"},
    {"name": "今日社工库", "bot_username": "jrsgk6_bot", "command": "/checkin"},
    {"name": "好望社工库", "bot_username": "haowangshegongkubot", "command": "/sign"},
    {"name": "优享", "bot_username": "youxs520_bot", "command": "/sign"},
    {"name": "云储", "bot_username": "yunchu_bot", "command": "/qd"},
    {"name": "mw社工库", "bot_username": "mwsgkbot", "command": "/qd"}
]
sign_in_status = {}
client = None # Telethon Client 实例

bot = telebot.TeleBot(API_TOKEN)
user_points = {}
user_states = {}

# --- 数据持久化 ---
def load_data():
    if os.path.exists(POINTS_FILE):
        try:
            with open(POINTS_FILE, 'r') as f:
                data = json.load(f)
                return {int(k): float(v) for k, v in data.items()}
        except: pass
    return {}

user_points = load_data()

def save_points():
    with open(POINTS_FILE, 'w') as f:
        json.dump({str(k): v for k, v in user_points.items()}, f)

# ================= 2. 自动签到与登录逻辑 =================

async def init_client():
    global client
    client = TelegramClient("my_account", API_ID, API_HASH)
    await client.connect()

async def sign_in_loop():
    """后台定时签到循环"""
    await init_client()
    print("✅ 自动签到引擎已启动...")
    while True:
        try:
            if await client.is_user_authorized():
                now = datetime.now()
                if now.hour in [0, 12]: # 每天0点和12点
                    for target in SIGN_IN_BOTS:
                        uname = target["bot_username"].replace("@","")
                        if uname not in sign_in_status or (time.time() - sign_in_status[uname].get("last", 0) > 3600):
                            await client.send_message(uname, target["command"])
                            sign_in_status[uname] = {"last": time.time(), "success": True}
                            await asyncio.sleep(5)
            await asyncio.sleep(60)
        except Exception as e:
            await asyncio.sleep(30)

# ================= 3. 原有业务逻辑 (车牌/核验/短信) =================

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

# ================= 4. 控制台 UI 与 登录系统 =================

@bot.message_handler(commands=['ml'])
def sign_control_menu(message):
    if message.from_user.id != ADMIN_ID: return
    menu = (
        "🤖 **控制命令:**\n\n"
        "📋 **状态查询:**\n"
        "/status - 查看状态\n"
        "/list - 查看签到机器人列表\n\n"
        "✨ **签到控制:**\n"
        "/sign_now - 立即签到一次\n"
        "/add_bot 名称 @用户名 命令 - 添加签到机器人\n"
        "/del_bot @用户名 - 删除签到机器人\n\n"
        "📝 **手动消息:**\n"
        "/send @用户名 消息 - 发送消息\n\n"
        "🔑 **账号登录:**\n"
        "/login 手机号 - 开始登录流程\n\n"
        "🔧 **其他:**\n"
        "/help - 查看帮助"
    )
    bot.reply_to(message, menu, parse_mode='Markdown')

# --- 登录逻辑 ---
@bot.message_handler(commands=['login'])
def login_start(message):
    if message.from_user.id != ADMIN_ID: return
    parts = message.text.split()
    if len(parts) < 2: return bot.reply_to(message, "用法: `/login +86138xxxx`", parse_mode='Markdown')
    phone = parts[1]
    
    async def do_login():
        await client.connect()
        sent = await client.send_code_request(phone)
        user_states[message.chat.id] = {'step': 'wait_code', 'phone': phone, 'phone_code_hash': sent.phone_code_hash}
        bot.send_message(message.chat.id, "📩 验证码已发送，请输入收到的 5 位验证码：")
    
    asyncio.run_coroutine_threadsafe(do_login(), loop)

@bot.message_handler(commands=['status'])
def status_check(message):
    if message.from_user.id != ADMIN_ID: return
    
    async def check():
        auth = await client.is_user_authorized()
        status = "✅ 已登录" if auth else "❌ 未登录"
        bot.reply_to(message, f"📊 **当前系统状态:**\n账号状态: {status}\n待执行机器人: {len(SIGN_IN_BOTS)} 个", parse_mode='Markdown')
    
    asyncio.run_coroutine_threadsafe(check(), loop)

@bot.message_handler(commands=['list'])
def list_bots(message):
    if message.from_user.id != ADMIN_ID: return
    res = "📋 **签到机器人列表:**\n"
    for i, b in enumerate(SIGN_IN_BOTS, 1):
        res += f"{i}. {b['name']} (@{b['bot_username']}) -> `{b['command']}`\n"
    bot.reply_to(message, res, parse_mode='Markdown')

@bot.message_handler(commands=['sign_now'])
def sign_now(message):
    if message.from_user.id != ADMIN_ID: return
    
    async def run():
        if not await client.is_user_authorized():
            return bot.reply_to(message, "❌ 请先使用 /login 登录账号")
        bot.send_message(message.chat.id, "🔄 正在尝试给所有机器人发送签到指令...")
        for target in SIGN_IN_BOTS:
            await client.send_message(target['bot_username'], target['command'])
            await asyncio.sleep(2)
        bot.send_message(message.chat.id, "✅ 手动触发任务完成")
        
    asyncio.run_coroutine_threadsafe(run(), loop)

@bot.message_handler(commands=['send'])
def manual_send(message):
    if message.from_user.id != ADMIN_ID: return
    parts = message.text.split(maxsplit=2)
    if len(parts) < 3: return bot.reply_to(message, "用法: `/send @用户名 消息`", parse_mode='Markdown')
    target, text = parts[1].replace("@",""), parts[2]
    
    async def send():
        await client.send_message(target, text)
        bot.reply_to(message, f"📤 已成功发送消息至 @{target}")
        
    asyncio.run_coroutine_threadsafe(send(), loop)

@bot.message_handler(commands=['add_bot'])
def add_bot(message):
    if message.from_user.id != ADMIN_ID: return
    parts = message.text.split(maxsplit=3)
    if len(parts) < 4: return bot.reply_to(message, "用法: `/add_bot 名称 @用户名 命令`", parse_mode='Markdown')
    SIGN_IN_BOTS.append({"name": parts[1], "bot_username": parts[2].replace("@",""), "command": parts[3]})
    bot.reply_to(message, f"✅ 已添加签到任务: {parts[1]}")

@bot.message_handler(commands=['del_bot'])
def del_bot(message):
    if message.from_user.id != ADMIN_ID: return
    target = message.text.split()[-1].replace("@","")
    global SIGN_IN_BOTS
    SIGN_IN_BOTS = [b for b in SIGN_IN_BOTS if b['bot_username'] != target]
    bot.reply_to(message, f"🗑️ 已删除机器人: @{target}")

# ================= 5. 指令分发逻辑 (原有功能) =================

@bot.message_handler(commands=['start', 'help', 'sms', 'cyh', '3ys', '2ys', 'cp', 'bq'])
def handle_old_commands(message):
    uid, chat_id = message.from_user.id, message.chat.id
    cmd = message.text.split()[0][1:]
    
    if cmd == 'start':
        if uid not in user_points: user_points[uid] = 0.0
        bot.send_message(chat_id, get_main_text(message, uid, user_points[uid]), parse_mode='Markdown', reply_markup=get_main_markup())
    elif cmd == 'help':
        # 引用你要求的完整帮助文本
        help_text = (
            "🛠️️使用帮助\n"
            "短信测压\n发送 /sms 手机号\n每次消耗 3.5 积分\n"
            "——————————————————\n"
            "补齐身份证\n发送 /bq 进行操作\n每次补齐扣除 0.1 积分\n"
            "——————————————————\n"
            "名字-身份证核验（企业级）\n全天24h秒出 毫秒级响应\n发送 /2ys 进行核验\n每次核验扣除 0.01 积分\n"
            "——————————————————\n"
            "名字-手机号-身份证核验（企业级）\n全天24h秒出 毫秒级响应\n发送 /3ys 进行核验\n每次核验扣除 0.05 积分\n"
            "——————————————————\n"
            "车牌号查询\n发送 /cp 进行查询\n全天24h秒出 假1赔10000\n每次查询扣除 2.5 积分 空不扣除积分\n"
            "——————————————————\n"
            "常用号查询\n发送 /cyh 进行查询\n全天24h秒出 假1赔10000\n每次查询扣除 1.5 积分 空不扣除积分"
        )
        bot.send_message(chat_id, help_text)
    # [此处原有 sms, cyh, 3ys, 2ys, cp, bq 的逻辑代码... 为保持长度略，部署时请从上一版本复制逻辑]

# ================= 6. 通用处理器 (处理登录验证码等) =================

@bot.message_handler(func=lambda m: True)
def handle_all(message):
    state = user_states.get(message.chat.id)
    if state and state.get('step') == 'wait_code':
        code = message.text.strip()
        async def finish_login():
            try:
                await client.sign_in(state['phone'], code, phone_code_hash=state['phone_code_hash'])
                bot.send_message(message.chat.id, "🎉 登录成功！自动签到功能已开启。")
                del user_states[message.chat.id]
            except Exception as e:
                bot.send_message(message.chat.id, f"❌ 登录失败: {str(e)}")
        asyncio.run_coroutine_threadsafe(finish_login(), loop)
        return

    # [此处原有处理核验、车牌号自动识别、身份证补齐的 handle_all 逻辑...]

# ================= 7. 回调与主程序 =================

def get_main_markup():
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(types.InlineKeyboardButton("使用帮助", callback_data="view_help"), types.InlineKeyboardButton("在线充值", callback_data="view_pay"))
    return markup

def get_main_text(source, uid, pts):
    first_name = source.from_user.first_name if hasattr(source.from_user, 'first_name') else "User"
    return (f"Admin@铭\n\n用户 ID: `{uid}`\n用户名称: `{first_name}`\n当前余额: `{pts:.2f}积分`\n\n使用帮助可查看使用教程\n在线充值可支持24小时\n1 USDT = 1 积分")

# 定时器与异步循环管理
loop = asyncio.new_event_loop()
def run_async_background(loop):
    asyncio.set_event_loop(loop)
    loop.run_until_complete(sign_in_loop())

if __name__ == '__main__':
    # 启动异步后台
    threading.Thread(target=run_async_background, args=(loop,), daemon=True).start()
    print("Bot 正在运行 (支持内置登录和自定义控制面板)...")
    bot.infinity_polling(timeout=10, long_polling_timeout=5)
