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
