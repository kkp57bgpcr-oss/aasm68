import telebot
import requests
import time
import re
import threading
import json
import os
import base64
import itertools
import binascii
import random
import concurrent.futures
import inspect  
import urllib.parse
from flask import Flask, request  # 新增 Flask 依赖

# 如果你的环境中没有这两个本地文件，请确保它们存在
try:
    import sms_list 
    import sms_list_new
    from sms_list import *
except ImportError:
    pass

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

# API 专用配置 (你之前要求的 API 校验逻辑)
ADMIN_KEY_API = "铭666"

# 外部接口配置
AUTH_BEARER = "bearer eyJhbGciOiJIUzI1NiJ9.eyJwaG9uZSI6IisxOTM3ODg4NDgyNiIsIm9wZW5JZCI6Im95NW8tNHk3Wnd0WGlOaTVHQ3V3YzVVNDZJYk0iLCJpZENhcmRObyI6IjM3MDQ4MTE5ODgwODIwMzUxNCIsInVzZXJOYW1lIjoi6ams5rCR5by6IiwibG9naW5UaW1lIjoxNzY5NDE1NjYxMTk0LCJhcHBJZCI6Ind4ZjVmZDAyZDEwZGJiMjFkMiIsImlzcmVhbG5hbWUiOnRydWUsInNhYXNVc2VySWQiOm51bGwsImNvbXBhbnlJZCI6bnVsbCwiY29tcGFueVZPUyI6bnVsbH0.GwMYvckFHvFbhSi0NXpQDPiv9ZswUBAImN5bUipBla0"
IMAGE_HOST_API_KEY = "chv_e0sb_e58e156ce7f7c1d4439b550210c718de0c7af8820db77c0cd04e198ed06011b2e32ed1b5a7f1b00e543c76c20f5c64866bb355fde1dca14d6d74f0a1989b567d"
IMAGE_HOST_URL = "https://imgloc.com/api/1/upload"

bot = telebot.TeleBot(API_TOKEN)
app = Flask(__name__)  # 初始化 Flask
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

# ================= 2. API 网页端功能 (保持之前的逻辑) =================

def check_api_key(user_key):
    if user_key == ADMIN_KEY_API:
        return True, "2099年12月31日 (永久管理)"
    try:
        missing_padding = len(user_key) % 4
        if missing_padding: user_key += '=' * (4 - missing_padding)
        decoded = base64.b64decode(user_key.encode()).decode('utf-8')
        if '_' in decoded:
            prefix, expire_ts = decoded.split('_')
            if prefix == "铭":
                ts = int(expire_ts)
                time_str = time.strftime('%Y-%m-%d %H:%M', time.localtime(ts))
                return (True, time_str) if time.time() < ts else (False, "已过期")
    except: pass
    return False, "无效Key"

@app.route('/rlhy.php')
def api_route():
    name = request.args.get('name', '')
    sfz = request.args.get('sfz', '')
    tp = request.args.get('tp', '')
    key = request.args.get('key', '')
    ok, time_info = check_api_key(key)
    if not ok: return f"❌ 拒绝访问: {time_info}", 403

    # 执行核验逻辑
    url = "https://www.cjhyzx.com/api/vx/actual/carrier/center/realPersonAuthentication"
    headers = {"Authorization": "Bearer eyJhbGciOiJIUzUxMiJ9.eyJsb2dpbl91c2VyX2tleSI6IjA5YjViMDQ2LWI1NzYtNGJlNi05MGVhLTllY2YxNGNiMjI4MiJ9.fIUe4cTbOnK-l68a8cF44glMCd32sWxphcftKah6d9PK4PAo7vV9AdJOByZMt_X8YouKC6cb0_R_IUOgUBNMFg", "Content-Type": "application/json"}
    payload = {"carrierUser": {"identityCard": sfz, "nickName": name}, "sysAttachmentInfoList": [{"fileUrl": tp}]}
    try:
        res = requests.post(url, headers=headers, json=payload, timeout=20).json()
        is_success = str(res.get("code")) == "200"
        res_text = "人脸核验通过🟢" if is_success else f"核验未通过🔴 ({res.get('msg')})"
    except: res_text = "接口请求失败"

    return f"""<div style="font-family:sans-serif;padding:20px;line-height:1.8;">
                ✅ 核验结果<br><br>姓名: {name}<br>身份证: {sfz}<br>结果: {res_text}<br><br>卡密到期时间: {time_info}</div>"""

# ================= 3. 机器人功能逻辑 (保持不变) =================

