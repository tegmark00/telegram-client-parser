from telethon import TelegramClient, events
from aiohttp import web
import asyncio
import threading

import config


client = TelegramClient(config.api_sess_name,
                        config.api_id,
                        config.api_hash)

ignore_chats = [] # chats to ignore
keywords = ["слово", "ключ", "таргет"] # all words must be in lowercase

@client.on(events.NewMessage)
async def my_event_handler(event):

  chat_id = event.chat_id
  sender_id = event.sender_id

  text = event.message.message.lower() # get message text in lowercase
  message_id = event.message.id

  if chat_id not in ignore_chats: # check if we searching keywords in this chat
    if text and any(word in text for word in keywords): # check if message text matches search keywords

      target_chat = await client.get_entity(config.target_chat_id) # Group to send messages matched
      res = await client.forward_messages(target_chat, event.message) # forward message to target group

      # push link on the message in chat

      message_link = ''
      if str(chat_id)[:4] == '-100':
        message_link = str(chat_id)[4:] # slice supergroup id '-100'
        message_link = config.link_template.\
                                            replace("{{chat_id}}", message_link).\
                                            replace('{{message_id}}', str(message_id))

      if message_link:
        await res.reply(message_link)

'''
WEB
'''

routes = web.RouteTableDef()

@routes.get('/')
async def hello(request):
    return web.Response(text="Hello, world")


app = web.Application()
app.add_routes(routes)
runner = web.AppRunner(app)

loop = asyncio.get_event_loop()


async def start() -> None:
    await client.start()
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', 5000)
    await site.start()


async def stop() -> None:
    await runner.cleanup()
    await client.disconnect()


loop.run_until_complete(start())
print("========== Initialization complete ==========")
print(f"Listening at http://")
print(f"Public URL prefix is")
print("(Press CTRL+C to quit)")
try:
    loop.run_forever()
except KeyboardInterrupt:
    loop.run_until_complete(stop())
except Exception:
    print("Fatal error in event loop")
    raise