import argparse
import asyncio
# import json
import os
import sys

from .checker import check_cue
from .parser import check_picture, extract_metadata, make_couple
from .encoder import encode_tracks, filter_tracks
from .splitter import detect_gaps, remove_gaps, sift_points, split_cue


def parse_args(version):
    args = argparse.ArgumentParser()
    args.add_argument(
        '-v', '--version', action='version', version=version)
    args.add_argument(
        '-g',
        action='store',
        dest='gaps',
        default='append',
        choices=('append', 'prepend', 'split'),
        help='control gaps, default is append')
    args.add_argument(
        '-m',
        action='store',
        dest='media_type',
        default='flac',
        choices=('flac',),
        help='the output media type, default is flac')
    args.add_argument(
        '-p',
        action='store',
        dest='picture',
        help='add cover front picture to tracks')
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
    metadata = dict()
    template = 'track'
    if arguments.picture:
        await check_picture(arguments.picture, metadata)
    await make_couple(arguments.filename, metadata)
    cue, media = metadata.get('cue'), metadata.get('media')
    if cue and media:
        await extract_metadata(cue, metadata)
    await check_cue(metadata)
    # print(json.dumps(metadata, indent=2, ensure_ascii=False))
    junk = await detect_gaps(metadata, arguments.gaps, template)
    # print(json.dumps(junk, indent=2))
    current = list()
    split = asyncio.create_task(
        split_cue(await sift_points(metadata, arguments.gaps),
                  metadata['media'], template))
    gaps = asyncio.create_task(remove_gaps(junk, split))
    tracks = asyncio.create_task(filter_tracks(template, current, junk, split))
    enc = asyncio.create_task(
        encode_tracks(metadata, current, tracks, arguments.media_type))
    await split
    await gaps
    await tracks
    await enc
