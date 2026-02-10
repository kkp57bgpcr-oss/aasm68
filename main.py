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
import sms_list 
import sms_list_new
from sms_list import *
from Crypto.Cipher import DES3
from datetime import datetime
from telebot import types
from concurrent.futures import ThreadPoolExecutor

# 屏蔽 SSL 证书报警
from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

# ================= 1. 核心配置 =================
API_TOKEN = '8338893180:AAH-l_4m1-tweKyt92bliyk4fsPqoPQWzpU'
ADMIN_ID = 6649617045 
ADMIN_USERNAME = "@aaSm68"
POINTS_FILE = 'points.json'
TOKEN_FILE = 'token.txt'
DEFAULT_TOKEN = "eyJhbGciOiJIUzUxMiIsInR5cCI6IkpXVCJ9.eyJ1c2VySWQiOiIyNDkyNDYiLCJpYXQiOjE3Mzg1MDMxMTcsImV4cCI6MTczODY3NTkxN30.i9w1G8Y2mU5R5cCI6IkpXVCJ9" 

# 接口 Authorization
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

# ================= 2. 核心文本显示 =================

def get_main_text(source, uid, pts):
    first_name = source.from_user.first_name if hasattr(source.from_user, 'first_name') else "User"
    username = f"@{source.from_user.username}" if hasattr(source.from_user, 'username') and source.from_user.username else "未设置"
    return (f"Admin@铭\n\n"
            f"用户 ID: `{uid}`\n"
            f"用户名称: `{first_name}`\n"
            f"用户名: {username}\n"
            f"当前余额: `{pts:.2f}积分`\n\n"
            f"使用帮助可查看使用教程\n"
            f"在线充值可支持24小时\n"
            f"1 USDT = 1 积分")

def get_help_text():
    return (
        "🛠️️使用帮助\n"
        "短信测压\n"
        "发送 /sms 手机号\n"
        "每次消耗 3.5 积分\n"
        "——————————————————\n"
        "批量二要素核验\n"
        "发送 /pl 进行核验\n"
        "每次核验扣除 2.5 积分\n"
        "——————————————————\n"
        "补齐身份证and核验\n"
        "发送 /bq 进行操作\n"
        "每次补齐扣除 0.1 积分\n"
        "——————————————————\n"
        "名字-身份证核验（企业级）\n"
        "全天24h秒出 毫秒级响应\n"
        "发送 /2ys 进行核验\n"
        "每次核验扣除 0.01 积分\n"
        "——————————————————\n"
        "名字-手机号-身份证核验（企业级）\n"
        "发送 /3ys 进行核验\n"
        "每次核验扣除 0.05 积分\n"
        "——————————————————\n"
        "常用号查询\n"
        "发送 /cyh 进行查询\n"
        "每次查询扣除 1.5 积分 空不扣除积分"
    )

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

# ================= 3. 业务逻辑 (去链接版) =================

# --- 三要素 (核心修复：已删除 qingfeng 链接) ---
def query_3ys_logic(chat_id, name, id_card, phone, uid):
    url = "https://esb.wbszkj.cn/prod-api/wxminiapp/user/userIdVerify"
    headers = {"Authorization": AUTH_BEARER, "Content-Type": "application/json"}
    data = {"name": name, "phone": phone, "idNo": id_card, "idType": 1}
    try:
        r = requests.post(url, headers=headers, json=data, verify=False, timeout=10)
        user_points[uid] -= 0.05
        save_points()
        status = "三要素核验一致✅" if r.status_code == 200 and r.json().get("success") else "三要素核验不一致❌"
        res = (f"名字：{name}\n手机号：{phone}\n身份证：{id_card}\n结果：{status}\n\n"
               f"已扣除 0.05 积分！\n当前积分余额：{user_points[uid]:.2f} 积分")
        bot.send_message(chat_id, res)
    except: bot.send_message(chat_id, "❌ 接口响应超时")

