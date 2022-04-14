''' 
Audio helper for Automator Audio module from Automator
======================================================

github: https://github.com/Davide255/Automator 

module from core.audio

MIT License

Copyright (c) 2022 Davide

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
'''

from pydub import AudioSegment
import pafy
import urllib.error

class Stream:
    pass

class Audio_Converter:
    def __init__(self, filename, _format=None) -> None:
        Audio_Converter.filename = filename
        if not _format:
            _format = Audio_Converter.filename.split('.')[-1]
        Audio_Converter.audio_stream = AudioSegment.from_file(Audio_Converter.filename, format=_format)
    
    def convert(self, output, _format=None):
        if not _format:
            _format = output.split('.')[-1]
        Audio_Converter.audio_stream.export(out_f=output, format=_format)

class Youtube(Stream):
    '''
    Stream simple usage:

    >>> from Audio import Audio
    >>> from AudioHelpers import Youtube

    >>> Audio.from_stream(Youtube('url').get_stream())
    
    >>> while Audio.is_playing():
    >>>     pass
    
    Download simple usage:
    
    >>> url = 'https://www.youtube.com/watch?v=fzNMd3Tu1Zw'
    >>> path_to = ''

    >>> from core.audio.AudioHelpers import Youtube

    >>> Youtube(url).download_audio(path_to) # only audio

    >>> Youtube(url).download_video(path_to) # audio and video
    '''

    def __init__(self, url) -> None:
        Youtube.url = url
        Youtube.data = pafy.new(Youtube.url)

    def get_stream(self):
        Youtube.audio_stream = Youtube.data.audiostreams[Youtube.data.audiostreams.index(Youtube.data.getbestaudio())]
        Youtube.audio_stream_url = Youtube.audio_stream.url
        from winrt.windows.foundation import Uri
        from winrt.windows.media import core

        Youtube.stream = core.MediaSource.create_from_uri(Uri(Youtube.audio_stream_url))
        
        return self

    def download(self, video_path, silent=False, callback=None):
        ''' get best video streaming aviable and download it '''
        payload = Youtube.data.streams[Youtube.data.streams.index(Youtube.data.getbest())]

        try:
            payload.download(video_path, quiet=silent, callback=callback)
        except urllib.error.HTTPError:
            pass

    def download_audio(self, audio_path, silent=False, callback=None):
        ''' get best audio streaming aviable and download it '''
        payload = Youtube.data.getbestaudio()

        try:
            payload.download(audio_path, quiet=silent, callback=callback)
        except urllib.error.HTTPError:
            pass
