import os


BOT_API_TOKEN = os.environ['BOT_API_KEY']


MONGO_DB = {
    'host': os.environ['MONGODB_HOSTNAME'],
    'port': os.environ['MONGODB_PORT'],
    'username': os.environ['MONGODB_USERNAME'],
    'password': os.environ['MONGODB_PASSWORD'],
}
