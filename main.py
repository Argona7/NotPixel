from utils.core import create_sessions
from utils.telegram import Accounts
from utils.NotPixel import NotPixel
from data.config import  USE_PROXY, USE_TG_BOT, BOT_TOKEN

import asyncio
import os
import time
import sys

async def main():
    action = int(input('Выберите действие:\n1. Начать сбор монет\n2. Создать сессию\n>'))

    if not os.path.exists('sessions'):
        os.mkdir('sessions')

    if action == 2:
        await create_sessions()

    if action == 1:
        accounts = await Accounts().get_accounts()

        tasks = []
        if USE_PROXY:
            proxy_dict = {}
            with open('proxy.txt', 'r', encoding='utf-8') as file:
                proxy = [i.strip().split() for i in file.readlines() if len(i.strip().split()) == 2]
                for prox, name in proxy:
                    proxy_dict[name] = prox
            for thread, account in enumerate(accounts):
                if account in proxy_dict:
                    tasks.append(
                        asyncio.create_task(NotPixel(account=account, thread=thread, proxy=proxy_dict[account]).main()))
                else:
                    tasks.append(asyncio.create_task(NotPixel(account=account, thread=thread).main()))
        else:
            for thread, account in enumerate(accounts):
                tasks.append(asyncio.create_task(NotPixel(account=account, thread=thread).main()))

        await asyncio.gather(*tasks)


if __name__ == '__main__':
    if sys.platform.startswith('win'):
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())
    print("\nThe automation has been completed successfully!")
    time.sleep(3)

