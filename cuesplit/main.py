import argparse
import asyncio
import os
import sys

from .checker import check_cue, check_couple
from .parser import check_picture, extract_metadata, make_couple
from .encoder import encode_tracks, filter_tracks
from .options import check_options
from .splitter import detect_gaps, remove_gaps, sift_points, split_cue
from .system import check_dep


def parse_args(version):
    args = argparse.ArgumentParser()
    args.add_argument(
        '-v', '--version', action='version', version=version)
    args.add_argument(
        '-g',
        action='store',
        dest='gaps',
        default='split',
        choices=('append', 'prepend', 'split'),
        help='control gaps, default is split')
    args.add_argument(
        '-m',
        action='store',
        dest='media_type',
        default='flac',
        choices=('flac', 'opus', 'vorbis', 'mp3'),
        help='the output media type, default is flac')
    args.add_argument(
        '-p',
        action='store',
        dest='picture',
        help='add cover front picture to tracks, not an option with vorbis')
    args.add_argument(
        '-o',
        action='store',
        dest='enc_opts',
        help='control some options while encoding tracks')
    args.add_argument(
        'filename', action='store', help='the converted file name')
    return args.parse_args()


def show_error(msg, code=1):
    print(
        os.path.basename(sys.argv[0]),
        'error',
        msg,
        sep=':',
        file=sys.stderr)
    sys.exit(code)


async def start_the_process(arguments):
    opts = await check_options(arguments.media_type, arguments.enc_opts)
    template, current, metadata, = 'track', list(), dict()
    if arguments.picture:
        await check_picture(arguments.picture, metadata)
    await make_couple(arguments.filename, metadata)
    cue, media = metadata.get('cue'), metadata.get('media')
    if not await check_dep('shntool'):
        raise OSError('shntool is not installed')
    if arguments.media_type == 'flac' or os.path.splitext(media)[1] == '.flac':
        if not await check_dep('flac'):
            raise OSError('flack is not installed')
    if os.path.splitext(media)[1] == '.ape':
        if not await check_dep('mac'):
            raise OSError("Monkey's Audio  is not installed")
    if arguments.media_type == 'opus':
        if not await check_dep('opusenc'):
            raise OSError('opus-tools is not installed')
    elif arguments.media_type == 'vorbis':
        if not await check_dep('oggenc'):
            raise OSError('vorbis-tools is not installed')
        if arguments.picture:
            print('picture is not an option with vorbis tracks, ignored')
    elif arguments.media_type == 'mp3':
        if not await check_dep('lame'):
            raise OSError('lame is not installed')
    await extract_metadata(cue, metadata)
    await check_cue(metadata)
    await check_couple(metadata)
    junk = await detect_gaps(metadata, arguments.gaps, template)
    split = asyncio.create_task(
        split_cue(await sift_points(metadata, arguments.gaps),
                  metadata['media'], template))
    gaps = asyncio.create_task(remove_gaps(junk, split))
    tracks = asyncio.create_task(filter_tracks(template, current, junk, split))
    enc = asyncio.create_task(
        encode_tracks(metadata, current, tracks, arguments.media_type, opts))
    await split
    await gaps
    await tracks
    await enc
