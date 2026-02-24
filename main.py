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

# 外部接口配置
AUTH_BEARER = "bearer eyJhbGciOiJIUzI1NiJ9.eyJwaG9uZSI6IisxOTM3ODg4NDgyNiIsIm9wZW5JZCI6Im95NW8tNHk3Wnd0WGlOaTVHQ3V3YzVVNDZJYk0iLCJpZENhcmRObyI6IjM3MDQ4MTE5ODgwODIwMzUxNCIsInVzZXJOYW1lIjoi6ams5rCR5by6IiwibG9naW5UaW1lIjoxNzY5NDE1NjYxMTk0LCJhcHBJZCI6Ind4ZjVmZDAyZDEwZGJiMjFkMiIsImlzcmVhbG5hbWUiOnRydWUsInNhYXNVc2VySWQiOm51bGwsImNvbXBhbnlJZCI6bnVsbCwiY29tcGFueVZPUyI6bnVsbH0.GwMYvckFHvFbhSi0NXpQDPiv9ZswUBAImN5bUipBla0"

bot = telebot.TeleBot(API_TOKEN)
user_points = {}
user_states = {}

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

# ================= 2. 功能逻辑 =================

def liemo_query_logic(chat_id, text, uid):
    """猎魔模糊查询逻辑 - 正在查询 (已移除翻页)"""
    wait_msg = bot.send_message(chat_id, "⏳ 正在查询...")

    api_url = "https://api.kona.uno/API/liemo.php"
    try:
        # 只查询第一页，移除翻页逻辑
        response = requests.get(api_url, params={"text": text, "page": 1}, timeout=20)
        res_text = response.text.strip()
        
        if res_text and "未找到" not in res_text:
            user_points[uid] -= 1.5
            save_points()
            
            # 清理正文，截断过长内容防止报错
            if len(res_text) > 3800:
                res_text = res_text[:3800] + "\n\n<b>(内容过多，仅显示部分)</b>"
            
            result = (f"🔍 <b>查询关键词: {text}</b>\n"
                      f"——————————————————\n"
                      f"{res_text}\n"
                      f"——————————————————\n"
                      f"<b>已扣除 1.5 积分！</b>\n"
                      f"<b>当前余额: {user_points[uid]:.2f}</b>")
            
            bot.delete_message(chat_id, wait_msg.message_id)
            bot.send_message(chat_id, result, parse_mode='HTML')
        else:
            msg = f"🔍 关键词: {text}\n\n未匹配到有效信息。\n\n查询无结果，未扣除积分。"
            bot.delete_message(chat_id, wait_msg.message_id)
            bot.send_message(chat_id, msg)
                
    except Exception as e:
        bot.edit_message_text(f"❌ 查询异常: {str(e)}", chat_id, wait_msg.message_id)

def cp_query_logic(chat_id, car_no, uid):
    """车牌查询 - 正在查询"""
    wait_msg = bot.send_message(chat_id, "⏳ 正在查询...")
    url = f"http://zgzapi.idc.cn.com/车档.php?key=体验卡&cph={urllib.parse.quote(car_no)}"
    try:
        response = requests.get(url, timeout=15); response.encoding = 'utf-8'
        raw_res = response.text.strip()
        if raw_res and "未找到" not in raw_res and "错误" not in raw_res:
            user_points[uid] -= 2.5; save_points()
            message = (f"🚗 车牌查询结果:\n\n车牌号：{car_no}\n详细信息：\n{raw_res}\n\n"
                       f"<b>已扣除 2.5 积分！</b>\n<b>当前余额: {user_points[uid]:.2f}</b>")
        else: message = (f"🚗 车牌查询结果:\n\n未匹配到有效车档信息。\n\n查询无结果，未扣除积分。\n<b>当前余额: {user_points[uid]:.2f}</b>")
        bot.delete_message(chat_id, wait_msg.message_id)
        bot.send_message(chat_id, message, parse_mode='HTML')
    except Exception as e: bot.edit_message_text(f"⚠️ 查询异常: {str(e)}", chat_id, wait_msg.message_id)

def query_3ys_logic(chat_id, name, id_card, phone, uid):
    """三要素核验 - 正在核验"""
    wait_msg = bot.send_message(chat_id, "⏳ 正在核验...")
    url = "http://xiaowunb.top/3ys.php"
    params = {"name": name, "sfz": id_card, "sjh": phone}
    try:
        response = requests.get(url, params=params, timeout=15); response.encoding = 'utf-8'
        user_points[uid] -= 0.05; save_points()
        clean_res = re.sub(r'小无 API.*?官方客服:@\w+', '', response.text.strip(), flags=re.DOTALL).strip()
        res_status = "三要素核验成功✅" if ("成功" in clean_res or "一致" in clean_res) else "三要素核验失败❌"
        bot.delete_message(chat_id, wait_msg.message_id)
        bot.send_message(chat_id, f"姓名：{name}\n手机号：{phone}\n身份证：{id_card}\n结果：{res_status}\n\n"
                                  f"<b>已扣除 0.05 积分！</b>\n<b>当前余额：{user_points[uid]:.2f}</b>", parse_mode='HTML')
    except Exception as e: bot.edit_message_text(f"⚠️ 核验异常: {str(e)}", chat_id, wait_msg.message_id)

