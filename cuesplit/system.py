import asyncio
import os


async def check_dep(dependency):
    for path in os.getenv('PATH').split(':'):
        dep_bin = os.path.join(path, dependency)
        if os.path.exists(dep_bin):
            return True


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
    if p.returncode:
        raise RuntimeError('something bad happened')
    return stdout.decode('utf-8').strip()
