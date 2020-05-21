import asyncio
import re


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
        await check_index(track["index0"], check_only=True)
        await check_index(track["index1"], check_only=True)
        num = track.get('num')
        if track.get('title') is None:
            raise ValueError(f'bad title for track {num}')
        if track['num'] != '01' and track['index1'] is None:
            raise ValueError(f'bad index for track {num}')
    slash = '/' if cue.get('comment') and cue.get('disc ID') else ''
    cue['commentary'] = f'{cue.get("comment")}{slash}{cue.get("disc ID")}'


async def check_index(timestamp, check_only=False):
    if timestamp:
        mm, ss, ff = re.split(r'[:.]', timestamp)
        if int(ss) > 59 or int(ff) > 74:
            raise ValueError('invalid timestamp')
        if not check_only:
            return mm, ss, ff


async def convert_to_number(timestamp):
    mm, ss, ff = await check_index(timestamp)
    ss = int(mm) * 60 + int(ss)
    nnn = round(int(ff) / 0.075)
    if nnn > 999:
        ss += 1
        nnn = 0
    return ss + nnn / 1000


async def check_couple(cue):
    p = await asyncio.create_subprocess_shell(
        f'shnlen -ct \"{cue.get("media")}\"',
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE)
    stdout, stderr = await p.communicate()
    await p.wait()
    if p.returncode:
        raise RuntimeError('it looks like the media file is not valid')
    r = stdout.decode('utf-8').split()
    if r[3] != '---':
        raise ValueError('the media file is not CDDA')
    length = await convert_to_number(r[0])
    last = await convert_to_number(cue["tracks"][-1]["index1"])
    if length - last < 2:
        raise ValueError('the media file is too short for this cue')
