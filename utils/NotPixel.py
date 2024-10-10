from urllib.parse import unquote
from fake_useragent import UserAgent
from pyrogram import Client
from data import config
from utils.core import logger

from aiohttp_socks import ProxyConnector
from pyrogram.raw.functions.messages import RequestAppWebView
from pyrogram.raw.types import InputBotAppShortName

import aiohttp
import asyncio
import random


class NotPixel:

    def __init__(self, thread: int, account: str, proxy=None):
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

        headers = {
            'accept': 'application/json, text/plain, */*',
            'accept-encoding': 'gzip, deflate, br, zstd',
            'accept-language': 'ru',
            'dnt': '1',
            'origin': 'https://app.notpx.app',
            'priority': 'u=1, i',
            'referer': 'https://app.notpx.app/',
            'sec-ch-ua': '"Chromium";v="128", "Not;A=Brand";v="24", "Google Chrome";v="128"',
            'sec-ch-ua-platform': '"Android"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-site',
            'user-agent': UserAgent(os='android').random
        }

        return aiohttp.ClientSession(headers=headers, trust_env=True, connector=connector)

    async def main(self):
        await asyncio.sleep(random.randint(*config.ACC_DELAY))
        while True:
            try:
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

                await self.me()
                status = await self.status()
                await self.list()
                await self.event({"n": "pageview", "u": "https://app.notpx.app/", "d": "notpx.app",
                                     "r": "https://web.telegram.org/"})
                await self.squad()
                await asyncio.sleep(random.uniform(*config.MINI_SLEEP))
                if status:
                    curr_cords = []
                    for i in range(status["charges"]):
                        if not curr_cords:
                            curr_cords = [random.randint(100, 800), random.randint(100, 800)]

                        rand_number = random.choice([i for i in range(-30, 31) if i != 0])
                        cord = curr_cords[0] * 1000 + rand_number * 1000 + curr_cords[1] + rand_number
                        color = random.choice(config.colors)
                        await self.paint(cord, color)
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
                    sleep_time = status["maxCharges"] * (status["reChargeSpeed"] // 1000) + random.randint(100, 600)
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
        response = await self.session.post("https://notpx.app/api/v1/repaint/start", json=body)
        response = await response.json()
        if "balance" in response:
            logger.success(f'paint | Thread {self.thread} | {self.name} | paint successfully: {response["balance"]}')
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
        response = await response.json()
        if "error" in response:
            logger.warning(f'upgrade | Thread {self.thread} | {self.name} | {response["error"]}')
            return False
        if response[type_upgrade] is True:
            logger.success(f'upgrade | Thread {self.thread} | {self.name} | Successfully upgraded : {type_upgrade}')
            return True

    async def farming_claim(self):
        response = await self.session.get("https://notpx.app/api/v1/mining/claim")
        if response.status == 200:
            logger.success(f'farming claim | Thread {self.thread} | {self.name} | farming reward claimed successfully!')
            return True
        return False

    async def do_task(self, task_name, type_task=None):
        if not type_task:
            response = await self.session.get(f"https://notpx.app/api/v1/mining/task/check/{task_name}")
            response = await response.json()
            if task_name in response and response[task_name] is True:
                logger.success(f'farming claim | Thread {self.thread} | {self.name} | Task completed: {task_name}')
        params = {"name": task_name}
        response = await self.session.get(f"https://notpx.app/api/v1/mining/task/check/{type_task}", params=params)
        response = await response.json()
        task = f"{type_task}:{task_name}"
        if task in response and response[task] is True:
            logger.success(f'farming claim | Thread {self.thread} | {self.name} | Task completed: {task_name} {type_task}')

    async def event(self, body):
        response = await self.session.post("https://plausible.joincommunity.xyz/api/event", json=body)
        if response.status == 202:
            return True
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

    async def list(self):
        response = await self.session.get("https://notpx.app/api/v1/buy/list")
        if response.status == 200:
            return await response.json()
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

                auth_url = web_view.url

                self.user_info = await self.client.get_me()
            except Exception as err:
                logger.error(f"main | Thread {self.thread} | {self.name} | {err}")
                if 'USER_DEACTIVATED_BAN' in str(err):
                    logger.error(f"login | Thread {self.thread} | {self.name} | USER BANNED")
                    await self.client.disconnect()
                    return False
            return unquote(string=auth_url.split('tgWebAppData=')[1].split('&tgWebAppVersion')[0])

    async def login(self):
        try:
            tg_web_data = await self.get_tg_web_data()
            if tg_web_data is False:
                return False

            self.session.headers['authorization'] = f"initData {tg_web_data}"
            if not await self.me():
                return False
            return True
        except Exception as err:
            logger.error(f"login | Thread {self.thread} | {self.name} | {err}")
            return False
