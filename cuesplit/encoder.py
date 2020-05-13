import asyncio
import glob
import os


async def filter_tracks(template, res, junk, main_task):
    files = list()
    while not main_task.done():
        await asyncio.sleep(0.1)
        files = [item for item in sorted(glob.glob(f'{template}*.wav'))
                 if item not in junk and item not in res['tracks']]
        if files and len(files) >= 2:
            if res['label'] is None:
                res['label'] = True
            res['tracks'].append(files[0])
    res['tracks'].append(files[0])


async def encode_tracks(res, main_task):
    while not main_task.done() or res['tracks']:
        while res['label'] is None:
            await asyncio.sleep(0.1)
        p = await asyncio.create_subprocess_shell(
            f'flac -8 -f {res["tracks"][0]}',
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE)
        await p.wait()
        os.remove(res["tracks"][0])
        current = res["tracks"].pop(0)
        print(f'{current} done')