def single_verify_2ys(chat_id, name, id_card, uid):
    """二要素核验 - 正在核验"""
    wait_msg = bot.send_message(chat_id, "⏳ 正在核验...")
    url = "https://api.xhmxb.com/wxma/moblie/wx/v1/realAuthToken"
    headers = {"Authorization": AUTH_BEARER, "Content-Type": "application/json", "User-Agent": "Mozilla/5.0", "Referer": "https://servicewechat.com/wxf5fd02d10dbb21d2/59/page-frame.html"}
    try:
        r = requests.post(url, headers=headers, json={"name": name, "idCardNo": id_card}, timeout=10)
        user_points[uid] -= 0.01; save_points()
        res_type = "二要素核验一致✅" if r.json().get("success") else "二要素验证失败 ❌"
        bot.delete_message(chat_id, wait_msg.message_id)
        bot.send_message(chat_id, f"姓名: {name}\n身份证: {id_card}\n结果: {res_type}\n\n"
                                  f"<b>已扣除 0.01 积分！</b>\n<b>当前余额：{user_points[uid]:.2f}</b>", parse_mode='HTML')
    except Exception as e: bot.edit_message_text(f"❌ 核验异常: {str(e)}", chat_id, wait_msg.message_id)

# ================= 3. UI 菜单 =================

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
    return (f"<b>Admin@铭</b>\n\n"
            f"<b>用户 ID:</b> <code>{uid}</code>\n"
            f"<b>用户名称:</b> {first_name}\n"
            f"<b>用户名:</b> {username}\n"
            f"<b>当前余额:</b> <code>{pts:.2f}积分</code>\n\n"
            f"<b>使用帮助可查看使用教程</b>\n"
            f"<b>在线充值可支持24小时</b>\n"
            f"<b>1 USDT = 1 积分</b>")

# ================= 4. 消息处理 =================

@bot.message_handler(commands=['start', '3ys', '2ys', 'cp', 'cx', 'add'])
def handle_commands(message):
    uid, chat_id = message.from_user.id, message.chat.id
    cmd_parts = message.text.split()
    cmd = cmd_parts[0][1:]
    current_pts = user_points.get(uid, 0.0)

    if cmd == 'start':
        if uid not in user_points: user_points[uid] = 0.0
        bot.send_message(chat_id, get_main_text(message, uid, user_points[uid]), parse_mode='HTML', reply_markup=get_main_markup())
    elif cmd == 'cx':
        if current_pts < 1.5: return bot.send_message(chat_id, "<b>积分不足，请先充值！</b>", parse_mode='HTML')
        user_states[chat_id] = {'step': 'v_cx'}
        bot.send_message(chat_id, "请输入要查询的信息：")
    elif cmd == '2ys':
        if current_pts < 0.01: return bot.send_message(chat_id, "<b>积分不足，请先充值！</b>", parse_mode='HTML')
        bot.send_message(chat_id, "请输入：姓名 身份证"); user_states[chat_id] = {'step': 'v_2ys'}
    elif cmd == '3ys':
        if current_pts < 0.05: return bot.send_message(chat_id, "<b>积分不足，请先充值！</b>", parse_mode='HTML')
        bot.send_message(chat_id, "请输入：姓名 身份证 手机号"); user_states[chat_id] = {'step': 'v_3ys'}
    elif cmd == 'cp':
        if current_pts < 2.5: return bot.send_message(chat_id, "<b>积分不足，请先充值！</b>", parse_mode='HTML')
        user_states[chat_id] = {'step': 'v_cp'}; bot.send_message(chat_id, "请输入车牌号：")
    elif cmd == 'add':
        if uid == ADMIN_ID:
            try:
                target_uid = int(cmd_parts[1])
                add_amount = float(cmd_parts[2])
                user_points[target_uid] = user_points.get(target_uid, 0.0) + add_amount
                save_points()
                # 修改点：显示用户当前余额
                bot.reply_to(message, f"✅ 充值成功！\n用户 ID: <code>{target_uid}</code>\n充值金额: {add_amount}\n<b>当前总余额: {user_points[target_uid]:.2f} 积分</b>", parse_mode='HTML')
            except Exception as e: bot.reply_to(message, f"❌ 格式错误：/add 用户ID 金额\n错误信息: {str(e)}")
        else: bot.reply_to(message, "⛔ 您没有权限访问此命令！")

