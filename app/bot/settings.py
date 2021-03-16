import os


API_TOKEN = os.environ['BOT_API_TOKEN']

MONGODB = {
    'host': os.environ['MONGODB_HOSTNAME'],
    'port': os.environ['MONGODB_PORT'],
    'username': os.environ['MONGODB_USERNAME'],
    'password': os.environ['MONGODB_PASSWORD']
}
