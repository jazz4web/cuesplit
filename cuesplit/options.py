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
    return ' '.join(res)


async def check_options(media, options):
    if media == 'flac':
        return await check_flac(options)
    elif media == 'opus':
        return await check_opus(options)