# --- 二要素 ---
def single_verify_2ys(chat_id, name, id_card, uid):
    url = "https://api.xhmxb.com/wxma/moblie/wx/v1/realAuthToken"
    try:
        r = requests.post(url, headers={"Authorization": AUTH_BEARER, "Content-Type": "application/json"}, 
                          json={"name": name, "idCardNo": id_card}, timeout=10)
        user_points[uid] -= 0.01
        save_points()
        res_json = r.json()
        status = "二要素核验一致✅" if res_json.get("success") else "二要素验证失败 ❌"
        res = (f"姓名: **{name}**\n身份证: **{id_card}**\n结果: **{status}**\n\n"
               f"已扣除 **0.01** 积分！\n当前余额：**{user_points[uid]:.2f}**")
        bot.send_message(chat_id, res, parse_mode='Markdown')
    except: bot.send_message(chat_id, "❌ 接口异常")

# --- 常用号查询 ---
def xiaowunb_query_logic(chat_id, id_number, uid):
    try:
        r = requests.get(f"http://xiaowunb.top/cyh.php?sfz={id_number}", timeout=10)
        user_points[uid] -= 1.5; save_points()
        bot.send_message(chat_id, f"📑 **身份查询结果**\n\n{r.text}\n\n已扣除 1.5 积分！", parse_mode='Markdown')
    except: bot.send_message(chat_id, "❌ 查询失败")

# --- 短信轰炸 / 批量核验 / 补齐 逻辑 ---
# [此处代码维持 sms_bomb_cmd, run_batch_task, get_all_senders 等完整函数逻辑]
# (由于篇幅限制，这里省略中间未变动的复杂函数体，请在 main.py 中保留它们)

# ================= 4. 全自动识别与分发 =================

@bot.message_handler(func=lambda m: True)
def handle_all(message):
    uid, chat_id, text = message.from_user.id, message.chat.id, message.text.strip()
    if text.startswith('/'):
        cmd = text.split()[0][1:]
        if cmd == 'start':
            if uid not in user_points: user_points[uid] = 0.0
            bot.send_message(chat_id, get_main_text(message, uid, user_points[uid]), parse_mode='Markdown', reply_markup=get_main_markup())
        elif cmd == '3ys': 
            bot.send_message(chat_id, "请输入三要素信息：\n姓名 身份证 手机号")
        elif cmd == '2ys': 
            user_states[chat_id] = {'step': 'v_2ys'}
            bot.send_message(chat_id, "请输入姓名 身份证")
        # [处理 /pl /bq /cyh /add 等指令...]
        return

    # --- 自动识别逻辑 ---
    if chat_id not in user_states or not user_states[chat_id].get('step'):
        parts = re.split(r'[,/\s]+', text)
        if len(parts) == 3: # 自动识别三要素
            n, p, i = None, None, None
            for x in parts:
                if re.match(r'^[\u4e00-\u9fa5]{2,4}$', x): n = x
                elif re.match(r'^1[3-9]\d{9}$', x): p = x
                elif re.match(r'^[\dXx]{15}$|^[\dXx]{18}$', x): i = x.upper()
            if n and p and i:
                if user_points.get(uid, 0.0) < 0.05: return bot.reply_to(message, "❌ 积分不足")
                return query_3ys_logic(chat_id, n, i, p, uid)
        
        if len(parts) == 2: # 自动识别二要素
            n, i = None, None
            for x in parts:
                if re.match(r'^[\u4e00-\u9fa5]{2,4}$', x): n = x
                elif re.match(r'^[\dXx]{15}$|^[\dXx]{18}$', x): i = x.upper()
            if n and i:
                if user_points.get(uid, 0.0) < 0.01: return bot.reply_to(message, "❌ 积分不足")
                return single_verify_2ys(chat_id, n, i, uid)

    # --- 状态机处理 (批量、补齐等后续步) ---
    # [保留原有的 state 处理逻辑]

@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    uid, pts = call.from_user.id, user_points.get(call.from_user.id, 0.0)
    if call.data == "view_help":
        bot.edit_message_text(get_help_text(), call.message.chat.id, call.message.message_id, reply_markup=types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("🔙", callback_data="back_to_main")))
    elif call.data == "view_pay":
        bot.edit_message_text("🛍️ 请选择充值方式：\n1 USDT = 1 积分", call.message.chat.id, call.message.message_id, reply_markup=get_pay_markup())
    elif call.data == "back_to_main":
        bot.edit_message_text(get_main_text(call, uid, pts), call.message.chat.id, call.message.message_id, parse_mode='Markdown', reply_markup=get_main_markup())

if __name__ == '__main__':
    bot.infinity_polling()
