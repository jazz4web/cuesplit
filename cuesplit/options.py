import shlex


async def check_flac(options):
    ini = shlex.split(options or '')
    res = list()
    for each in ini:
        try:
            v = int(each) * -1
            if v in range(9):
                res.append(each)
                break
        except ValueError:
            pass
    return ' '.join(res)


async def try_float(s):
    try:
        float(s)
    except ValueError:
        return False
    return True


async def try_int(s):
    try:
        int(s)
    except ValueError:
        return False
    return True


async def check_opus(options):
    ini = shlex.split(options or '')
    res = list()
    if '--bitrate' in ini:
        if len(ini) < 2:
            raise ValueError('bad encoder options')
        spec = ini[ini.index('--bitrate') + 1]
        if not await try_float(spec) or not 16 <= float(spec) <= 256:
            raise ValueError('bad encoder options:bitrate')
        res.append('--bitrate')
        res.append(str(round(float(spec), 3)))
    if res:
        return ' ' + ' '.join(res)


async def check_vorbis(options):
    ini = shlex.split(options or '')
    res = list()
    if '-q' in ini:
        if len(ini) < 2:
            raise ValueError('bad encoder options')
        spec = ini[ini.index('-q') + 1]
        if not await try_float(spec) or not -1.0 <= float(spec) <= 10.0:
            raise ValueError('bad encoder options:q')
        res.append('-q')
        res.append(str(round(float(spec), 1)))
    return ' '.join(res)


async def check_mp3(options):
    ini = shlex.split(options or '')
    res = list()
    if ini and len(ini) < 2:
        raise ValueError('bad encoder options')
    if '-V' in ini:
        spec = ini[ini.index('-V') + 1]
        if not await try_int(spec) or int(spec) not in range(10):
            raise ValueError('bad encoder options:V')
        res.append('-V')
        res.append(spec)
    if '-b' in ini:
        pot = (32, 40, 48, 56, 64, 80, 96,
               112, 128, 160, 192, 224, 256, 320)
        spec = ini[ini.index('-b') + 1]
        if not await try_int(spec) or int(spec) not in pot:
            raise ValueError('bad encoder options:b')
        res.append('-b')
        res.append(spec)
    if '-q' in ini and '-V' not in res:
        spec = ini[ini.index('-q') + 1]
        if not await try_int(spec) or int(spec) not in range(10):
            raise ValueError('bad encoder options:q')
        res.append('-q')
        res.append(spec)
    if res:
        return ' ' + ' '.join(res)


async def check_options(media, options):
    if media == 'flac':
        return await check_flac(options)
    elif media == 'opus':
        return await check_opus(options)
    elif media == 'vorbis':
        return await check_vorbis(options)
    elif media == 'mp3':
        return await check_mp3(options)
