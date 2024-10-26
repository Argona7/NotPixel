from urllib.parse import unquote
from pyrogram import Client
from data import config
from utils.core import logger
from curl_cffi.requests import AsyncSession
from pyrogram.raw.functions.messages import RequestAppWebView
from pyrogram.raw.types import InputBotAppShortName
from PIL import Image
from io import BytesIO
from time import time
import asyncio
import random
from utils import helpers
from utils import headers
import json
from multiprocessing import Manager

class NotPixel:

    def __init__(self, thread: int, account: str, proxy=None):
        self.ws_task = None
        self.session_id = None
        self.app_user = None
        self.user_info = None
        self.token = None
        self.auth_url = None
        self.global_map = Manager().dict()
        self.thread = thread
        self.name = account
        self.ref = config.REF_CODE
        if proxy:
            proxy_client = {
                "scheme": config.PROXY_TYPE,
                "hostname": proxy.split(':')[0],
                "port": int(proxy.split(':')[1]),
                "username": proxy.split(':')[2],
                "password": proxy.split(':')[3],
            }
            self.client = Client(name=account, 
                                 api_id=config.API_ID, 
                                 api_hash=config.API_HASH, 
                                 workdir=config.WORKDIR,
                                 proxy=proxy_client)
        else:
            self.client = Client(name=account, 
                                 api_id=config.API_ID, 
                                 api_hash=config.API_HASH, 
                                 workdir=config.WORKDIR)

        if proxy:
            self.proxy = {
                "http": f"{config.PROXY_TYPE}://{proxy.split(':')[2]}:{proxy.split(':')[3]}@{proxy.split(':')[0]}:{proxy.split(':')[1]}",
                "https": f"{config.PROXY_TYPE}://{proxy.split(':')[2]}:{proxy.split(':')[3]}@{proxy.split(':')[0]}:{proxy.split(':')[1]}"
            }
        else:
            self.proxy = None

        self.auth_token = ""

    async def create_session(self, impersonate):
        return AsyncSession(headers=headers.APP_HEADERS, 
                            impersonate=impersonate, 
                            verify=False, 
                            proxies=self.proxy)
    
    async def create_analytics_session(self, impersonate):
        content = random.choice(headers.CONTENT_DATA)
        session = AsyncSession(headers=headers.ANALYTICS_HEADERS, 
                               impersonate=impersonate, 
                               verify=False, 
                               proxies=self.proxy)
        session.headers['Content'] = content
        return session

    async def create_ws_session(self, impersonate):
        ws_key = helpers.generate_sec_websocket_key()
        session = AsyncSession(headers=headers.WS_HEADERS,
                               impersonate=impersonate,
                               verify=False,
                               proxies=self.proxy)
        session.headers['Sec-Websocket-Key'] = ws_key
        return session
    
    async def main(self):
        await asyncio.sleep(random.randint(*config.ACC_DELAY))
        while True:
            try:
                impersonate = random.choice(config.FINGERPRINTS)
                self.session = await self.create_session(impersonate)
                self.analytics_session = await self.create_analytics_session(impersonate)
                self.ws_session = await self.create_ws_session(impersonate)
                try:
                    login = await self.login()
                    if not login:
                        raise Exception("Failed to log in!")
                    logger.info(f"main | Thread {self.thread} | {self.name} | Start! | PROXY : {self.session.proxies['https'] if self.proxy else 'No Proxy'}")
                except Exception as err:
                    logger.error(f"main | Thread {self.thread} | {self.name} | {err}")
                    await asyncio.sleep(random.uniform(300, 450))
                    await self.session.close()
                    if self.ws_task:
                        self.ws_task.cancel()
                    continue

                status = await self.status()
                while True:
                    template_info = await self.my() # информация о выбранном шаблоне
                    if template_info == {} or not template_info: # если шаблон не установлен , происходит его установка
                        await self.event({"n": "pageview", "u": "https://app.notpx.app/template", "d": "notpx.app",
                                        "r": None})

                        templates_1 = await self.list(0)
                        await asyncio.sleep(random.uniform(2, 4))
                        templates_2 = await self.list(12)
                        await asyncio.sleep(random.uniform(2, 4))
                        templates_3 = await self.list(24)
                        if templates_1 and templates_2 and templates_3:
                            templates = [*templates_1, *templates_2, *templates_3]
                            template_id = random.choice([i["templateId"] for i in templates])
                            await asyncio.sleep(random.uniform(3, 5))
                            await self.choose_template(template_id)
                            logger.success(f"main | Thread {self.thread} | {self.name} | Template installed!")
                            continue
                        raise Exception("Template installation failed")
                    else:
                        break

                template_image = await self.get_template(template_info['id']) # изображение шаблона
                await asyncio.sleep(random.uniform(*config.MINI_SLEEP))
                if config.DO_PAINT:
                    if template_info and template_image and status and self.global_map:
                        x_cord = template_info['x']
                        y_cord = template_info['y']
                        size = template_info['imageSize']

                        charges = status["charges"]
                        y_cord_list = list(range(y_cord, y_cord + size))
                        while charges > 0:
                            if not y_cord_list:
                                raise Exception("Template already full painted")

                            # Выбираем цвет преимущественно либо в начале, либо в конце мапы
                            weights = [2 if i < 15 or i >= size - 15 else 1 for i in range(len(y_cord_list))]
                            y = random.choices(y_cord_list, weights=weights, k=1)[0]
                            y_cord_list.remove(y)

                            for x in range(x_cord, x_cord + size):
                                if charges == 0:
                                    break
                                global_map_color = self.global_map.get((x, y))
                                template_map_color = template_image.get((x - x_cord, y - y_cord))
                                # Если цвет на глобальной карте не совпадает с шаблоном происходит закрашивание пикселя
                                if global_map_color and global_map_color != template_map_color:
                                    cord = y * 1000 + x
                                    paint = await self.paint(cord, template_map_color)
                                    if paint:
                                        charges -= 1
                                        await asyncio.sleep(random.uniform(*config.PAINT_SLEEP))
                await asyncio.sleep(random.uniform(*config.MINI_SLEEP))
                if await self.event({"n": "pageview", "u": "https://app.notpx.app/claiming", "d": "notpx.app",
                                     "r": None}):

                    await asyncio.sleep(random.uniform(3, 5))
                    await self.farming_claim()

                    if config.DO_TASKS:
                        status = await self.status()
                        if status:
                            user_tasks = status["tasks"]
                            for task in config.tasks:
                                if task not in user_tasks.keys():
                                    await self.analytics_event('app-hide')
                                    if task.startswith("x:"):
                                        await asyncio.sleep(random.uniform(*config.TASK_SLEEP))
                                        await self.do_task(task.split(":")[1], "x")
                                    elif task.startswith("channel:"):
                                        await self.client.connect()
                                        await self.client.join_chat(task.split(":")[1])
                                        await self.client.disconnect()
                                        await asyncio.sleep(random.uniform(*config.TASK_SLEEP))
                                        await self.do_task(task.split(":")[1], "channel")
                                    else:
                                        await asyncio.sleep(random.uniform(*config.TASK_SLEEP))
                                        await self.do_task(task)

                            leagues = ["leagueBonusSilver", "leagueBonusGold", "leagueBonusPlatinum"]
                            for league in leagues:
                                if league not in user_tasks.keys():
                                    await asyncio.sleep(random.uniform(*config.TASK_SLEEP))
                                    await self.do_task(league)
                                    break

                    await asyncio.sleep(random.uniform(*config.MINI_SLEEP))
                    if config.DO_UPGRADES:
                        await self.upgrade_skills()

                    await self.event({"n": "pageview", "u": "https://app.notpx.app/", "d": "notpx.app",
                                      "r": None})

                status = await self.status()
                if status:
                    sleep_time = (status["maxCharges"] - status["charges"]) * (
                            status["reChargeSpeed"] // 1000) + random.randint(100, 600)
                    logger.info(f"main | Thread {self.thread} | {self.name} | КРУГ ОКОНЧЕН! Ожидание: {sleep_time}")
                    await self.session.close()
                    self.ws_task.cancel()
                    await asyncio.sleep(sleep_time)
                else:
                    raise Exception("Неудалось продолжить играть")

            except Exception as err:
                logger.error(f"main | Thread {self.thread} | {self.name} | {err}")
                await asyncio.sleep(random.uniform(300, 450))
                await self.session.close()
                if self.ws_task:
                    self.ws_task.cancel()
                continue

    async def paint(self, pixel_id: int, color: str):
        body = {"pixelId": pixel_id, "newColor": color}
        response = await self.session.post("https://notpx.app/api/v1/repaint/start", json=body)
        if response.status_code not in config.BAD_RESPONSES:
            response = response.json()
            if "balance" in response:
                logger.success(
                    f'paint | Thread {self.thread} | {self.name} | paint successfully: {response["balance"]} : {pixel_id}')
                return True
        return False

    async def upgrade_skills(self):
        status = await self.status()
        balance = int(status["userBalance"])
        boosts = status["boosts"]

        for key, value in boosts.items():
            if config.max_limits[key] > value:
                if balance >= config.levels[key][value]:
                    resp = await self.upgrade(key)
                    if resp:
                        balance = balance - config.levels[key][value]
                    await asyncio.sleep(random.uniform(*config.MINI_SLEEP))

    async def upgrade(self, type_upgrade: str):
        response = await self.session.get(f"https://notpx.app/api/v1/mining/boost/check/{type_upgrade}")
        if response.status_code not in config.BAD_RESPONSES:
            response = response.json()
            if "error" in response:
                logger.warning(f'upgrade | Thread {self.thread} | {self.name} | {response["error"]}')
                return False
            if response[type_upgrade] is True:
                logger.success(f'upgrade | Thread {self.thread} | {self.name} | Successfully upgraded : {type_upgrade}')
                return True
        return False

    async def farming_claim(self):
        response = await self.session.get("https://notpx.app/api/v1/mining/claim")
        if response.status_code == 200:
            logger.success(f'farming claim | Thread {self.thread} | {self.name} | farming reward claimed successfully!')
            return True
        return False

    async def do_task(self, task_name, type_task=None):
        if not type_task:
            response = await self.session.get(f"https://notpx.app/api/v1/mining/task/check/{task_name}")
            if response.status_code not in config.BAD_RESPONSES:
                response = response.json()
                if task_name in response and response[task_name] is True:
                    logger.success(f'task | Thread {self.thread} | {self.name} | Task completed: {task_name}')
                    return True
            return False
        params = {"name": task_name}
        response = await self.session.get(f"https://notpx.app/api/v1/mining/task/check/{type_task}", params=params)
        if response.status_code not in config.BAD_RESPONSES:
            response = response.json()
            task = f"{type_task}:{task_name}"
            if task in response and response[task] is True:
                logger.success(
                    f'task | Thread {self.thread} | {self.name} | Task completed: {task_name} {type_task}')
                return True
        return False

    async def choose_template(self, template_id):
        await self.session.get(f"https://notpx.app/api/v1/image/template/{template_id}")
        response = await self.session.put(f"https://notpx.app/api/v1/image/template/subscribe/{template_id}")
        await self.session.get(f"https://notpx.app/api/v1/image/template/{template_id}")
        if response.status_code == 204:
            return True
        return False

    async def get_template(self, template_id):
        del self.session.headers['authorization']
        params = {"time": str(int(time() * 1000))}
        response = await self.session.get(f"https://static.notpx.app/templates/{template_id}.png", params=params)
        self.session.headers['authorization'] = self.token
        if response.status_code == 200:
            image = Image.open(BytesIO(response.content))
            return helpers.image_to_matrix(image)

        return False

    async def get_global_map(self):
        del self.session.headers['authorization']
        response = await self.session.get(f"https://image.notpx.app/api/v2/image")
        self.session.headers['authorization'] = self.token
        if response.status_code == 200:
            image = Image.open(BytesIO(response.content))
            return helpers.image_to_matrix(image)

        return False

    async def event(self, body):
        if 'authorization' in self.session.headers:
            del self.session.headers['authorization']
        response = await self.session.post("https://plausible.joincommunity.xyz/api/event", json=body)
        self.session.headers['authorization'] = self.token
        if response.status_code == 202:
            return True
        return False
    
    async def analytics_event(self, event_name: str):
        timestamp = int(time() * 1000)
        event_data = {
            "event_name": event_name,
            "session_id": self.session_id,
            "user_id": self.user_info.id,
            "app_name": "NotPixel",
            "is_premium": self.user_info.is_premium,
            "platform": "android",
            "locale": 'ru',
            "client_timestamp": timestamp
        }
        await self.analytics_session.post("https://tganalytics.xyz/events", json=event_data)

    async def my(self):
        response = await self.session.get("https://notpx.app/api/v1/image/template/my")
        if response.status_code == 200:
            return response.json()
        if response.status_code == 404 and (response.json())["error"] == "not found":
            return {}
        return False

    async def me(self):
        response = await self.session.get("https://notpx.app/api/v1/users/me")
        if response.status_code == 200:
            return response.json()
        return False

    async def status(self):
        response = await self.session.get("https://notpx.app/api/v1/mining/status")
        if response.status_code == 200:
            return response.json()
        return False

    async def list(self, offset):
        params = {"limit": "12", "offset": str(offset)}
        response = await self.session.get("https://notpx.app/api/v1/image/template/list", params=params)
        if response.status_code == 200:
            return response.json()
        return False
    
    async def get_tg_web_data(self):
        async with self.client:
            try:
                web_view = await self.client.invoke(RequestAppWebView(
                    peer=await self.client.resolve_peer('notpixel'),
                    app=InputBotAppShortName(bot_id=await self.client.resolve_peer('notpixel'), short_name="app"),
                    platform='android',
                    write_allowed=True,
                    start_param=self.ref
                ))

                self.auth_url = web_view.url
                self.user_info = await self.client.get_me()
                self.session_id = helpers.generate_session_id()
            except Exception as err:
                logger.error(f"main | Thread {self.thread} | {self.name} | {err}")
                if 'USER_DEACTIVATED_BAN' in str(err):
                    logger.error(f"login | Thread {self.thread} | {self.name} | USER BANNED")
                    await self.client.disconnect()
                    return False
            return unquote(string=self.auth_url.split('tgWebAppData=')[1].split('&tgWebAppVersion')[0])

    async def login(self):
        try:
            tg_web_data = await self.get_tg_web_data()
            if tg_web_data is False:
                return False
            self.token = f"initData {tg_web_data}"
            self.session.headers['authorization'] = self.token
            await self.event({"n": "pageview", "u": self.auth_url, "d": "notpx.app",
                              "r": None})
            self.app_user = await self.me()
            if not self.app_user:
                return False
            await self.analytics_event('app-init')
            self.global_map = await self.get_global_map()
            self.ws_task = asyncio.create_task(self.receive_ws())
            return True
        except Exception as err:
            logger.error(f"login | Thread {self.thread} | {self.name} | {err}")
            return False

    async def receive_ws(self):
        while True:
            ws_token = self.app_user['websocketToken']
            socket = await self.ws_session.ws_connect('wss://notpx.app/connection/websocket')
            auth_request = b'\xcb\x01\x08\x01"\xc6\x01\n\xbf\x01' + ws_token.encode('utf-8') + b'"\x02js'
            await asyncio.to_thread(socket.send, auth_request)
            logger.success(f'task | Thread {self.thread} | {self.name} | Websocket connected succesfully')
            while True:
                msg, _ = await asyncio.to_thread(socket.recv)
                # ping
                if msg == b"\x00":
                    # pong
                    await asyncio.to_thread(socket.send, b"\x00")
                    continue
                replies = helpers.decode_protobuf(msg)
                for reply in replies:
                    # Update pixels
                    if reply.push and reply.push.channel == 'pixel:message':
                        # Декопрессим DEFLATE содержимое
                        decompress_data = helpers.decompress_data(reply.push.pub.data)
                        updates = json.loads(decompress_data.decode('utf-8'))
                        for color, cords in updates.items():
                            for cord in cords:
                                x = cord % 1000
                                y = cord // 1000
                                self.global_map[(x, y)] = f'#{color}'