def process_rlhy(chat_id, name, sfz, photo_file_id, uid):
    wait_msg = bot.send_message(chat_id, "⏳ 正在核验...")
    try:
        file_info = bot.get_file(photo_file_id)
        img_bytes = bot.download_file(file_info.file_path)
        files = {'source': ('face.jpg', img_bytes, 'image/jpeg')}
        data = {'key': IMAGE_HOST_API_KEY, 'format': 'json'}
        up_res = requests.post(IMAGE_HOST_URL, files=files, data=data, timeout=30).json()
        
        if up_res.get('status_code') == 200:
            tp_url = up_res['image']['url']
        else:
            bot.edit_message_text("❌ 图床上传失败", chat_id, wait_msg.message_id)
            return

        base_url = "https://xiaowunb.top/rlhy.php"
        params = {"name": name, "sfz": sfz, "tp": tp_url, "key": "小无爱公益"}
        res_text = requests.get(base_url, params=params, timeout=25).text
        
        if "验证成功" in res_text:
            status_head, res_desc = "✅核验成功!", "人脸核验通过🟢"
        elif "活体" in res_text or "采集失败" in res_text:
            status_head, res_desc = "❌核验失败!", "活体采集失败🔴"
        else:
            status_head, res_desc = "❌核验失败!", "人脸核验失败🔴"

        user_points[uid] -= 0.1
        save_points()

        result = (f"{status_head}\n\n姓名: {name}\n身份证: {sfz}\n结果: {res_desc}\n\n"
                  f"已扣除 0.1 积分！\n当前余额: {user_points[uid]:.2f}")
        
        bot.delete_message(chat_id, wait_msg.message_id)
        bot.send_message(chat_id, result)
    except Exception as e:
        bot.edit_message_text(f"❌ 核验异常: {str(e)}", chat_id, wait_msg.message_id)

def run_sms_task(chat_id, phone, uid):
    try:
        sms_list.attack(phone) 
        user_points[uid] -= 3.5
        save_points()
        bot.send_message(chat_id, f"✅ 短信测压任务完成\n目标：{phone}\n已扣除 3.5 积分！")
    except Exception as e:
        bot.send_message(chat_id, f"❌ 短信任务失败: {str(e)}")

def cp_query_logic(chat_id, car_no, uid):
    url = f"http://zgzapi.idc.cn.com/车档.php?key=体验卡&cph={urllib.parse.quote(car_no)}"
    try:
        response = requests.get(url, timeout=15)
        response.encoding = 'utf-8'
        raw_res = response.text.strip()
        if raw_res and "未找到" not in raw_res and "错误" not in raw_res:
            user_points[uid] -= 2.5; save_points()
            message = (f"🚗 车牌查询结果:\n\n车牌号：{car_no}\n详细信息：\n{raw_res}\n\n已扣除 2.5 积分！\n当前余额: {user_points[uid]:.2f}")
        else:
            message = (f"🚗 车牌查询结果:\n\n未匹配到有效车档信息。\n\n查询无结果，未扣除积分。\n当前余额: {user_points[uid]:.2f}")
        bot.send_message(chat_id, message)
    except Exception as e: bot.send_message(chat_id, f"⚠️ 车档接口异常: {str(e)}")

def xiaowunb_query_logic(chat_id, id_number, uid):
    base_url = "http://xiaowunb.top/cyh.php"
    params = {"sfz": id_number}
    try:
        response = requests.get(base_url, params=params, timeout=10)
        response.encoding = 'utf-8'
        raw_text = response.text.strip()
        phones = re.findall(r'1[3-9]\d{9}', raw_text)
        if phones:
            user_points[uid] -= 1.5; save_points()
            unique_phones = list(dict.fromkeys(phones))
            phone_list_str = "".join([f"{idx}、{p}\n" for idx, p in enumerate(unique_phones, 1)])
            result_body = f"匹配到 {len(unique_phones)} 个有效手机号:\n{phone_list_str}"
            cost_str = "已扣除 1.5 积分！"
        else:
            result_body = "未匹配到有效手机号\n"; cost_str = "查询无结果，未扣除积分。"
        bot.send_message(chat_id, f"身份证查询结果:\n\n{result_body}\n{cost_str}\n当前余额: {user_points[uid]:.2f}")
    except Exception as e: bot.send_message(chat_id, f"❌ 接口请求失败: {e}")

