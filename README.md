*cuesplit* is a simple tool for reading cuesheet files, splitting CDDA-images
and filling tracks' metadata, it is free and anybody may use its code in
accordance with GNU GPLv3.

*cuesplit* is written in Debian bullseye environment, I used python3.8.3
for debugging this tool. *cuesplit* depends on:

* python3-chardet;
* shntool;
* flac;
* opus-tools;
* voribs-tools;
* lame;
* Monkey's Audio Codec.

These dependencies must be installed.

Right now, *cuesplit* is almost ready. Here is some examples of its usage:

FLAC tracks

    cuesplit sample.cue
    # There must be a couple sample.wav, or sample.flac, or sample.ape
    # As a result, cuesplit will create FLAC tracks
    # with maxmimum compression level

FLAC tracks with optional compression level

    cuesplit -o "-7" sample.cue

You can use a media file instead of cue as the argument

    cuesplit sample.flac

Optional output media type

    cuesplit -m opus sample.cue

Set a picture in metadata

    cuesplit -m opus -p cover.jpg sample.cue

***Warning**: be aware, opusenc does not like some jpg-pictures, so cuesplit
might demonstrate an unpredictable failure without an exception instead of
opus tracks, just change the picture*.

Save gaps

    cuesplit -g append sample.cue
    # or
    cuesplit -g prepend sample.cue

Optional encoder options

    cuesplit -m opus -o "--bitrate 92.435" sample.cue
    cuesplit -m mp3 -o "-V 0" sample.cue
    cuesplit -m mp3 -o "-b 224 -q 2" sample.cue
    cuesplit -m vorbis -o "-q 3" sample.cue
    cuesplit -m flac -o "-7" sample.cue

Default encoder options:

* mp3 - `-b 320`;
* opus - default bitrate;
* flac - `-8`;
* vorbis - `-q 4`.

*cuesplit* is simple, I do not think it is needed to write some special man
page or supplementary help right now.
