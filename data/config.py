# api id, hash
API_ID = 19222150
API_HASH = "b6776f066dc9193e33a0929e44187c1e"

USE_TG_BOT = False  # True if you want use tg, else False
BOT_TOKEN = '283993:kdmioieiweikiokeocki4okew'  # API TOKEN get in @BotFather
CHAT_ID = '22803822'  # Your telegram id

ACC_DELAY = [5, 5400]

# тип прокси
PROXY_TYPE = "socks5"  # http/socks5

# папка с сессиями (не менять)
WORKDIR = "sessions/"

# использование прокси
USE_PROXY = True  # True/False

EXCLUDE_SESSIONS = ["deadrees", "ranker", "rimuru"]

# реф код, идет после startapp=
REF_CODE = 'f1087108725'

TASK_SLEEP = [10, 20]

PAINT_SLEEP = [2, 4]

MINI_SLEEP = [5, 9]


DO_PAINT = True
DO_UPGRADES = True
DO_TASKS = True

tasks = {"x:notcoin", "x:notpixel", "channel:notcoin", "channel:notpixel_channel", "makePixelAvatar", "paint20pixels",
         "jettonTask", "boinkTask", "pixelInNickname"}



max_limits = {"energyLimit": 7, "paintReward": 7, "reChargeSpeed": 9}
levels = {"energyLimit": {1: 5, 2: 100, 3: 200, 4: 300, 5: 400, 6: 10},
          "paintReward": {1: 5, 2: 100, 3: 200, 4: 300, 5: 500, 6: 600},
          "reChargeSpeed": {1: 5, 2: 100, 3: 200, 4: 300, 5: 400, 6: 500, 7: 600, 8: 700}}

BAD_RESPONSES = [500, 502, 504, 524]