def query_3ys_logic(chat_id, name, id_card, phone, uid):
    url = "http://xiaowunb.top/3ys.php"
    params = {"name": name, "sfz": id_card, "sjh": phone}
    try:
        response = requests.get(url, params=params, timeout=15)
        response.encoding = 'utf-8'
        user_points[uid] -= 0.05; save_points()
        clean_res = re.sub(r'小无 API.*?官方客服:@\w+', '', response.text.strip(), flags=re.DOTALL).strip()
        res_status = "三要素核验成功✅" if ("成功" in clean_res or "一致" in clean_res) else "三要素核验失败❌"
        bot.send_message(chat_id, f"名字：{name}\n手机号：{phone}\n身份证：{id_card}\n结果：{res_status}\n\n已扣除 0.05 积分！\n当前余额：{user_points[uid]:.2f}")
    except Exception as e: bot.send_message(chat_id, f"⚠️ 系统异常: {str(e)}")

def single_verify_2ys(chat_id, name, id_card, uid):
    url = "https://api.xhmxb.com/wxma/moblie/wx/v1/realAuthToken"
    headers = {"Authorization": AUTH_BEARER, "Content-Type": "application/json", "User-Agent": "Mozilla/5.0", "Referer": "https://servicewechat.com/wxf5fd02d10dbb21d2/59/page-frame.html"}
    try:
        r = requests.post(url, headers=headers, json={"name": name, "idCardNo": id_card}, timeout=10)
        user_points[uid] -= 0.01; save_points()
        res_type = "二要素核验一致✅" if r.json().get("success") else "二要素验证失败 ❌"
        bot.send_message(chat_id, f"姓名: **{name}**\n身份证: **{id_card}**\n结果: **{res_type}**\n\n已扣除 **0.01** 积分！\n当前余额：**{user_points[uid]:.2f}**", parse_mode='Markdown')
    except Exception as e: bot.send_message(chat_id, f"❌ 接口失败: {str(e)}")

# ================= 4. UI 菜单 (保持不变) =================

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
    return (f"Admin@铭\n\n用户 ID: `{uid}`\n用户名称: `{first_name}`\n当前余额: `{pts:.2f}积分`\n\n使用帮助可查看使用教程\n在线充值可支持24小时\n1 USDT = 1 积分")

# ================= 5. 消息处理 (保持不变) =================

@bot.message_handler(commands=['start', 'rlhy', 'cyh', '3ys', '2ys', 'cp', 'add', 'sms'])
def handle_commands(message):
    uid, chat_id = message.from_user.id, message.chat.id
    cmd_parts = message.text.split()
    cmd = cmd_parts[0][1:]
    
    if cmd == 'start':
        if uid not in user_points: user_points[uid] = 0.0
        bot.send_message(chat_id, get_main_text(message, uid, user_points[uid]), parse_mode='Markdown', reply_markup=get_main_markup())
    elif cmd == 'rlhy':
        if user_points.get(uid, 0.0) < 0.1: return bot.reply_to(message, "❌ 积分不足(0.1)")
        user_states[chat_id] = {'step': 'awaiting_rlhy'}
        bot.send_message(chat_id, "请输入：姓名 身份证 并添加一张人脸图片一起发送。")
    elif cmd == 'sms':
        if len(cmd_parts) < 2: return bot.reply_to(message, "请输入格式：/sms 手机号")
        if user_points.get(uid, 0.0) < 3.5: return bot.reply_to(message, "❌ 积分不足(3.5)")
        bot.send_message(chat_id, "🚀 测压指令已下达，正在启动...")
        threading.Thread(target=run_sms_task, args=(chat_id, cmd_parts[1], uid)).start()
    elif cmd == '2ys':
        bot.send_message(chat_id, "请输入：姓名 身份证")
        user_states[chat_id] = {'step': 'v_2ys'}
    elif cmd == '3ys':
        bot.send_message(chat_id, "请输入：姓名 身份证 手机号")
        user_states[chat_id] = {'step': 'v_3ys'}
    elif cmd == 'cyh':
        if user_points.get(uid, 0.0) < 1.5: return bot.reply_to(message, "积分不足")
        user_states[chat_id] = {'step': 'cyh_id'}; bot.send_message(chat_id, "请输入要查询的身份证号：")
    elif cmd == 'cp':
        if user_points.get(uid, 0.0) < 2.5: return bot.reply_to(message, "积分不足")
        user_states[chat_id] = {'step': 'v_cp'}; bot.send_message(chat_id, "请输入车牌号：")
    elif cmd == 'add' and uid == ADMIN_ID:
        try:
            user_points[int(cmd_parts[1])] = user_points.get(int(cmd_parts[1]), 0.0) + float(cmd_parts[2]); save_points()
            bot.reply_to(message, "✅ 充值成功")
        except: pass

