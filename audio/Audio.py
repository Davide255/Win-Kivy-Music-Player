'''
Audio player and controller from Automator
==========================================

github: https://github.com/Davide255/Automator

module from core.audio

See Audio class fro docs

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

import time, os

#Audio Requirements
from ctypes import POINTER, cast
from os import environ

class Audio:

    '''
Class for controlling playing audios and queues
===============================================

Simples:
       
    Playing audio file:

        >>> from Audio import Audio

        >>> Audio().play_audio('path\\to\\file.ext')

    Controlling Audio in your system:

        >>> from Audio import Audio

        >>> controller = Audio.Controller()
        >>> controller.setMasterLevel(60) #volume will be set to 60%

    Advanced:

        Real time control:

        >>> from Audio import Audio

        >>> Audio().play_audio('path\\to\\file.ext', True) #True means that this
                                                            instruction will be executed
                                                            in a separate Thread
        >>> while True:

        >>>    command = input('Audio %s is playing:\nP) Play/Pause\nQ) Quit\n\nWhat did you choose? ')

        >>>    if command in ('p', 'P'):
        >>>        Audio.play_pause()

        >>>    elif command in ('q', 'Q'):
        >>>        Audio.quit()
        >>>        break

        >>>    else: print('Unknown command')

        >>>    print ("\033[A                             \033[A") #clean line

        Play from Youtube audio:

        >>> from Audio import Audio
        >>> from AudioHelpers import Youtube

        >>> Audio.from_stream(Youtube('url').get_stream())

        >>> while Audio.is_playing():
        >>>     pass

        Mute/Unmute a sigle process:

        >>> from Audio import Audio
        >>> from core.process import getallprocs

        >>> controller = Audio.Controller()

        >>> for p in getallprocs(name=False):
    '''

    events = ('media_ended', 'source_changed', 'volume_changed', 'playback_state_changed', 'position_changed')

    class Controller:
        class Process:
            def __init__(self, process_name) -> None:
                if process_name != None:
                    self.process_name = process_name

            def mute(self):
                from libs.PyCAW import AudioUtilities
                import logging as Logger
                sessions = AudioUtilities.GetAllSessions()
                for session in sessions:
                    interface = session.SimpleAudioVolume
                    if session.Process and self.process_name in session.Process.name():
                        print(dir(interface))
                        interface.SetMute(1, None)
                        Logger.info('Audio:', self.process_name, 'has been muted.')

            def unmute(self):
                from libs.PyCAW import AudioUtilities
                import logging as Logger
                sessions = AudioUtilities.GetAllSessions()
                for session in sessions:
                    interface = session.SimpleAudioVolume
                    if session.Process and self.process_name in session.Process.name():
                        print(dir(interface))
                        interface.SetMute(0, None)
                        Logger.info('Audio:', self.process_name, 'has been unmuted.')

            def get_volume(self):
                from libs.PyCAW import AudioUtilities
                import logging as Logger
                sessions = AudioUtilities.GetAllSessions()
                for session in sessions:
                    interface = session.SimpleAudioVolume
                    if session.Process and session.Process.name() == self.process_name:
                        Logger.info('Audio: Volume:' + str(round(interface.GetMasterVolume() ** 100)) + '%')
                        return round(interface.GetMasterVolume() ** 100)

            def set_volume(self, volume):
                from libs.PyCAW import AudioUtilities
                import logging as Logger
                sessions = AudioUtilities.GetAllSessions()
                for session in sessions:
                    interface = session.SimpleAudioVolume
                    if session.Process and session.Process.name() == self.process_name:
                        Logger.info('Audio: Volume:' + str(round(interface.GetMasterVolume() ** 100)) + '%')
                        return not bool(interface.SetMasterVolume(volume/100, None))

        def get_all_sessions(self):
            from libs.PyCAW import AudioUtilities
            sessions = AudioUtilities.GetAllSessions()
            procs = list()
            for session in sessions:
                if session.Process:
                    procs.append(session.Process.name())
            return procs

        def setMasterLevel(self, level):
            if isinstance(level, int):
                level = level/100
            if level > 1.0:
                level = level/10
            from comtypes import CLSCTX_ALL, CoUninitialize
            from libs.PyCAW import AudioUtilities, IAudioEndpointVolume
            interface = AudioUtilities.GetSpeakers().Activate(IAudioEndpointVolume._iid_, CLSCTX_ALL, None)
            volume = cast(interface, POINTER(IAudioEndpointVolume))
            volume.SetMasterVolumeLevelScalar(level, None)
            CoUninitialize()

    async def async_initiallize(self):
        
        from winrt.windows.media.playback import MediaPlayer
        if hasattr(Audio, 'mediaplayer'):
            del Audio.mediaplayer
        Audio.mediaplayer = MediaPlayer()
        Audio.mediaplayer.add_media_ended(Audio.media_ended)
        Audio.mediaplayer.add_source_changed(Audio.source_changed)
        Audio.mediaplayer.add_volume_changed(Audio.volume_changed)
        Audio.mediaplayer.playback_session.add_playback_state_changed(Audio.playback_state_changed)
        Audio.mediaplayer.playback_session.add_position_changed(Audio.position_changed)

    def from_stream(stream_obj):
        import asyncio
        asyncio.run(Audio().async_initiallize())

        from winrt.windows.foundation import TimeSpan

        Audio._stream = stream_obj

        Audio.mediaplayer.source = stream_obj.stream
        Audio.duration = TimeSpan()
        Audio.duration.duration = stream_obj.data.length * 10000000
        
        Audio.title = stream_obj.data.title

        Audio.play()

        from threading import Thread
        Thread(target=Audio.stream_end_handler, daemon=True).start()

    def get_stream(self):
        if hasattr(Audio, '_stream'):
            return Audio._stream

    def is_stream(self):
        return True if hasattr(Audio, 'duration') else False

    def stream_end_handler():
        while True:
            if Audio().get_pos() == Audio().get_total():
                Audio().media_ended()
                break
            else:
                time.sleep(1)

    def _menu_voices(self, state:bool):
        try:
            from libs.LibWin import SysTrayIcon
            if state:
                Audio_voices = ("Play/Pause Audio", None, lambda *args: Audio().play_pause()),  ("Close Audio", None, lambda *args: Audio().quit()),
            else:
                Audio_voices = ("Play/Pause Audio", None, SysTrayIcon.Item_Deactivate),  ("Close Audio", None, SysTrayIcon.Item_Deactivate),
            for i in Audio_voices:
                SysTrayIcon().EditMenuItemInfo(i[0], i)
        except ImportError:
            pass   

    async def _play_audio(self, filename, keep_alive: bool = True):
        from winrt.windows.media.playback import MediaPlaybackItem, MediaPlaybackState
        from winrt.windows.media import core, MediaPlaybackType
        from winrt.windows.storage import StorageFile
        import asyncio
        await asyncio.create_task(self.async_initiallize())
        if isinstance(filename, str):
            try:
                file = await StorageFile.get_file_from_path_async(filename)
            except RuntimeError:
                print(filename, 'is not a valid file')
                Audio.title = ''
                return
            Audio.title = file.display_name
            Audio.source = core.MediaSource.create_from_storage_file(file)
        elif isinstance(filename, core.MediaSource):
            Audio.source = filename
            Audio.title = ''
        else:
            raise Audio.FileTypeError('No file was specified!')
        item = MediaPlaybackItem(Audio.source)
        Audio.mediaplayer.source = item
        Audio.mediaplayer.play()

        del Audio._stream

        #update the display proprieties
        props = item.get_display_properties()
        props.type = MediaPlaybackType.MUSIC
        props.music_properties.title = os.path.basename(filename)
        item.apply_display_properties(props)

        self._menu_voices(True)

        if keep_alive:
            try:
                session = Audio.mediaplayer.playback_session
                while session.playback_state != MediaPlaybackState.NONE:
                    time.sleep(2)
                return
            except RuntimeError:
                return
            except KeyboardInterrupt:
                Audio().quit()

    class StopMusic(BaseException):
        pass

    def quit():
        try:
            Audio.mediaplayer.close()
            if os.environ.get('DEBUG'):
                print('[DEBUG  ] [Media       ] Audio player destroyed')
        except AttributeError:
            try: 
                from kivy.logger import Logger
                Logger.debug('Audio: No media player initiallized, skipping')
            except ImportError:
                pass

    def play():
        Audio.mediaplayer.play()
        
    def pause():
        Audio.mediaplayer.pause()

    def play_pause():
        try:
            from winrt.windows.media.playback import MediaPlaybackState
            session = Audio.mediaplayer.playback_session.playback_state
            if session == MediaPlaybackState.PLAYING:
                Audio.pause()
            elif session == MediaPlaybackState.PAUSED:
                Audio.play()
            else:
                pass
        except RuntimeError:
            pass

    def play_audio(self, filename, threadded=False):
        import asyncio
        #: Union[str, bytes, PathLike[str], PathLike[bytes], IO]
        #: Optional[str] 
        if threadded:
            asyncio.run(self._play_audio(filename, False))
            #Logger.debug('Audio: audio started at {}'.format(datetime.now()))
            return True
        else:
            #Logger.debug('Audio: audio started at {}'.format(datetime.now()))
            asyncio.run(self._play_audio(filename))
            return True

    def get_pos(self):
        try:
            return round(Audio.mediaplayer.playback_session.position.duration / 10000000)
        except RuntimeError:
            return 0
    
    def set_pos(self, date):
        if isinstance(date, str):
            date = sum(int(x) * 60 ** i for i, x in enumerate(reversed(date.split(':'))))
        from winrt.windows.foundation import TimeSpan
        tm = TimeSpan()
        tm.duration = int(date) * 10000000
        try:
            Audio.mediaplayer.playback_session.position = tm
        except RuntimeError:
            pass
        pass

    def get_total(self):
        if hasattr(Audio, 'duration'):
            return round(Audio.duration.duration / 10000000)
        elif hasattr(Audio, 'source') and hasattr(Audio.source.duration, 'duration'):
            return round(Audio.source.duration.duration / 10000000)
        else:
            return 0

    def is_playing(self):
        try:
            from winrt.windows.media.playback import MediaPlaybackState
            session = Audio.mediaplayer.playback_session.playback_state
            return True if session == MediaPlaybackState.PLAYING else False
        except RuntimeError:
            return False

    def set_volume(self, volume):
        if volume > 1:
            volume /= 100
        try:
            Audio.mediaplayer.volume = volume
        except AttributeError:
            pass

    def get_volume(self):
        try:
            return Audio.mediaplayer.volume * 100
        except AttributeError:
            return 0

    def bind(self, **kwargs):
        for i in list(kwargs.keys()):
            if i in self.events:
                exec('Audio.{} = kwargs[i]'.format(i))
            else:
                raise KeyError('"%s" is not an event! Events are: %s' % (i, self.events)) from None

    class NotSupportedFile(BaseException):
        pass
    
    class FileTypeError(BaseException):
        pass

    # events

    def media_ended(self, *args, **kwargs):
        ''' default media_ended handler '''
        Audio.quit()

    def source_changed(self, *args, **kwargs):
        ''' default source_changed handler '''
        pass

    def volume_changed(self, *args, **kwargs):
        ''' default volume_changed handler '''
        pass

    def playback_state_changed(self, *args, **kwargs):
        ''' default playback_state_changed handler '''
        pass

    def position_changed(self, *args, **kwargs):
        ''' default position_changed handler '''
        pass

    class Queue:

        def __init__(self, queue_definition: object, random: bool = True, repeat: int = 0, threadded: bool = False, daemon: bool = None, **t_kwargs) -> None:
            '''
            Play a music Queue
            ==================
            
            simple usage:

                Select music from a list:
                >>> from audio import Audio
                >>> Audio.Queue(['file1.mp3', 'some\\dir\\file2.mp3'])

                select a music from a file:
                >>> from audio import Audio
                >>> Audio.Queue(file.txt or file.json) #see options to know file format

                select music from a folder:
                >>> from audio import Audio
                >>> folder = Audio.Queue.Folder('C:\\Users\\david\\Music\\Dede')
                >>> Audio.Queue(folder)

            options:

              queue_definition:
                
                the list of files name that must be:
                - list
                - file with .read() support
                - .json file like formatted as {"queue":[somefiles]}
                - Queue.Folder object

              random:

                ramdom choose the order of audios

              threadded (for advanced users):

                Start a thread as Queue manager, with this option you have the full control of queue function:
                for example, stopping a queue:

                >>> from audio import Audio
                >>> Audio.Queue(['file1.mp3', 'some\\dir\\file2.mp3'], threadded=True)
                >>>  
                >>> while True: # <- Leave the process open
                >>>     if input() == '':  # <- on enter press
                >>>         Audio.Queue.quit()  #<- do not pass self parameter
                >>>         break  #<- interrupt the main loop

              other options:

                Audio.Queue.next()      play the next song on in the list
                Audio.Queue.provious()  play the previous song in the list


            '''
            import asyncio
            asyncio.run(Audio().async_initiallize())
            if threadded:
                asyncio.run(self.play_queue_mp(queue_definition, random, repeat, False))
            else:
                asyncio.run(self.play_queue_mp(queue_definition, random, repeat))

        async def play_queue_mp(self, queue_definition: object, random: bool = False, repeat: int = 0, keep_alive: bool = True):
            from winrt.windows.media.playback import MediaPlaybackItem, MediaPlaybackList, MediaPlaybackState
            from winrt.windows.media import core, MediaPlaybackType
            from winrt.windows.storage import StorageFile
            try:
                if environ['queue_playing'] == '1':
                    try:
                        from kivy.logger import Logger
                    except ImportError:
                        import logging as Logger
                    Logger.warning('A queue from automator is already playing. End it to start a new one')
                    return
                else:
                    environ['queue_playing'] = '1'
            except KeyError:
                environ['queue_playing'] = '1'

            try:
                queue = queue_definition.read()
                queue = queue.split('\n')
            except (IOError, OSError, AttributeError):
                if isinstance(queue_definition, str):
                    try:
                        suffix = os.path.basename(queue_definition).split('.')[1]
                        if not os.path.isfile(queue_definition):
                            raise FileNotFoundError('file {} not found!'.format(queue_definition))
                    except IndexError:
                        raise Audio.NotSupportedFile('extension is not supported')

                    if suffix == 'json':
                        from json import load
                        js = load(open(queue_definition, 'r'))
                        queue = js['queue']
                    elif suffix == 'txt':
                        file = open(queue_definition, 'r')
                        queue = file.read().split('\n')
                        file.close()
                elif isinstance(queue_definition, list):
                    queue = queue_definition
                elif isinstance(queue_definition, self.Folder):
                    queue = [os.path.join(self.Folder.folder, f) for f in os.listdir(self.Folder.folder) if os.path.isfile(os.path.join(self.Folder.folder, f))]


            Audio.Queue._list = MediaPlaybackList()
            Audio.Queue._list.shuffle_enabled = random
            print(dir(Audio.Queue._list))
            file_list = {}
            for i in queue:
                if i.endswith('mp3'):
                    f = await StorageFile.get_file_from_path_async(i)
                    file_list[i] = f
            
            for f in file_list:
                metas = os.path.basename(f).split(' - ')
                if len(metas) > 1:
                    artist = metas[0]
                    title = metas[1].split('.')[0]
                else:
                    artist = ''
                    title = metas[0].split('.')[0]
                _item = MediaPlaybackItem(core.MediaSource.create_from_storage_file(file_list[f]))
                prop = _item.get_display_properties()
                prop.type = MediaPlaybackType.MUSIC
                prop.music_properties.title = title
                prop.music_properties.artist = artist
                _item.apply_display_properties(prop)
                Audio.Queue._list.items.append(_item)

            Audio.mediaplayer.source = Audio.Queue._list
            Audio.mediaplayer.play()
            Audio()._menu_voices(True)
            if keep_alive:
                try:
                    session = Audio.mediaplayer.playback_session.playback_state
                    while session != MediaPlaybackState.NONE:
                        time.sleep(2)
                    return
                except (RuntimeError, KeyboardInterrupt):
                    Audio().quit()

        def next():
            Audio.Queue._list.move_next()

        def previous():
            Audio.Queue._list.move_previous()

        def pause():
            Audio.pause()

        def play():
            Audio.play()

        def quit():
            Audio.quit()
            return

        class Folder:
            folder = None
            def __init__(self, folder) -> None:
                Audio.Queue.Folder.folder = folder
