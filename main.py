from telethon import TelegramClient, events
from aiohttp import web
import asyncio
import threading

import config


def load_keywords():
  with open(config.keywords_file, 'r') as file:
    data = file.read()
  return data.lower().strip().split(', ')


def save_keywords(keywords):
  with open(config.keywords_file, 'w') as file:
    file.write(config.joiner.join(keywords).lower().strip())
  return


keywords = load_keywords() # list with keywords to search in messages

client = TelegramClient(config.api_sess_name,
                        config.api_id,
                        config.api_hash)


@client.on(events.NewMessage)
async def my_event_handler(event):

  global keywords

  chat_id = event.chat_id
  sender_id = event.sender_id

  text = event.message.message.lower() # get message text in lowercase
  message_id = event.message.id

  if chat_id not in config.ignore_chats: # check if we searching keywords in this chat
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
async def index(request):

  global keywords

  with open('index.html', 'r') as file:
    html = file.read()
  html = html.replace("{{keywords}}", config.joiner.join(keywords))

  return web.Response(text=html, content_type='text/html')


@routes.post('/save')
async def save(request):

  global keywords

  form = await request.post()

  new_keywords = form.get('keywords', "")
  new_keywords = new_keywords.split(config.joiner)

  save_keywords(new_keywords)
  keywords = new_keywords
  
  raise web.HTTPFound('/')


app = web.Application()
app.add_routes(routes)
runner = web.AppRunner(app)

loop = asyncio.get_event_loop()


async def start() -> None:
    await client.start()
    await runner.setup()
    site = web.TCPSite(runner, config.host, config.port)
    await site.start()


async def stop() -> None:
    await runner.cleanup()
    await client.disconnect()


loop.run_until_complete(start())
print("========== Initialization complete ==========")
print("========== Initialization complete ==========")
print(f"Listening at http://{config.host}:{config.port}")
print(f"Public URL prefix is {config.public_url}")
print("(Press CTRL+C to quit)")

try:
    loop.run_forever()
except KeyboardInterrupt:
    loop.run_until_complete(stop())
except Exception as e:
    print("Fatal error in event loop")
    print(str(e))
    raise