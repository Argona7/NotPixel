from urllib.parse import unquote
from pyrogram import Client
from data import config
from utils.core import logger

from aiohttp_socks import ProxyConnector
from pyrogram.raw.functions.messages import RequestAppWebView
from pyrogram.raw.types import InputBotAppShortName
from fake_useragent import UserAgent
from PIL import Image
from io import BytesIO
from time import time
from pathlib import Path

import os
import json
import aiofiles
import aiohttp
import asyncio
import random


class NotPixel:

    def __init__(self, thread: int, account: str, proxy=None):
        self.session = None
        self.UserAgent = None
        self.device = 'android'
        self.user_info = None
        self.token = None
        self.auth_url = None
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
            self.client = Client(name=account, api_id=config.API_ID, api_hash=config.API_HASH, workdir=config.WORKDIR,
                                 proxy=proxy_client)
        else:
            self.client = Client(name=account, api_id=config.API_ID, api_hash=config.API_HASH, workdir=config.WORKDIR)

        if proxy:
            self.proxy = f"{config.PROXY_TYPE}://{proxy.split(':')[2]}:{proxy.split(':')[3]}@{proxy.split(':')[0]}:{proxy.split(':')[1]}"
        else:
            self.proxy = None

        self.auth_token = ""

    async def create_session(self):
        connector = ProxyConnector.from_url(self.proxy) if self.proxy else aiohttp.TCPConnector(verify_ssl=False)
        browser_version = self.UserAgent.split("Chrome/")[1].split(".")[0]
        headers = {
            'accept': 'application/json, text/plain, */*',
            'accept-encoding': 'gzip, deflate, br, zstd',
            'content-type': 'text/plain',
            'pragma':'no-cache',
            'cache-control':'no-cache',
            'accept-language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
            'origin': 'https://app.notpx.app',
            'priority': 'u=1, i',
            'referer': 'https://app.notpx.app/',
            'sec-ch-ua': f'"Chromium";v="{browser_version}", "Not;A=Brand";v="24", "Google Chrome";v="{browser_version}"',
            'sec-ch-ua-mobile': '?1',
            'sec-ch-ua-platform': f'"{self.device}"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'cross-site',
            'user-agent': self.UserAgent
        }

        return aiohttp.ClientSession(headers=headers, trust_env=True, connector=connector)

    async def set_useragent(self):
        try:
            file_path = os.path.join(os.path.join(Path(__file__).parent.parent, "data"), "UserAgent.json")

            if not os.path.exists(file_path):
                data = {self.name: UserAgent(os=self.device).random}
                async with aiofiles.open(file_path, 'w', encoding="utf-8") as file:
                    await file.write(json.dumps(data, ensure_ascii=False, indent=4))

                self.UserAgent = data[self.name]
                return True

            else:
                try:
                    async with aiofiles.open(file_path, 'r', encoding='utf-8') as file:
                        content = await file.read()
                        data = json.loads(content)

                    if self.name in data:
                        self.UserAgent = data[self.name]
                        return True

                    else:
                        self.UserAgent = UserAgent(os=self.device).random
                        data[self.name] = self.UserAgent

                        async with aiofiles.open(file_path, 'w', encoding='utf-8') as file:
                            await file.write(json.dumps(data, ensure_ascii=False, indent=4))

                        return True
                except json.decoder.JSONDecodeError:
                    logger.error(f"useragent | Thread {self.thread} | {self.name} | syntax error in UserAgents json file!")
                    return False

        except Exception as err:
            logger.error(f"useragent | Thread {self.thread} | {self.name} | {err}")
            return False

    async def main(self):
        await asyncio.sleep(random.randint(*config.ACC_DELAY))
        while True:
            try:
                useragent = await self.set_useragent()
                if not useragent:
                    logger.error(f"UserAgent | Thread {self.thread} | {self.name} | Invalid User Agent!")
                    return 0
                self.session = await self.create_session()
                try:
                    login = await self.login()
                    if login is False:
                        raise Exception("Failed to log in!")
                    logger.info(f"main | Thread {self.thread} | {self.name} | Start! | PROXY : {self.proxy}")
                except Exception as err:
                    logger.error(f"main | Thread {self.thread} | {self.name} | {err}")
                    await asyncio.sleep(random.uniform(300, 450))
                    await self.session.close()
                    continue

                status = await self.status()
                await self.squad()
                template_info = await self.my()  # информация о выбранном шаблоне
                if template_info == {}:  # если шаблон не установлен , происходит его установка
                    await self.event({"n": "pageview", "u": "https://app.notpx.app/template", "d": "notpx.app",
                                      "r": "https://web.telegram.org/"})

                    templates_1 = await self.list(0)
                    if templates_1:
                        templates = [*templates_1]

                        template_id = random.choice([i["templateId"] for i in templates])
                        await asyncio.sleep(random.uniform(3, 5))
                        await self.choose_template(template_id)

                        logger.success(f"main | Thread {self.thread} | {self.name} | Template installed!")
                        await asyncio.sleep(random.uniform(150, 300))
                        await self.session.close()
                        continue

                    raise Exception("Template installation failed")

                elif template_info is False:
                    raise Exception("Failed to load the template")

                template_image = await self.get_template(template_info['id'])  # изображение шаблона
                await asyncio.sleep(random.uniform(*config.MINI_SLEEP))
                if config.DO_PAINT:
                    if template_info and template_image and status:
                        template_image = template_image.convert("RGB")
                        x_cord = template_info['x']
                        y_cord = template_info['y']
                        size = template_info['imageSize']

                        charges = status["charges"]
                        y_cord_list = list(range(y_cord, y_cord + size))
                        while charges > 0:
                            map_template = await self.get_map_template()  # изображение карты
                            map_template = map_template.convert("RGB")
                            if not map_template:
                                await asyncio.sleep(random.uniform(*config.MINI_SLEEP))
                                continue

                            if not y_cord_list:
                                raise Exception(
                                    f"Template already full painted: x_cord {x_cord} y_cord {y_cord}  size {size}")

                            weights = [2 if i < 15 or i >= size - 15 else 1 for i in range(
                                len(y_cord_list))]  # увеличиваем вероятность выбора координат в начале шаблона и в конце , т.к там меньше закрашиваний
                            y = random.choices(y_cord_list, weights=weights, k=1)[0]
                            y_cord_list.remove(y)

                            for x in range(x_cord, x_cord + size):
                                if charges == 0:
                                    break
                                if random.randint(0,
                                                  3) == 0:  # чем чаще будет обновляться карта , тем точнее будут закрашивания
                                    map_template_1 = await self.get_map_template()

                                    if map_template_1:
                                        map_template = map_template_1

                                map_template = map_template.convert("RGB")
                                r, g, b = map_template.getpixel((x, y))
                                hex_color_map = f"#{r:02X}{g:02X}{b:02X}"
                                r, g, b = template_image.getpixel((x - x_cord, y - y_cord))
                                hex_color_template = f"#{r:02X}{g:02X}{b:02X}"
                                if hex_color_map != hex_color_template:  # если цвет на шаблоне не совпадает с изначальным происходит закрашивание пикселя
                                    cord = y * 1000 + x
                                    color = hex_color_template
                                    paint = await self.paint(cord, color)
                                    if paint:
                                        charges -= 1
                                    await asyncio.sleep(random.uniform(*config.PAINT_SLEEP))

                await asyncio.sleep(random.uniform(*config.MINI_SLEEP))
                if await self.event({"n": "pageview", "u": "https://app.notpx.app/claiming", "d": "notpx.app",
                                     "r": "https://web.telegram.org/"}):

                    await asyncio.sleep(random.uniform(3, 5))
                    await self.farming_claim()

                    if config.DO_TASKS:
                        status = await self.status()
                        if status:
                            user_tasks = status["tasks"]
                            for task in config.tasks:
                                if task not in user_tasks.keys():
                                    if task.startswith("x:"):
                                        await asyncio.sleep(random.uniform(*config.TASK_SLEEP))
                                        await self.do_task(task.split(":")[1], "x")
                                    elif task.startswith("channel:"):
                                        await self.client.connect()
                                        await self.client.join_chat(task.split(":")[1])
                                        await self.client.disconnect()
                                        await asyncio.sleep(random.uniform(*config.TASK_SLEEP))
                                        await self.do_task(task.split(":")[1], "channel")
                                    elif task == "pixelInNickname":
                                        await self.client.connect()
                                        user = await self.client.get_me()
                                        user_name = user.first_name
                                        new_user_name = user_name + " ▪️"
                                        print(new_user_name)
                                        await self.client.update_profile(first_name=new_user_name)
                                        await self.client.disconnect()
                                        await asyncio.sleep(random.uniform(*config.TASK_SLEEP))
                                        await self.do_task(task)

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
                                      "r": "https://web.telegram.org/"})

                status = await self.status()
                if status:
                    add_delay = random.randint(1000, 1800) if random.randint(0, 4) == 0 else random.randint(100, 600)
                    sleep_time = (status["maxCharges"] - status["charges"]) * (
                            status["reChargeSpeed"] // 1000) + add_delay
                    logger.info(f"main | Thread {self.thread} | {self.name} | КРУГ ОКОНЧЕН! Ожидание: {sleep_time}")
                    await self.session.close()
                    await asyncio.sleep(sleep_time)
                else:
                    raise Exception("Неудалось продолжить играть")

            except Exception as err:
                logger.error(f"main | Thread {self.thread} | {self.name} | {err}")
                await asyncio.sleep(random.uniform(300, 450))
                await self.session.close()
                continue

    async def paint(self, pixel_id: int, color: str):
        body = {"pixelId": pixel_id, "newColor": color}
        body_json = json.dumps(body)
        content_length = str(len(body_json.encode('utf-8')))
        self.session.headers['content-length'] = content_length
        self.session.headers['content-type'] = 'application/json'
        response = await self.session.post("https://notpx.app/api/v1/repaint/start", json=body)
        del self.session.headers['content-length']
        del self.session.headers['content-type']
        if response.status not in config.BAD_RESPONSES:
            response = await response.json()
            if "balance" in response:
                logger.success(
                    f'paint | Thread {self.thread} | {self.name} | paint successfully: {response["balance"]}')
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
        if response.status not in config.BAD_RESPONSES:
            response = await response.json()
            if "error" in response:
                logger.warning(f'upgrade | Thread {self.thread} | {self.name} | {response["error"]}')
                return False
            if response[type_upgrade] is True:
                logger.success(f'upgrade | Thread {self.thread} | {self.name} | Successfully upgraded : {type_upgrade}')
                return True
        return False

    async def farming_claim(self):
        response = await self.session.get("https://notpx.app/api/v1/mining/claim")
        if response.status == 200:
            logger.success(f'farming claim | Thread {self.thread} | {self.name} | farming reward claimed successfully!')
            return True
        return False

    async def do_task(self, task_name, type_task=None):
        if not type_task:
            response = await self.session.get(f"https://notpx.app/api/v1/mining/task/check/{task_name}")
            if response.status not in config.BAD_RESPONSES:
                response = await response.json()
                if task_name in response and response[task_name] is True:
                    logger.success(f'task | Thread {self.thread} | {self.name} | Task completed: {task_name}')
                    return True
                elif task_name in response and response[task_name] is False:
                    logger.warning(
                        f'task | Thread {self.thread} | {self.name} | Failed to complete task: {task_name}')
                    return False
            return False
        params = {"name": task_name}
        response = await self.session.get(f"https://notpx.app/api/v1/mining/task/check/{type_task}", params=params)
        if response.status not in config.BAD_RESPONSES:
            response = await response.json()
            task = f"{type_task}:{task_name}"
            if task in response and response[task] is True:
                logger.success(
                    f'task | Thread {self.thread} | {self.name} | Task completed: {task_name} {type_task}')
                return True
            elif task in response and response[task] is False:
                logger.warning(
                    f'task | Thread {self.thread} | {self.name} | Failed to complete task: {task_name} {type_task}')
                return False
        return False

    async def choose_template(self, template_id):
        await self.session.get(f"https://notpx.app/api/v1/image/template/{template_id}")
        response = await self.session.put(f"https://notpx.app/api/v1/image/template/subscribe/{template_id}")
        await self.session.get(f"https://notpx.app/api/v1/image/template/{template_id}")
        await self.get_template(template_id)
        if response.status == 204:
            return True
        return False

    async def get_template(self, template_id):
        del self.session.headers['authorization']
        params = {"time": str(int(time() * 1000))}
        response = await self.session.get(f"https://static.notpx.app/templates/{template_id}.png", params=params)
        self.session.headers['authorization'] = self.token
        if response.status == 200:
            image_data = await response.read()
            image = Image.open(BytesIO(image_data))
            return image

        return False

    async def get_map_template(self):
        del self.session.headers['authorization']
        response = await self.session.get(f"https://image.notpx.app/api/v2/image")
        self.session.headers['authorization'] = self.token
        if response.status == 200:
            image_data = await response.read()
            image = Image.open(BytesIO(image_data))
            return image

        return False

    async def event(self, body):
        del self.session.headers['authorization']
        body_json = json.dumps(body)
        content_length = str(len(body_json.encode('utf-8')))
        self.session.headers['content-length'] = content_length
        response = await self.session.post("https://plausible.joincommunity.xyz/api/event", json=body)
        del self.session.headers['content-length']
        self.session.headers['authorization'] = self.token
        if response.status == 202:
            return True
        return False

    async def my(self):
        response = await self.session.get("https://notpx.app/api/v1/image/template/my")
        if response.status == 200:
            return await response.json()
        if response.status == 404 and (await response.json())["error"] == "not found":
            return {}
        return False

    async def me(self):
        response = await self.session.get("https://notpx.app/api/v1/users/me")
        if response.status == 200:
            return await response.json()
        return False

    async def status(self):
        response = await self.session.get("https://notpx.app/api/v1/mining/status")
        if response.status == 200:
            return await response.json()
        return False

    async def squad(self):
        response = await self.session.get("https://notpx.app/api/v1/ratings/squads/576576")
        if response.status == 200:
            return True
        return False

    async def list(self, offset):
        params = {"limit": "12", "offset": str(offset)}
        response = await self.session.get("https://notpx.app/api/v1/image/template/list", params=params)
        if response.status == 200:
            return await response.json()
        return False

    async def get_tg_web_data(self):
        async with self.client:
            try:
                web_view = await self.client.invoke(RequestAppWebView(
                    peer=await self.client.resolve_peer('notpixel'),
                    app=InputBotAppShortName(bot_id=await self.client.resolve_peer('notpixel'), short_name="app"),
                    platform=self.device,
                    write_allowed=True,
                    start_param=self.ref
                ))

                self.auth_url = web_view.url
                self.user_info = await self.client.get_me()
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
                              "r": "https://web.telegram.org/"})
            self.session.headers['sec-fetch-site'] = 'same-site'

            if not await self.me():
                return False
            return True
        except Exception as err:
            logger.error(f"login | Thread {self.thread} | {self.name} | {err}")
            return False
