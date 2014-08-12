#!/usr/bin/python
# Interface to the commandline version of mediainfo to read stream information
#
# This module is by AndreFMi...@gmail.com
# https://code.google.com/p/medianav/
#
# Published under the GPL v3
#

import sys
import os
import subprocess
from pprint import pprint

MEDIAINFO='mediainfo'

# Media has a container, and then video, audio and text streams

# Lines to parse
#General
#Format                           : Matroska
#Codec                            : Matroska
#File size                        : 2416672563
#Overall bit rate                 : 3206541
#Duration                         : 6029357
#
#Video
#Format                           : AVC
#Codec ID                         : V_MPEG4/ISO/AVC
#Codec                            : V_MPEG4/ISO/AVC
#Duration                         : 6023333
#Nominal bit rate                 : 2971000
#Width                            : 960
#Height                           : 720
#Display aspect ratio             : 1.778
#Pixel Aspect Ratio               : 1.000
#Frame rate                       : 23.976
#Scan type                        : Progressive
#
#Audio
#Format                           : AAC
#Codec ID                         : A_AAC
#Codec                            : A_AAC/MPEG4/LC
#Duration                         : 6029357
#Bit rate mode                    : VBR
#Bit rate                         : 129720
#Channel(s)                       : 6
#Sampling rate                    : 48000
#Resolution                       : 16
#Language                         : eng
#
#Text #1
#Format                           : ASS
#Codec ID                         : S_TEXT/ASS
#Codec                            : S_TEXT/ASS
#Language                         : eng

def set_par(result_dict, index, value):
    if (not result_dict.has_key(index)) or result_dict[index] is None or result_dict[index] == '':
        result_dict[index] = value

def set_par_audio(result_dict, audio_num, index, value):
    def_audio = {
        'audio_format' : '',
        'audio_codec_id' : '',
        'audio_codec' : '',
        'audio_bitrate' : None,
        'audio_channels' : None,
        'audio_samplerate' : None,
        'audio_resolution' : None,
        'audio_language' : '',
        }
    audio_dict = result_dict['audios'].setdefault(audio_num, def_audio)
    if (not audio_dict.has_key(index)) or audio_dict[index] is None or audio_dict[index] == '':
        audio_dict[index] = value

def parse_info(filename):
    """ Parses media info for filename """
    args = [MEDIAINFO, '-f', filename]
    output = subprocess.Popen(args, stdout=subprocess.PIPE).stdout
    data = output.readlines()
    output.close()
    mode = 'none'
    result = {
            'general_format' : '',
            'general_codec' : '',
            'general_size' : None,
            'general_bitrate' : None,
            'general_duration' : None,
            'video_format' : '',
            'video_codec_id' : '',
            'video_codec' : '',
            'video_bitrate' : None,
            'video_width' : None,
            'video_height' : None,
            'video_frame_rate': '',
            'video_displayaspect' : None,
            'video_pixelaspect' : None,
            'video_scantype' : '',
            'audios' : {}
            }
    for line in data:
        if not ':' in line:
            if 'General' in line:
                mode = 'General'
            elif 'Video' in line:
                mode = 'Video'
            elif 'Audio' in line:
                mode = 'Audio'
                line = line.strip()
                if '#' in line:
                    audio_num = int(line[line.index('#')+1:])
                else:
                    audio_num = 1
            elif 'Text' in line:
                mode = 'Text'
        else:
            key, sep, value = line.partition(':')
            key = key.strip()
            value = value.strip()
            if mode == 'General':
                if key == 'Format': set_par(result, 'general_format', value)
                if key == 'Codec': set_par(result,'general_codec', value)
                if key == 'File size': set_par(result,'general_size', value)
                if key == 'Overall bit rate': set_par(result,'general_bitrate', value)
                if key == 'Duration': set_par(result,'general_duration', value)
            if mode == 'Video':
                if key == 'Format': set_par(result,'video_format', value)
                if key == 'Codec ID': set_par(result,'video_codec_id', value)
                if key == 'Codec': set_par(result,'video_codec', value)
                if key == 'Nominal bit rate': set_par(result,'video_bitrate', value)
                if key == 'Width': set_par(result,'video_width', value)
                if key == 'Height': set_par(result,'video_height', value)
                if key == 'Frame rate': set_par(result,'video_frame_rate', value)
                if key == 'Original frame rate': set_par(result,'video_orig_frame_rate', value)
                if key == 'Display aspect ratio': set_par(result,'video_displayaspect', value)
                if key == 'Pixel Aspect Ratio': set_par(result,'video_pixelaspect', value)
                if key == 'Scan type': set_par(result,'video_scantype', value)
            if mode == 'Audio':
                if key == 'Format': set_par_audio(result, audio_num, 'audio_format', value)
                if key == 'Codec ID': set_par_audio(result, audio_num, 'audio_codec_id', value)
                if key == 'Codec': set_par_audio(result, audio_num, 'audio_codec', value)
                if key == 'Bit rate': set_par_audio(result, audio_num, 'audio_bitrate', value)
                if key == 'Channel(s)': set_par_audio(result, audio_num, 'audio_channels', value)
                if key == 'Sampling rate': set_par_audio(result, audio_num, 'audio_samplerate', value)
                if key == 'Resolution': set_par_audio(result, audio_num, 'audio_resolution', value)
                if key == 'Language': set_par_audio(result, audio_num, 'audio_language', value)
    return result

if __name__ == '__main__':
    print sys.argv[1]
    r = parse_info(sys.argv[1])
    pprint(r)
