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
IMAGE_HOST_API_KEY = "chv_e0sb_e58e156ce7f7c1d4439b550210c718de0c7af8820db77c0cd04e198ed06011b2e32ed1b5a7f1b00e543c76c20f5c64866bb355fde1dca14d6d74f0a1989b567d"
IMAGE_HOST_URL = "https://imgloc.com/api/1/upload"

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

def process_rlhy(chat_id, name, sfz, photo_file_id, uid):
    wait_msg = bot.send_message(chat_id, "⏳ <b>正在核验...</b>", parse_mode='HTML')
    try:
        file_info = bot.get_file(photo_file_id)
        img_bytes = bot.download_file(file_info.file_path)
        files = {'source': ('face.jpg', img_bytes, 'image/jpeg')}
        data = {'key': IMAGE_HOST_API_KEY, 'format': 'json'}
        up_res = requests.post(IMAGE_HOST_URL, files=files, data=data, timeout=30).json()
        
        if up_res.get('status_code') == 200:
            tp_url = up_res['image']['url']
        else:
            bot.edit_message_text("❌ <b>图床上传失败</b>", chat_id, wait_msg.message_id, parse_mode='HTML')
            return

        base_url = "https://xiaowunb.top/rlhy.php"
        params = {"name": name, "sfz": sfz, "tp": tp_url, "key": "小无爱公益"}
        res_text = requests.get(base_url, params=params, timeout=25).text
        
        if "验证成功" in res_text:
            status_head, res_desc = "✅<b>核验成功!</b>", "人脸核验通过🟢"
        elif "活体" in res_text or "采集失败" in res_text:
            status_head, res_desc = "❌<b>核验失败!</b>", "活体采集失败🔴"
        else:
            status_head, res_desc = "❌<b>核验失败!</b>", "人脸核验失败🔴"

        user_points[uid] -= 0.1
        save_points()

        result = (f"{status_head}\n\n<b>姓名:</b> {name}\n<b>身份证:</b> {sfz}\n<b>结果:</b> {res_desc}\n\n"
                  f"已扣除 <b>0.1</b> 积分！\n<b>当前余额:</b> <code>{user_points[uid]:.2f}</code>")
        
        bot.delete_message(chat_id, wait_msg.message_id)
        bot.send_message(chat_id, result, parse_mode='HTML')
    except Exception as e:
        bot.edit_message_text(f"❌ <b>核验异常:</b> {str(e)}", chat_id, wait_msg.message_id, parse_mode='HTML')

def cp_query_logic(chat_id, car_no, uid):
    url = f"http://zgzapi.idc.cn.com/车档.php?key=体验卡&cph={urllib.parse.quote(car_no)}"
    try:
        response = requests.get(url, timeout=15)
        response.encoding = 'utf-8'
        raw_res = response.text.strip()
        if raw_res and "未找到" not in raw_res and "错误" not in raw_res:
            user_points[uid] -= 2.5; save_points()
            message = (f"🚗 <b>车牌查询结果:</b>\n\n<b>车牌号：</b> <code>{car_no}</code>\n<b>详细信息：</b>\n{raw_res}\n\n已扣除 <b>2.5</b> 积分！\n<b>当前余额:</b> <code>{user_points[uid]:.2f}</code>")
        else:
            message = (f"🚗 <b>车牌查询结果:</b>\n\n未匹配到有效车档信息。\n\n查询无结果，未扣除积分。\n<b>当前余额:</b> <code>{user_points[uid]:.2f}</code>")
        bot.send_message(chat_id, message, parse_mode='HTML')
    except Exception as e: bot.send_message(chat_id, f"⚠️ <b>车档接口异常:</b> {str(e)}", parse_mode='HTML')

def query_3ys_logic(chat_id, name, id_card, phone, uid):
    url = "http://xiaowunb.top/3ys.php"
    params = {"name": name, "sfz": id_card, "sjh": phone}
    try:
        response = requests.get(url, params=params, timeout=15)
        response.encoding = 'utf-8'
        user_points[uid] -= 0.05; save_points()
        clean_res = re.sub(r'小无 API.*?官方客服:@\w+', '', response.text.strip(), flags=re.DOTALL).strip()
        res_status = "<b>三要素核验成功✅</b>" if ("成功" in clean_res or "一致" in clean_res) else "<b>三要素核验失败❌</b>"
        bot.send_message(chat_id, f"<b>姓名：</b> {name}\n<b>手机号：</b> {phone}\n<b>身份证：</b> {id_card}\n<b>结果：</b> {res_status}\n\n已扣除 <b>0.05</b> 积分！\n<b>当前余额：</b> <code>{user_points[uid]:.2f}</code>", parse_mode='HTML')
    except Exception as e: bot.send_message(chat_id, f"⚠️ <b>系统异常:</b> {str(e)}", parse_mode='HTML')

