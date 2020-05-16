import asyncio
import glob
import os
import re

from .system import check_dep
from . import version


async def set_track_name(metadata, num, ext):
    e = r'[\\/|?<>*:]'
    return '{0} - {1} - {2}{3}'.format(
        metadata['tracks'][num]['num'],
        re.sub(e, '~', metadata['tracks'][num]['performer']),
        re.sub(e, '~', metadata['tracks'][num]['title']),
        ext)


async def get_flac(metadata, num, filename):
    new = await set_track_name(metadata, num, '.flac')
    pic = None
    if 'cover front' in metadata:
        pic = f' --picture=\"3||front cover||{metadata["cover front"]}\"'
    cmd = 'flac -8 -f -o "{0}"{1}{2}{3}{4}{5}{6}{7}{8} {9}'.format(
        new,
        f' --tag=artist=\"{metadata["tracks"][num]["performer"]}\"',
        f' --tag=album=\"{metadata["album"]}\"',
        f' --tag=genre=\"{metadata["genre"]}\"',
        f' --tag=title=\"{metadata["tracks"][num]["title"]}\"',
        f' --tag=tracknumber={int(metadata["tracks"][num]["num"])}',
        f' --tag=date=\"{metadata["date"]}\"',
        f' --tag=comment=\"{metadata["commentary"] or version}\"',
        pic,
        filename)
    return new, cmd


async def get_opus(metadata, num, filename):
    new = await set_track_name(metadata, num, '.opus')
    pic = None
    if 'cover front' in metadata:
        pic = f' --picture \"3||front cover||{metadata["cover front"]}\"'
    cmd = 'opusenc {0}{1}{2}{3}{4}{5}{6}{7} {8} \"{9}\"'.format(
        f' --artist \"{metadata["tracks"][num]["performer"]}\"',
        f' --album \"{metadata["album"]}\"',
        f' --genre \"{metadata["genre"]}\"',
        f' --title \"{metadata["tracks"][num]["title"]}\"',
        f' --comment tracknumber=\"{int(metadata["tracks"][num]["num"])}\"',
        f' --date \"{metadata["date"]}\"',
        f' --comment comment=\"{metadata["commentary"] or version}\"',
        pic,
        filename,
        new)
    return new, cmd


async def set_cmd(metadata, media, num, filename):
    if media == 'flac':
        if os.path.splitext(metadata.get('media'))[1] != '.flac':
            if not await check_dep('flac'):
                raise OSError('flack is not installed')
        return await get_flac(metadata, num, filename)
    elif media == 'opus':
        if not await check_dep('opusenc'):
            raise OSError('opus-tools is not installed')
        return await get_opus(metadata, num, filename)


async def filter_tracks(template, res, junk, main_task):
    files = list()
    while not main_task.done():
        await asyncio.sleep(0.1)
        files = [item for item in sorted(glob.glob(f'{template}*.wav'))
                 if item not in junk and item not in res]
        if files and len(files) >= 2:
            res.append(files[0])
    res.append(files[0])


async def encode_tracks(metadata, res, main_task, media):
    i = 0
    while not main_task.done() or res:
        if not len(res):
            await asyncio.sleep(0.1)
            continue
        new, cmd = await(set_cmd(metadata, media, i, res[0]))
        p = await asyncio.create_subprocess_shell(
            cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE)
        await p.wait()
        os.remove(res[0])
        current = res.pop(0)
        print(f'{current} -> {new}')
        i += 1
