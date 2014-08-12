#!/usr/bin/env python2

import sys
import os
import os.path as osp
import shutil
import tempfile
import subprocess
import argparse
import itertools

import mediainfo


def main():
    parser = argparse.ArgumentParser(description='Change FPS of a Video and adjust audio.')
    parser.add_argument('input',
                        help='input filename')
    parser.add_argument('-n', '--dry-run',       action='store_true',
                        help='do only a dry run and only print the commands that would otherwise be executed')
    parser.add_argument('-r', '--fps',           default=24,      type=int,               metavar='FPS',
                        help='target fps FPS')
    parser.add_argument('-o', '--output',        default=None,
                        help='output file or folder name')
    parser.add_argument('-t', '--tmp',           default='/tmp',
                        help='folder for temporary files')
    parser.add_argument('-C', '--copy',          action='store_true',
                        help='copy source file to temporary directory while processing')
    tgrp = parser.add_argument_group(title='Track specific options',
                                     description='These options specify what should be done to specific tracks. '
                                                'Repeat options for multiple tracks. '
                                                'For each track at most one of -k, -c or -p can be specified. '
                                                'Counting starts at 0.')
    tgrp.add_argument('-k', '--keep-pitch',    action='append', type=int, default = [], metavar='TID',
                        help='change tempo of track TID while keeping the pitch')
    tgrp.add_argument('-c', '--no-keep-pitch', action='append', type=int, default = [], metavar='TID',
                        help='change tempo of track TID without keeping the pitch')
    tgrp.add_argument('-p', '--passthrough',   action='append', type=int, default = [], metavar='TID',
                        help='do not filter track TID')
    tgrp.add_argument('-s', '--sfps',          action='append',           default = [], metavar='TID:FPS',
                        help='assume source FPS for track TID')
    args = parser.parse_args()

    args.sfps = dict((int(x), float(y)) for x, y in itertools.imap(lambda z: z.split(':'), args.sfps))

    sets = []
    for name in ['keep_pitch', 'no_keep_pitch', 'passthrough']:
        s = set(getattr(args, name))
        setattr(args, name, s)
        sets.append(s)

    if not all(a.isdisjoint(b) for a, b in itertools.combinations(sets, 2)):
        print 'Input error: ambiguous track options!'
        sys.exit(1)

    if not osp.isfile(args.input):
        print 'Input error: input file does not exist!'
        sys.exit(1)

    head, tail = osp.split(args.input)
    base, ext = osp.splitext(tail)
    if args.output is None:
        ohead = osp.join(head, '{}fps'.format(args.fps))
        try:
            os.makedirs(ohead)
        except os.error:
            pass
        args.output = osp.join(ohead, tail)
    if osp.isdir(args.output):
        args.output = osp.join(args.output, tail)

    try:
        info = mediainfo.parse_info(args.input)
        ifps = float(info['video_frame_rate'])
    except:
        print 'Error: could not parse results of mediainfo for input file!'
        sys.exit(1)

    ffargs = ['ffmpeg',
              '-i', args.input,
              '-map', '0',
              '-vn', '-sn',]

    for i, j in enumerate(sorted(info['audios'].keys())):
        audio = info['audios'][j]
        ffargs.extend(["-b:a:{}".format(i), "{}".format(audio['audio_bitrate'])])
        if i in args.keep_pitch:
            mode='k'
        elif i in args.no_keep_pitch:
            mode='c'
        elif i in args.passthrough:
            mode='p'
        elif audio['audio_language'] == 'de':
            mode='k'
        else:
            mode='c'

        if mode in ['k', 'c']:
            ffargs.extend(['-c:a:{}'.format(i), 'ac3'])
        elif mode in ['p']:
            ffargs.extend(['-c:a:{}'.format(i), 'copy'])
        else:
            raise ValueError

        try:
            atempo = args.fps/args.sfps[i]
        except KeyError:
            atempo = args.fps/ifps

        if mode == 'k':
            ffargs.extend(["-filter:a:{}".format(i), "atempo={}".format(atempo)])
        elif mode == 'c':
            arate = int(audio['audio_samplerate'])
            srate = int(round(atempo*float(arate)))
            ffargs.extend(["-filter:a:{}".format(i), "asetrate={},aresample={}".format(srate, arate)])
        elif mode == 'p':
            pass
        else:
            raise ValueError

    if not args.dry_run:
        tmpdir = tempfile.mkdtemp(dir=args.tmp)
    else:
        tmpdir = osp.join(args.tmp, 'tmpXYZ')
    tmpfile = osp.join(tmpdir, '{}-AUDIO.mkv'.format(base))

    ffargs.extend([tmpfile])

    print '"'+'" "'.join(ffargs)+'"'
    print

    if not args.dry_run:
        ffproc = subprocess.Popen(ffargs)
        if args.copy:
            tmpfile2 = osp.join(tmpdir, '{}.mkv'.format(base))
            shutil.copyfile(args.input, tmpfile2)
            args.input = tmpfile2
        ffproc.wait()

    mmargs=['mkvmerge',
            '-o', args.output,
            '--no-audio',
            '--sync', '0:0,{}/{}'.format(ifps, args.fps),
            "--fix-bitstream-timing-information", "0:1",
            args.input,
            '--no-video',
            '--no-subtitles',
            '--no-buttons',
            '--no-global-tags',
            '--no-track-tags',
            '--no-chapters',
            '--no-attachments',
            tmpfile]

    print '"'+'" "'.join(mmargs)+'"'
    print

    if not args.dry_run:
        subprocess.check_call(mmargs)

        try:
            os.remove(tmpfile)
        except os.error:
            pass

        if args.copy:
            try:
                os.remove(tmpfile2)
            except os.error:
                pass

        try:
            os.rmdir(tmpdir)
        except os.error:
            pass


if __name__== "__main__":
    main()