def single_verify_2ys(chat_id, name, id_card, uid):
    url = "https://api.xhmxb.com/wxma/moblie/wx/v1/realAuthToken"
    headers = {"Authorization": AUTH_BEARER, "Content-Type": "application/json", "User-Agent": "Mozilla/5.0", "Referer": "https://servicewechat.com/wxf5fd02d10dbb21d2/59/page-frame.html"}
    try:
        r = requests.post(url, headers=headers, json={"name": name, "idCardNo": id_card}, timeout=10)
        user_points[uid] -= 0.01; save_points()
        res_type = "<b>二要素核验一致✅</b>" if r.json().get("success") else "<b>二要素验证失败 ❌</b>"
        bot.send_message(chat_id, f"<b>姓名:</b> {name}\n<b>身份证:</b> {id_card}\n<b>结果:</b> {res_type}\n\n已扣除 <b>0.01</b> 积分！\n<b>当前余额：</b> <code>{user_points[uid]:.2f}</code>", parse_mode='HTML')
    except Exception as e: bot.send_message(chat_id, f"❌ <b>接口失败:</b> {str(e)}", parse_mode='HTML')

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
            f"使用帮助可查看使用教程\n"
            f"在线充值可支持24小时\n"
            f"<b>1 USDT = 1 积分</b>")

# ================= 4. 消息处理 =================

@bot.message_handler(commands=['start', 'rlhy', '3ys', '2ys', 'cp', 'add'])
def handle_commands(message):
    uid, chat_id = message.from_user.id, message.chat.id
    cmd_parts = message.text.split()
    cmd = cmd_parts[0][1:]
    
    current_pts = user_points.get(uid, 0.0)

    if cmd == 'start':
        if uid not in user_points: user_points[uid] = 0.0
        bot.send_message(chat_id, get_main_text(message, uid, user_points[uid]), parse_mode='HTML', reply_markup=get_main_markup())
    
    elif cmd == 'rlhy':
        if current_pts < 0.1: return bot.send_message(chat_id, "<b>积分不足，请先充值！</b>", parse_mode='HTML')
        user_states[chat_id] = {'step': 'awaiting_rlhy'}
        bot.send_message(chat_id, "请输入：<b>姓名 身份证</b> 并添加一张人脸图片一起发送。", parse_mode='HTML')
    
    elif cmd == '2ys':
        if current_pts < 0.01: return bot.send_message(chat_id, "<b>积分不足，请先充值！</b>", parse_mode='HTML')
        bot.send_message(chat_id, "请输入：<b>姓名 身份证</b>", parse_mode='HTML')
        user_states[chat_id] = {'step': 'v_2ys'}
    
    elif cmd == '3ys':
        if current_pts < 0.05: return bot.send_message(chat_id, "<b>积分不足，请先充值！</b>", parse_mode='HTML')
        bot.send_message(chat_id, "请输入：<b>姓名 身份证 手机号</b>", parse_mode='HTML')
        user_states[chat_id] = {'step': 'v_3ys'}
    
    elif cmd == 'cp':
        if current_pts < 2.5: return bot.send_message(chat_id, "<b>积分不足，请先充值！</b>", parse_mode='HTML')
        user_states[chat_id] = {'step': 'v_cp'}; bot.send_message(chat_id, "请输入<b>车牌号</b>：", parse_mode='HTML')
    
    elif cmd == 'add':
        if uid == ADMIN_ID:
            try:
                target_uid = int(cmd_parts[1])
                add_pts = float(cmd_parts[2])
                user_points[target_uid] = user_points.get(target_uid, 0.0) + add_pts
                save_points()
                bot.reply_to(message, "✅ <b>充值成功</b>", parse_mode='HTML')
            except: pass
        else:
            bot.reply_to(message, "⛔ <b>您没有权限访问此命令！</b>", parse_mode='HTML')

