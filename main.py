from telethon import TelegramClient, events
from aiohttp import web
import re
import asyncio
import logging

import config


logging.basicConfig(level=logging.INFO)


def load_keywords():
  with open(config.keywords_file, 'r') as file:
    data = file.read()
  return data.lower().strip().split(', ')


async def save_keywords(keywords):
  with open(config.keywords_file, 'w') as file:
    file.write(config.joiner.join(keywords).lower().strip())
  return


keywords = load_keywords() # list with keywords to search in messages

client = TelegramClient(config.api_sess_name,
                        config.api_id,
                        config.api_hash)


@client.on(events.NewMessage(func=lambda event: not event.is_private)) # do not search in private messages
async def my_event_handler(event):

  global keywords

  chat_id = event.chat_id
  sender_id = event.sender_id
  message_id = event.message.id

  text = event.message.message # get message text
  word_list = re.sub("[^a-zа-яёїієґ0-9_-]", " ",  text.lower()).split() # string to list of words

  if chat_id not in config.ignore_chats: # check if we searching keywords in this chat
    if any(word in word_list for word in keywords): # check if message text matches search keywords

      logging.info(f'[PARSER]: match new message chat_id: {chat_id}, sender_id: {sender_id}, text: {text}')

      target_chat = await client.get_entity(config.target_chat_id) # Group to send messages matched
      res = await client.forward_messages(target_chat, event.message) # forward message to target group

      # push link on the message in chat

      message_link = ''
      if str(chat_id)[:4] == '-100':
        message_link = str(chat_id)[4:] # slice supergroup id '-100'
        message_link = config.link_template.\
                                            replace("{{chat_id}}", message_link).\
                                            replace('{{message_id}}', str(message_id))

      if res and message_link:
        await res.reply(message_link)


'''
WEB
'''

routes = web.RouteTableDef()

@routes.get('/')
async def index(request):

  logging.info('[WEB]: access /')

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

  await save_keywords(new_keywords) # save changes to file
  keywords = new_keywords # update current var with keywords

  logging.info('[WEB]: access /save')
  logging.info(f'[WEB]: Keywords updated: {keywords}')

  raise web.HTTPFound('/')


async def start() -> None:
    await client.start()
    await runner.setup()
    site = web.TCPSite(runner, config.host, config.port)
    await site.start()


async def stop() -> None:
    await runner.cleanup()
    await client.disconnect()


app = web.Application()
app.add_routes(routes)
runner = web.AppRunner(app)

loop = asyncio.get_event_loop()

loop.run_until_complete(start())
logging.info("========== Initialization complete ==========")
logging.info(f"Listening at http://{config.host}:{config.port}")
logging.info(f"Public URL prefix is {config.public_url}")
logging.info(f"Current keywords: {keywords}")
logging.info("(Press CTRL+C to quit)")

try:
    loop.run_forever()
except KeyboardInterrupt:
    loop.run_until_complete(stop())
except Exception as e:
    logging.critical("Fatal error in event loop")
    logging.critical(str(e))
    raise