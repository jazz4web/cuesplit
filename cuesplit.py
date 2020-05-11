#!/usr/bin/env python3

import argparse
import asyncio
import json
import glob
import os
import re

from chardet import detect


def parse_args():
    args = argparse.ArgumentParser()
    args.add_argument(
        '-v', '--version', action='version', version='cuesplit-1.0.1-pre')
    args.add_argument(
        '-g',
        action='store',
        dest='gaps',
        default='append',
        choices=('append', 'prepend', 'split'),
        help='control gaps')
    args.add_argument(
        'filename', action='store', help='the converted file name')
    return args.parse_args()


async def check_dep(dependency):
    for path in os.getenv('PATH').split(':'):
        dep_bin = os.path.join(path, dependency)
        if os.path.exists(dep_bin):
            return True


async def make_couple(filename, res):
    medias = ('.wav', '.flac')
    cues = ('.cue', '.cue~')
    if not os.path.exists(filename):
        raise FileNotFoundError(f'"{filename}" does not exist')
    source = os.path.realpath(filename)
    hd = os.path.dirname(source)
    name, ext = os.path.splitext(os.path.basename(source))
    if ext in cues:
        for each in medias:
            m = os.path.join(hd, name + each)
            if os.path.exists(m):
                res['media'] = m
                res['cue'] = source
                break
    elif ext in medias:
        for each in cues:
            c = os.path.join(hd, name + each)
            if os.path.exists(c):
                res['cue'] = c
                res['media'] = source
                break


async def detect_f_type(name):
    required = 'file'
    dep = await check_dep(required)
    if not dep:
        raise OSError(f'{required} is not installed')
    p = await asyncio.create_subprocess_shell(
        f'file -b --mime-type "{name}"',
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE)
    stdout, stderr = await p.communicate()
    if stderr:
        raise RuntimeError('something bad happened')
    return stdout.decode('utf-8').strip()


async def read_file(name):
    t = await detect_f_type(name)
    if t != 'text/plain':
        raise OSError('bad cue')
    try:
        with open(name, 'rb') as f:
            enc = detect(f.read())['encoding']
            f.seek(0)
            return [line.decode(enc).rstrip() for line in f]
    except(OSError, ValueError):
        return None


async def get_value(content, expression, index=False):
    pattern = re.compile(expression)
    for line in content:
        box = pattern.match(line)
        if box:
            if index:
                return box.group(1)
            return box.group(1).strip('"')


async def get_tracks(content):
    res = list()
    i = 0
    pattern = re.compile(r'^ +TRACK +(\d+) +(.+)')
    for step, item in enumerate(content):
        box = pattern.match(item)
        if box:
            track = dict()
            track['num'] = box.group(1)
            track['this'] = step
            if i:
                res[i - 1]['next'] = step
            res.append(track)
            i += 1
    return res


async def get_tracks_meta(content, tracks, performer):
    title = r'^ +TITLE +(.+)'
    perf = r'^ +PERFORMER +(.+)'
    index0 = r'^ +INDEX 00 +(\d{2}:\d{2}:\d{2})'
    index1 = r'^ +INDEX 01 +(\d{2}:\d{2}:\d{2})'
    for i in range(len(tracks)):
        first = tracks[i].get('this')
        second = tracks[i].get('next')
        tracks[i]['title'] = await get_value(content[first:second], title)
        tracks[i]['performer'] = await get_value(content[first:second], perf)
        if tracks[i].get('performer') is None:
            tracks[i]['performer'] = performer
        tracks[i]['index0'] = await get_value(
            content[first:second], index0, index=True)
        tracks[i]['index1'] = await get_value(
            content[first:second], index1, index=True)
        if first:
            del tracks[i]['this']
        if second:
            del tracks[i]['next']


async def extract_metadata(filename, res):
    content = await read_file(filename)
    if content is None:
        raise ValueError('cue is not readable or has bad encoding')
    res['album performer'] = await get_value(content, r'^PERFORMER +(.+)')
    res['album'] = await get_value(content, r'^TITLE +(.+)')
    res['genre'] = await get_value(content, r'REM GENRE +(.+)')
    res['disc ID'] = await get_value(content, r'^REM DISCID +(.+)')
    res['date'] = await get_value(content, r'^REM DATE +(.+)')
    res['comment'] = await get_value(content, r'^REM COMMENT +(.+)')
    res['tracks'] = await get_tracks(content)
    if res['tracks']:
        await get_tracks_meta(content, res['tracks'], res['album performer'])


async def check_cue(cue):
    summary = [bool(cue.get('album')),
               bool(cue.get('album performer')),
               bool(cue.get('tracks'))]
    if not all(summary):
        raise ValueError('this cuesheet is not valid')
    if cue['tracks'][0].get('index0') == '00:00:00':
        cue['tracks'][0]['index0'] = None
    if cue['tracks'][0].get('index1') == '00:00:00':
        cue['tracks'][0]['index1'] = None
    for track in cue.get('tracks', list()):
        num = track.get('num')
        if track.get('title') is None:
            raise ValueError(f'bad title for track {num}')
        if track['num'] != '01' and track['index1'] is None:
            raise ValueError(f'bad index for track {num}')


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


async def remove_gaps(junk):
    while junk:
        await asyncio.sleep(0.5)
        for each in os.listdir('.'):
            if each in junk:
                os.remove(each)
                junk.remove(each)
                print(f'{each} is a gap and removed')


async def clean_cwd(template):
    for each in glob.glob(template):
        os.remove(each)
    print('cwd got cleaned')


async def split_cue(points, filename, template):
    dep = await check_dep('shntool')
    if not dep:
        raise OSError(f'shntool is not installed')
    await clean_cwd(f'{template}*.wav')
    p = await asyncio.create_subprocess_shell(
        f'shnsplit -a {template} "{filename}"',
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE)
    await p.communicate(points)
    await p.wait()
    if p.returncode == 0:
        print(f'{os.path.basename(filename)} got split')


async def main(arguments):
    data = dict()
    template = 'track'
    await make_couple(arguments.filename, data)
    cue, media = data.get('cue'), data.get('media')
    if cue and media:
        await extract_metadata(cue, data)
    await check_cue(data)
    # print(json.dumps(data, indent=2, ensure_ascii=False))
    junk = await detect_gaps(data, arguments.gaps, template)
    # print(json.dumps(junk, indent=2))
    first = asyncio.create_task(
        split_cue(await sift_points(data, arguments.gaps),
                  data['media'], template))
    second = asyncio.create_task(remove_gaps(junk))
    await first
    await second


if __name__ == '__main__':
    cmd = parse_args()
    try:
        asyncio.run(main(cmd))
    except Exception as e:
        print(e)
