import os
from dotenv import load_dotenv


load_dotenv()

BOT_TOKEN = str(os.getenv("BOT_TOKEN"))

trello_key = str(os.getenv("trello_key"))
trello_secret = str(os.getenv("trello_secret"))

admins = [
    os.getenv("ADMIN_ID"),
]

ip = os.getenv("ip")

aiogram_redis = {
    'host': ip,
}

redis = {
    'address': (ip, 6379),
    'encoding': 'utf8'
}