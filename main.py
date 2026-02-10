import telebot
import requests
import time
import re
import json
import os
from telebot import types

# ================= 1. 核心配置 =================
API_TOKEN = '8338893180:AAH-l_4m1-tweKyt92bliyk4fsPqoPQWzpU'
ADMIN_ID = 6649617045 
ADMIN_USERNAME = "@aaSm68"
POINTS_FILE = 'points.json'
AUTH_BEARER = "bearer eyJhbGciOiJIUzI1NiJ9.eyJwaG9uZSI6IisxOTM3ODg4NDgyNiIsIm9wZW5JZCI6Im95NW8tNHk3Wnd0WGlOaTVHQ3V3YzVVNDZJYk0iLCJpZENhcmRObyI6IjM3MDQ4MTE5ODgwODIwMzUxNCIsInVzZXJOYW1lIjoi6ams5rCR5by6IiwibG9naW5UaW1lIjoxNzY5NDE1NjYxMTk0LCJhcHBJZCI6Ind4ZjVmZDAyZDEwZGJiMjFkMiIsImlzcmVhbG5hbWUiOnRydWUsInNhYXNVc2VySWQiOm51bGwsImNvbXBhbnlJZCI6bnVsbCwiY29tcGFueVZPUyI6bnVsbH0.GwMYvckFHvFbhSi0NXpQDPiv9ZswUBAImN5bUipBla0"

bot = telebot.TeleBot(API_TOKEN)
user_points = {}
user_states = {}

def load_data():
    if os.path.exists(POINTS_FILE):
        try:
            with open(POINTS_FILE, 'r') as f:
                data = json.load(f)
                return {int(k): float(v) for k, v in data.items()}
        except: return {}
    return {}

def save_points():
    with open(POINTS_FILE, 'w') as f:
        json.dump({str(k): v for k, v in user_points.items()}, f)

user_points = load_data()

# ================= 2. 纯净界面 (无多余提示) =================

def get_main_text(message, uid, pts):
    first_name = message.from_user.first_name if message.from_user.first_name else "铭"
    username = f"@{message.from_user.username}" if message.from_user.username else "未设置"
    # 这里修复了那个该死的括号问题，直接返回字符串
    return (f"Admin@铭\n\n"
            f"用户 ID: {uid}\n"
            f"用户名称: {first_name}\n"
            f"用户名: {username}\n"
            f"当前余额: {pts:.2f}积分\n\n"
            f"使用帮助可查看使用教程\n"
            f"在线充值可支持 24 小时\n"
            f"1 USDT = 1 积分")

def get_help_text():
    return ("🛠️️使用帮助\n"
            "短信测压\n发送 /sms 手机号\n每次消耗 3.5 积分\n"
            "——————————————————\n"
            "批量二要素核验\n发送 /pl 进行核验\n每次核验扣除 2.5 积分\n"
            "——————————————————\n"
            "补齐身份证and核验\n发送 /bq 进行操作\n每次补齐扣除 0.1 积分\n"
            "——————————————————\n"
            "名字-身份证核验（企业级）\n全天 24h 秒出 毫秒级响应\n发送 /2ys 进行核验\n每次核验扣除 0.01 积分\n"
            "——————————————————\n"
            "名字-手机号-身份证核验（企业级）\n发送 /3ys 进行核验\n每次核验扣除 0.05 积分\n"
            "——————————————————\n"
            "常用号查询\n发送 /cyh 进行查询\n每次查询扣除 1.5 积分")

def get_main_markup():
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(types.InlineKeyboardButton("使用帮助", callback_data="view_help"),
               types.InlineKeyboardButton("在线充值", callback_data="view_pay"))
    return markup

# ================= 3. 业务功能 (三要素核验一致✅) =================

def query_3ys_logic(chat_id, name, id_card, phone, uid):
    url = "https://esb.wbszkj.cn/prod-api/wxminiapp/user/userIdVerify"
    headers = {"Authorization": AUTH_BEARER, "Content-Type": "application/json"}
    payload = {"name": name, "phone": phone, "idNo": id_card, "idType": 1}
    try:
        r = requests.post(url, headers=headers, json=payload, verify=False, timeout=10)
        user_points[uid] -= 0.05
        save_points()
        is_ok = r.status_code == 200 and r.json().get("success") == True
        status = "三要素核验一致✅" if is_ok else "三要素核验不一致❌"
        res = (f"名字：{name}\n手机号：{phone}\n身份证：{id_card}\n"
               f"结果：{status}\n\n已扣除 0.05 积分！\n当前余额：{user_points[uid]:.2f}")
        bot.send_message(chat_id, res)
    except: bot.send_message(chat_id, "❌ 接口超时")

# ================= 4. 全能消息路由 (指令+自动识别) =================

@bot.message_handler(commands=['start', 'add', 'sms', 'pl', 'bq', 'cyh', '2ys', '3ys'])
def handle_commands(message):
    uid, chat_id = message.from_user.id, message.chat.id
    if uid not in user_points: user_points[uid] = 0.0
    cmd = message.text.split()[0][1:].lower()

    if cmd == 'start':
        bot.send_message(chat_id, get_main_text(message, uid, user_points[uid]), reply_markup=get_main_markup())
    elif cmd == 'add' and uid == ADMIN_ID:
        try:
            p = message.text.split()
            tid, amt = int(p[1]), float(p[2])
            user_points[tid] = user_points.get(tid, 0.0) + amt
            save_points()
            bot.reply_to(message, f"✅ 已充值！当前余额：{user_points[tid]:.2f}")
        except: bot.reply_to(message, "格式：/add ID 积分")
    else:
        # 指令占位，提示用户输入内容
        bot.reply_to(message, f"已开启 {cmd} 模式，请发送对应内容。")

@bot.message_handler(func=lambda m: True)
def handle_all_text(message):
    uid, chat_id, text = message.from_user.id, message.chat.id, message.text.strip()
    if text.startswith('/'): return 

    # 自动识别 (3项为三要素，2项为二要素)
    parts = re.split(r'[,/\s]+', text)
    if len(parts) == 3:
        n, p, i = None, None, None
        for x in parts:
            if re.match(r'^[\u4e00-\u9fa5]{2,4}$', x): n = x
            elif re.match(r'^1[3-9]\d{9}$', x): p = x
            elif re.match(r'^\d{15,18}[xX]?$', x): i = x.upper()
        if n and p and i:
            if user_points.get(uid, 0.0) < 0.05: return bot.reply_to(message, "积分不足")
            return query_3ys_logic(chat_id, n, i, p, uid)
    
    # 状态处理逻辑 (比如正在进行的批量任务)
    if chat_id in user_states:
        # 这里补齐你原本的批量逻辑
        pass

@bot.callback_query_handler(func=lambda call: True)
def handle_cb(call):
    if call.data == "view_help":
        bot.edit_message_text(get_help_text(), call.message.chat.id, call.message.message_id)
    elif call.data == "view_pay":
        bot.send_message(call.message.chat.id, f"充值联系：{ADMIN_USERNAME}")

if __name__ == '__main__':
    bot.infinity_polling()