@bot.message_handler(func=lambda m: True)
def handle_all_text(message):
    uid, chat_id, text = message.from_user.id, message.chat.id, message.text.strip()
    if text.startswith('/'): return
    current_pts = user_points.get(uid, 0.0); state = user_states.get(chat_id, {})
    
    if state.get('step') == 'v_cx':
        del user_states[chat_id]
        return liemo_query_logic(chat_id, text, uid)

    if 'x' in text:
        if current_pts < 1.5: return bot.send_message(chat_id, "<b>积分不足，请先充值！</b>", parse_mode='HTML')
        return liemo_query_logic(chat_id, text, uid)
        
    parts = re.split(r'[,，\s\n]+', text)
    if re.match(r'^[京津沪渝冀豫云辽黑湖南皖鲁新苏浙赣鄂桂甘晋蒙陕吉闽贵粤青藏川宁琼]{1}[A-Z]{1}[A-Z0-9]{5,6}$', text.upper()):
        if current_pts < 2.5: return bot.send_message(chat_id, "<b>积分不足，请先充值！</b>", parse_mode='HTML')
        return cp_query_logic(chat_id, text.upper(), uid)
    if len(parts) >= 3:
        n, p, i = None, None, None
        for x in parts:
            if not n and re.match(r'^[\u4e00-\u9fa5]{2,4}$', x): n = x
            elif not p and re.match(r'^1[3-9]\d{9}$', x): p = x
            elif not i and re.match(r'^[\dXx]{15}$|^[\dXx]{18}$', x): i = x.upper()
        if n and p and i:
            if current_pts < 0.05: return bot.send_message(chat_id, "<b>积分不足，请先充值！</b>", parse_mode='HTML')
            return query_3ys_logic(chat_id, n, i, p, uid)
    if len(parts) == 2:
        n, i = None, None
        for x in parts:
            if not n and re.match(r'^[\u4e00-\u9fa5]{2,4}$', x): n = x
            elif not i and re.match(r'^[\dXx]{15}$|^[\dXx]{18}$', x): i = x.upper()
        if n and i:
            if current_pts < 0.01: return bot.send_message(chat_id, "<b>积分不足，请先充值！</b>", parse_mode='HTML')
            return single_verify_2ys(chat_id, n, i, uid)
    
    if current_pts < 1.5: return bot.send_message(chat_id, "<b>积分不足，请先充值！</b>", parse_mode='HTML')
    return liemo_query_logic(chat_id, text, uid)

# ================= 5. 回调处理 =================

@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    uid, pts = call.from_user.id, user_points.get(call.from_user.id, 0.0)
    
    if call.data == "view_help":
        # 已移除人脸核验描述
        help_text = (
            "<b>🛠️ 使用帮助</b>\n"
            "<b>liemo查询 (猎魔人)</b>\n"
            "<b>发送 /cx 进行查询</b>\n"
            "<b>全天24h秒出 liemo同款接口</b>\n"
            "<b>每次查询扣除 1.5 积分</b>\n"
            "<b>——————————————————</b>\n"
            "<b>名字-身份证核验 (企业级)</b>\n"
            "<b>全天 24h 秒出 毫秒级响应</b>\n"
            "<b>发送 /2ys 进行核验</b>\n"
            "<b>每次核验扣除 0.01 积分</b>\n"
            "<b>——————————————————</b>\n"
            "<b>名字-手机号-身份证核验 (企业级)</b>\n"
            "<b>全天 24h 秒出 毫秒级响应</b>\n"
            "<b>发送 /3ys 进行核验</b>\n"
            "<b>每次核验扣除 0.05 积分</b>\n"
            "<b>——————————————————</b>\n"
            "<b>车牌号查询</b>\n"
            "<b>发送 /cp 进行查询</b>\n"
            "<b>全天 24h 秒出 假 1 赔 10000</b>\n"
            "<b>每次查询扣除 2.5 积分 空不扣除积分</b>"
        )
        bot.edit_message_text(help_text, call.message.chat.id, call.message.message_id, reply_markup=get_help_markup(), parse_mode='HTML')
    elif call.data == "view_pay":
        bot.edit_message_text("🛍️ <b>请选择充值方式：</b>\n<b>1 USDT = 1 积分</b>", call.message.chat.id, call.message.message_id, reply_markup=get_pay_markup(), parse_mode='HTML')
    elif call.data == "back_to_main":
        bot.edit_message_text(get_main_text(call, uid, pts), call.message.chat.id, call.message.message_id, parse_mode='HTML', reply_markup=get_main_markup())

if __name__ == '__main__':
    print("Bot 正在运行 (已移除人脸与翻页功能)...")
    bot.infinity_polling(timeout=10)