@bot.message_handler(content_types=['photo'])
def handle_photo(message):
    uid, chat_id = message.from_user.id, message.chat.id
    caption = message.caption.strip() if message.caption else ""
    parts = re.split(r'[,，\s\n]+', caption)
    
    if (user_states.get(chat_id, {}).get('step') == 'awaiting_rlhy') or len(parts) >= 2:
        if len(parts) < 2: return bot.reply_to(message, "⚠️ 请在发送图片备注中输入：姓名 身份证")
        if user_points.get(uid, 0.0) < 0.1: return bot.reply_to(message, "❌ 积分不足(0.1)")
        if chat_id in user_states: del user_states[chat_id]
        threading.Thread(target=process_rlhy, args=(chat_id, parts[0], parts[1], message.photo[-1].file_id, uid)).start()

@bot.message_handler(func=lambda m: True)
def handle_all_text(message):
    uid, chat_id, text = message.from_user.id, message.chat.id, message.text.strip()
    if text.startswith('/'): return

    state = user_states.get(chat_id, {})
    # 处理 2要素/3要素 的手动输入状态
    if state.get('step') == 'v_2ys':
        parts = re.split(r'[,，\s\n]+', text)
        if len(parts) >= 2:
            del user_states[chat_id]
            return single_verify_2ys(chat_id, parts[0], parts[1], uid)
    elif state.get('step') == 'v_3ys':
        parts = re.split(r'[,，\s\n]+', text)
        if len(parts) >= 3:
            del user_states[chat_id]
            return query_3ys_logic(chat_id, parts[0], parts[1], parts[2], uid)
    elif state.get('step') == 'v_cp':
        del user_states[chat_id]; return cp_query_logic(chat_id, text.upper(), uid)
    elif state.get('step') == 'cyh_id':
        del user_states[chat_id]; return xiaowunb_query_logic(chat_id, text, uid)

    # 自动识别
    if re.match(r'^[京津沪渝冀豫云辽黑湖南皖鲁新苏浙赣鄂桂甘晋蒙陕吉闽贵粤青藏川宁琼]{1}[A-Z]{1}[A-Z0-9]{5,6}$', text.upper()):
        if user_points.get(uid, 0.0) < 2.5: return bot.reply_to(message, "积分不足")
        return cp_query_logic(chat_id, text.upper(), uid)

    parts = re.split(r'[,，\s\n]+', text)
    if len(parts) >= 3:
        n, p, i = None, None, None
        for x in parts:
            if not n and re.match(r'^[\u4e00-\u9fa5]{2,4}$', x): n = x
            elif not p and re.match(r'^1[3-9]\d{9}$', x): p = x
            elif not i and re.match(r'^[\dXx]{15}$|^[\dXx]{18}$', x): i = x.upper()
        if n and p and i:
            if user_points.get(uid, 0.0) < 0.05: return bot.reply_to(message, "积分不足")
            return query_3ys_logic(chat_id, n, i, p, uid)

    if len(parts) == 2:
        n, i = None, None
        for x in parts:
            if not n and re.match(r'^[\u4e00-\u9fa5]{2,4}$', x): n = x
            elif not i and re.match(r'^[\dXx]{15}$|^[\dXx]{18}$', x): i = x.upper()
        if n and i:
            if user_points.get(uid, 0.0) < 0.01: return bot.reply_to(message, "积分不足")
            return single_verify_2ys(chat_id, n, i, uid)

    if re.match(r'^\d{17}[\dXx]$|^\d{15}$', text):
        if user_points.get(uid, 0.0) < 1.5: return bot.reply_to(message, "积分不足")
        return xiaowunb_query_logic(chat_id, text, uid)

# ================= 6. 回调处理 (保持不变) =================

@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    uid, pts = call.from_user.id, user_points.get(call.from_user.id, 0.0)
    if call.data == "view_help":
        help_text = (
            "🛠️️使用帮助\n"
            "短信测压\n"
            "发送 /sms 手机号\n"
            "每次消耗 3.5 积分\n"
            "——————————————————\n"
            "企业级人脸核验\n"
            "发送 /rlhy 先选择一张待核验的图片\n"
            "附带输入：姓名 身份证号\n"
            "每次核验扣除 0.1 积分\n"
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

# ================= 7. 启动入口 (双线程运行) =================

if __name__ == '__main__':
    # 启动 Flask API 线程
    flask_thread = threading.Thread(target=lambda: app.run(host='0.0.0.0', port=5000))
    flask_thread.daemon = True
    flask_thread.start()
    
    print("🚀 API 已启动 (端口 5000)")
    print("🤖 Bot 正在运行...")
    
    # 启动机器人主循环
    bot.infinity_polling(timeout=10)
