import tempfile
from config import settings
import os

def get_tmp_dir(trailing_slash=False):
    path = tempfile.gettempdir()
    return path+'/' if trailing_slash else path

def extract_env():
    return settings.DOMAIN.lower()

def extract_domain():
    env = os.environ.get("YOUR_ENV")  # integrationservice
    url = settings.DOMAIN + env
    if settings.ENV_FOR_DYNACONF.upper() == "DEVELOPMENT":
        return f"http://localhost:8000"
    return f"https://{url}.sentieo.com"

    # return f"http://localhost:8000"

def fetchCookies(request):
    cookies = {
        "apid": request.cookies.get("apid"),
        "usid": request.cookies.get("usid"),
        "csrftoken": request.cookies.get("csrftoken"),
    }
    return cookies

def divide_chunks(l, n):

    # looping till length l
    for i in range(0, len(l), n):
        yield l[i:i + n]