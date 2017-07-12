import asyncio
from aiohttp import ClientSession
import requests as re
import sys
import shelve
import os

tasks_amount = 0
done_amount = 0


async def download_images(title, image_url, session):
    async with session.get(image_url) as response:
        with open(f'{title}\\'+image_url.split('/')[-1], 'wb') as file:
            content = await response.read()
            file.write(content)
            global done_amount
            done_amount += 1
            print("Downloaded {} out of {}".format(done_amount, tasks_amount))

async def fetch_images(thread_url, session):
    async with session.get(thread_url.replace('.html', '.json')) as response:
        thread = await response.json()
        posts = thread['threads'][0]['posts']
        title = thread['title']
        title = " ".join(title.split()[:2])
        tasks = []
        try:
            os.mkdir(title)
        except FileExistsError:
            pass
        for post in range(len(posts)):
            files = posts[post]['files']
            for src in range(len(files)):
                task = asyncio.ensure_future(download_images(title, 'https://2ch.hk'+files[src]['path'], session=session))
                tasks.append(task)
        global tasks_amount
        tasks_amount = len(tasks)
        await asyncio.gather(*tasks)


if __name__ == "__main__":
    url = ''
    while True:
        if url == '':
            url = input("Enter url of thread you want to save: ").rstrip()
        with shelve.open('config') as config:
            try:
                config['usercode_auth']
            except KeyError:
                config['usercode_auth'] = ''
                config['ageallow'] = '1'

            cookies = {
                'usercode_auth': config['usercode_auth'],
                'ageallow': config['ageallow']
            }

            status_code = re.get(url, cookies=cookies).status_code

            if status_code == 404:
                print('Thread is not found! It is not exist, expired, or you need specific cookies!')
                answer = input('Do you want to enter the cookies? y/n: ')
                if answer == 'y':
                    config['usercode_auth'] = input('Enter usercode_auth: ')
                    config['ageallow'] = '1'
                else:
                    sys.exit()
            else:
                if status_code == 200:
                    break
                else:
                    print('Thread is not found. Status code is {}'.format(status_code))

    print('Downloading...')
    loop = asyncio.get_event_loop()
    future = asyncio.ensure_future(fetch_images(url, ClientSession(cookies=cookies)), loop=loop)
    loop.run_until_complete(future)
    print('Done!')
