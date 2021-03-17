import gspread_asyncio
from oauth2client.service_account import ServiceAccountCredentials


def get_creds():
    # To obtain a service account JSON file, follow these steps:
    # https://gspread.readthedocs.io/en/latest/oauth2.html
    # for-bots-using-service-account
    return ServiceAccountCredentials.from_json_keyfile_name(
        "service_account_credentials.json",
        [
            "https://spreadsheets.google.com/feeds",
            "https://www.googleapis.com/auth/drive",
            "https://www.googleapis.com/auth/spreadsheets",
        ],
    )


client = gspread_asyncio.AsyncioGspreadClientManager(get_creds())
