import glob
import os
import asyncio


async def detect_gaps(cue, schema, template):
    junk = list()
    if schema == 'split':
        step = 1
        for each in cue['tracks']:
            if each['num'] == '01':
                if each['index1']:
                    junk.append(f'{template}{str(step).zfill(2)}.wav')
                    step += 1
            else:
                if each['index0']:
                    step += 1
                    junk.append(f'{template}{str(step).zfill(2)}.wav')
                    step += 1
                else:
                    step += 1
    return junk


async def check_point(index):
    if index:
        parts = index.split(':')
        return f'{int(parts[0])}:{parts[1]}.{parts[2]}'


async def sift_points(cue, schema):
    points = list()
    for track in cue['tracks']:
        if schema == 'append' and track['num'] != '01':
            points.append(await check_point(track['index1']))
        elif schema == 'prepend':
            if track['index0'] and track['num'] != '01':
                points.append(await check_point(track['index0']))
            elif not track['index0'] and track['num'] != '01':
                points.append(await check_point(track['index1']))
        elif schema == 'split':
            if track['index0']:
                points.append(await check_point(track['index0']))
            if track['index1']:
                points.append(await check_point(track['index1']))
    return '\n'.join(points).encode("utf-8")


async def clean_cwd(template):
    for each in glob.glob(template):
        os.remove(each)
    print('current working directory is clean')


async def split_cue(points, filename, template):
    await clean_cwd(f'{template}*.wav')
    p = await asyncio.create_subprocess_shell(
        f'shnsplit -a {template} "{filename}"',
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE)
    await p.communicate(points)
    await p.wait()
    if p.returncode == 0:
        print(f'{os.path.basename(filename)} got split, wait for encoding...')


async def remove_gaps(junk, main_task):
    while not main_task.done():
        await asyncio.sleep(0.1)
        for each in os.listdir('.'):
            if each in junk:
                os.remove(each)
                print(f'{each} is a gap, removed')