@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    uid, chat_id = message.from_user.id, message.chat.id
    caption = message.caption.strip() if message.caption else ""
    parts = re.split(r'[,，\s\n]+', caption)
    
    if (user_states.get(chat_id, {}).get('step') == 'awaiting_rlhy') or len(parts) >= 2:
        if len(parts) < 2: return bot.reply_to(message, "⚠️ <b>请在发送图片备注中输入：姓名 身份证</b>", parse_mode='HTML')
        if user_points.get(uid, 0.0) < 0.1: return bot.send_message(chat_id, "<b>积分不足，请先充值！</b>", parse_mode='HTML')
        if chat_id in user_states: del user_states[chat_id]
        threading.Thread(target=process_rlhy, args=(chat_id, parts[0], parts[1], message.photo[-1].file_id, uid)).start()

@bot.message_handler(func=lambda m: True)
def handle_all_text(message):
    uid, chat_id, text = message.from_user.id, message.chat.id, message.text.strip()
    if text.startswith('/'): return

    current_pts = user_points.get(uid, 0.0)
    state = user_states.get(chat_id, {})
    
    # 状态识别逻辑
    if state.get('step') == 'v_2ys':
        parts = re.split(r'[,，\s\n]+', text)
        if len(parts) >= 2:
            if current_pts < 0.01: return bot.send_message(chat_id, "<b>积分不足，请先充值！</b>", parse_mode='HTML')
            del user_states[chat_id]
            return single_verify_2ys(chat_id, parts[0], parts[1], uid)
            
    elif state.get('step') == 'v_3ys':
        parts = re.split(r'[,，\s\n]+', text)
        if len(parts) >= 3:
            if current_pts < 0.05: return bot.send_message(chat_id, "<b>积分不足，请先充值！</b>", parse_mode='HTML')
            del user_states[chat_id]
            return query_3ys_logic(chat_id, parts[0], parts[1], parts[2], uid)
            
    elif state.get('step') == 'v_cp':
        if current_pts < 2.5: return bot.send_message(chat_id, "<b>积分不足，请先充值！</b>", parse_mode='HTML')
        del user_states[chat_id]; return cp_query_logic(chat_id, text.upper(), uid)

    # 自动识别逻辑
    if re.match(r'^[京津沪渝冀豫云辽黑湖南皖鲁新苏浙赣鄂桂甘晋蒙陕吉闽贵粤青藏川宁琼]{1}[A-Z]{1}[A-Z0-9]{5,6}$', text.upper()):
        if current_pts < 2.5: return bot.send_message(chat_id, "<b>积分不足，请先充值！</b>", parse_mode='HTML')
        return cp_query_logic(chat_id, text.upper(), uid)

    parts = re.split(r'[,，\s\n]+', text)
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

# ================= 5. 回调处理 =================

@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    uid, pts = call.from_user.id, user_points.get(call.from_user.id, 0.0)
    if call.data == "view_help":
        help_text = (
            "<b>🛠️ 使用帮助</b>\n"
            "<b>企业级人脸核验</b>\n"
            "发送 /rlhy 先选择一张待核验的图片\n"
            "附带输入：<b>姓名 身份证号</b>\n"
            "每次核验扣除 <b>0.1</b> 积分\n"
            "——————————————————\n"
            "<b>名字-身份证核验（企业级）</b>\n"
            "全天 24h 秒出 <b>毫秒级响应</b>\n"
            "发送 /2ys 进行核验\n"
            "每次核验扣除 <b>0.01</b> 积分\n"
            "——————————————————\n"
            "<b>名字-手机号-身份证核验（企业级）</b>\n"
            "全天 24h 秒出 <b>毫秒级响应</b>\n"
            "发送 /3ys 进行核验\n"
            "每次核验扣除 <b>0.05</b> 积分\n"
            "——————————————————\n"
            "<b>车牌号查询</b>\n"
            "发送 /cp 进行查询\n"
            "全天 24h 秒出 <b>假 1 赔 10000</b>\n"
            "每次查询扣除 <b>2.5</b> 积分 空不扣除积分"
        )
        bot.edit_message_text(help_text, call.message.chat.id, call.message.message_id, reply_markup=get_help_markup(), parse_mode='HTML')
    elif call.data == "view_pay":
        bot.edit_message_text("🛍️ <b>请选择充值方式：</b>\n<b>1 USDT = 1 积分</b>", call.message.chat.id, call.message.message_id, reply_markup=get_pay_markup(), parse_mode='HTML')
    elif call.data == "back_to_main":
        bot.edit_message_text(get_main_text(call, uid, pts), call.message.chat.id, call.message.message_id, parse_mode='HTML', reply_markup=get_main_markup())

if __name__ == '__main__':
    print("Bot 正在运行 (HTML 模式)...")
    bot.infinity_polling(timeout=10)
