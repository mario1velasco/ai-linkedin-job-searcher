# ! Un solo archivo lee el entorno; el resto importa de aqui
import os

from dotenv import load_dotenv

load_dotenv()

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
CLIENT_ID = os.getenv("CLIENT_ID")
CLIENT_SECRET = os.getenv("CLIENT_SECRET")
REDIRECT_URI = os.getenv("REDIRECT_URI")
LI_AT_COOKIE = os.getenv("LI_AT_COOKIE")
JSESSIONID = os.getenv("JSESSIONID")
FOUNDRY_API_KEY = os.getenv("FOUNDRY_API_KEY")
