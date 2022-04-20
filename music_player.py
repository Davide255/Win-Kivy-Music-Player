''' 
Kivy music player from Automator
================================

github: https://github.com/Davide255/Automator 

module from core.graphics

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

import comtypes, os, sys

comtypes.CoUninitialize()

try:
    from winrt import _winrt
    _winrt.init_apartment()
except RuntimeError:
    if not os.environ.get('NO_MEDIA_PLAYER_WINRT_MESSAGE'):
        print('winrt not initiallized!')

from kivymd.app import MDApp
from kivymd.uix.slider import MDSlider
from kivymd.uix.button import MDFloatingActionButton, MDIconButton
from kivy.uix.screenmanager import ScreenManager, Screen
from kivymd.uix.boxlayout import MDBoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivymd.uix.progressbar import MDProgressBar
from kivymd.uix.label import MDLabel
from kivy.core.window import Window
from kivy.uix.image import Image
from kivymd.app import MDApp
from kivy.clock import Clock
from kivy.properties import BooleanProperty, StringProperty, ListProperty

try:
    from core.graphics import pakedWidget
except ImportError:
    from kivymd.uix.toolbar import MDToolbar
    class pakedWidget:
        def boxlayout(self, **kwargs):
            from kivy.uix.boxlayout import BoxLayout
            bl = BoxLayout(**kwargs)
            if not kwargs.get('orientation'):
                bl.orientation = 'vertical'
            return bl

        def toolbar(self, title, **kwargs):
            if kwargs.get('left_action_item_bypass') == True:
                kwargs.pop('left_action_item_bypass')
            tb = MDToolbar(**kwargs)
            tb.title = title
            return tb

from threading import Thread

import time, logging
try:
    from core.audio.Audio import Audio
    from core.audio.AudioHelpers import *
except ModuleNotFoundError:
    from Audio import Audio
    from AudioHelpers import *

Audio().bind(media_ended = lambda *args: setattr(GUI.play_pause_button, 'icon', 'play'),
             source_changed = lambda *args: GUI.source_changed(),
             position_changed = lambda *args: setattr(GUI.time_slider, 'value', Audio().get_pos()) \
                if GUI.time_slider.value != sum(int(x) * 60 ** i for i, x in enumerate(reversed(GUI.total_time_label.text.split(':')))) and GUI.time_slider.pressed == False else None,
             playback_state_changed = lambda *args: setattr(GUI.play_pause_button, 'icon', 'play' if not Audio().is_playing() else 'pause'))


import asyncio, sys
if sys.version_info >= (3, 8, 0): #If python version is > than 3.8.0 asyncio must set his policy to WindowsSelectorEventLoopPolicy()
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

class Slider(MDSlider):
    def collide_point(self, x, y):
        return self.x <= x <= self.right and self.y+250 <= y <= self.top-250

class DownloadProgressBar(MDProgressBar):
    hide = BooleanProperty(True)
    def collide_point(self, x, y):
        return self.x <= x <= self.right and self.y+300 <= y <= self.top-300

class Volume_Icon(MDIconButton):
    def collide_point(self, x, y):
        return self.x <= x <= self.right and self.y+300 <= y <= self.top-300

class GUI(MDBoxLayout):

    orientation = StringProperty('vertical')
    left_actions = ListProperty()

    def __init__(self, **kwargs):
        super(GUI, self).__init__(**kwargs)
        self.build()
        self.register_event_type('on_backward_button_pressed')
        self.register_event_type('on_backward_button_released')
        self.register_event_type('on_forward_button_pressed')
        self.register_event_type('on_forward_button_released')

    def build(self):
        Window.bind(on_drop_file=self.on_drop_file)
        if bool(os.environ.get('FORCE_DARK')):
            try:
                MDApp.get_running_app().theme_cls.theme_style = 'Dark'
            except AttributeError:
                from kivymd.theming import ThemeManager
                self.theme_cls = ThemeManager()
                self.theme_cls.theme_style = 'Dark'
        toolbar = pakedWidget().toolbar('Music Player', left_action_item_bypass=True)
        if self.left_actions:
            toolbar.left_action_items = self.left_actions
        toolbar.right_action_items = [["music-note", lambda x: self.open_menu(x)]]
        self.add_widget(toolbar)
    
        mainbox = MDBoxLayout(orientation='vertical')
        mainFrame = FloatLayout()
        
        GUI.sc = time.strftime("%M:%S", time.gmtime(0))
        GUI.secs = sum(int(x) * 60 ** i for i, x in enumerate(reversed(GUI.sc.split(':'))))

        image = Image(source=os.path.realpath('datab\\graphic\\icon-music.png') if os.path.isfile(os.path.realpath('datab\\graphic\\icon-music.png')) else "D:\Automator\datab\graphic\icon-music.png")
        image.size_hint = None, None
        image.size = 325, 325
        if False:
            image.pos_hint = {'center_x': .77, 'center_y': .70}
        else:
            image.pos_hint = {'center_x': .5, 'center_y': .70}
        mainFrame.add_widget(image)

        if False:
            GUI.tree_view = tree_view(start_directory='music',size_hint=(.54, .60), pos_hint={'center_y':.7, 'center_x':.269})
            mainFrame.add_widget(GUI.tree_view)
        else:
            GUI.tree_view = None

        GUI.title = MDLabel(text=Audio.title if hasattr(Audio, 'title') else 'No suorce', halign='center', font_style='H6')
        GUI.title.pos_hint = {'center_x':.5, 'center_y':.35}

        GUI.loading = MDLabel(text='Loading...', halign='center')
        GUI.loading.pos_hint = {'center_x':.5, 'center_y':.30}
        GUI.loading.opacity = 0

        mainFrame.add_widget(GUI.title)
        mainFrame.add_widget(GUI.loading)

        GUI.time_slider = Slider()
        GUI.time_slider.min = 0
        GUI.time_slider.max = GUI.secs+1
        GUI.time_slider.hint = False
        GUI.time_slider.pos_hint = {'center_x':.5, 'center_y':.25}
        GUI.time_slider.pressed = False
        GUI.time_slider.bind(value=lambda *args: GUI.on_slider_move(args[0]))
        GUI.time_slider.bind(on_touch_down=lambda *args: self.slider_pressed(args[1]))
        GUI.time_slider.bind(on_touch_up=lambda *args: self.slider_released(args[1], args[0].value))
        mainFrame.add_widget(GUI.time_slider)

        GUI.total_time_label = MDLabel(text=GUI.sc, halign='center')
        GUI.total_time_label.pos_hint = {'center_x':.95, 'center_y':.19}
        mainFrame.add_widget(GUI.total_time_label)

        class BakwordsButton(MDIconButton):

            def on_press(self):
                #return GUI.dispatch('on_backward_button_pressed')
                pass

            def on_release(self):
                #return GUI.dispatch('on_backward_button_released')
                pass

        GUI.backwords_button = BakwordsButton(icon='skip-backward')
        GUI.backwords_button.pos_hint = {'center_x':.43, 'center_y':.17}
        GUI.backwords_button.size_hint = None, None
        GUI.backwords_button.size = 37, 37
        mainFrame.add_widget(GUI.backwords_button)

        GUI.play_pause_button = MDFloatingActionButton(icon='play')
        GUI.play_pause_button.pos_hint = {'center_x':.5, 'center_y':.17}
        GUI.play_pause_button.bind(on_release=lambda *args: Audio.play_pause())
        mainFrame.add_widget(GUI.play_pause_button)

        class FastForwardButton(MDIconButton):
            def on_press(self):
                #return GUI.dispatch('on_forward_button_pressed')
                pass

            def on_release(self):
                #return GUI.dispatch('on_forward_button_released')
                pass

        GUI.fast_forward_button = FastForwardButton(icon='skip-forward')
        GUI.fast_forward_button.pos_hint = {'center_x':.57, 'center_y':.17}
        GUI.fast_forward_button.size_hint = None, None
        GUI.fast_forward_button.size = 37, 37
        mainFrame.add_widget(GUI.fast_forward_button)

        GUI.current_time_label = MDLabel(text='00:00', halign='center')
        GUI.current_time_label.pos_hint = {'center_x':.05, 'center_y':.19}
        mainFrame.add_widget(GUI.current_time_label)

        volume_low_icon = Volume_Icon(icon='volume-low')
        volume_low_icon.pos_hint = {'center_x':.72, 'center_y':.085}
        mainFrame.add_widget(volume_low_icon)

        GUI.volume_slider = Slider(min=0, max=100, hint=True, step=5)
        GUI.volume_slider.value = 100
        GUI.volume_slider.pos_hint = {'center_x':.84, 'center_y':.09}
        GUI.volume_slider.size_hint_x = .2
        GUI.volume_slider.bind(value=self.volume_slider_handler)
        mainFrame.add_widget(GUI.volume_slider)

        volume_high_icon = Volume_Icon(icon='volume-high')
        volume_high_icon.pos_hint = {'center_x':.95, 'center_y':.085}
        mainFrame.add_widget(volume_high_icon)

        GUI.download_button = MDIconButton(icon='arrow-down-circle')
        GUI.download_button.pos_hint = {'center_x':.04, 'center_y':.085}
        GUI.download_button.bind(on_release=lambda *args: [Clock.schedule_once(lambda *args: asyncio.run(self.download()))])
        mainFrame.add_widget(GUI.download_button)

        GUI.downlod_progress = DownloadProgressBar()
        GUI.downlod_progress.pos_hint = {'center_x':.12, 'center_y':.088}
        GUI.downlod_progress.size_hint_x = .1
        GUI.downlod_progress.opacity = 0
        GUI.downlod_progress.bind(hide=lambda *args: \
            setattr(GUI.downlod_progress, 'opacity', GUI.title.opacity if not GUI.downlod_progress.hide else 0))
        mainFrame.add_widget(GUI.downlod_progress)

        mainbox.add_widget(mainFrame)

        self.add_widget(mainbox)

        self.create_menu()

        return self

    def volume_slider_handler(self, slider, value):
        Audio().set_volume(value)

    def on_drop_file(self, window, filename, *args):
        Audio().play_audio(filename.decode('utf-8'), True)
        GUI.title.text = os.path.basename(filename.decode('utf-8')).split('.')[0]
        time.sleep(.1)
        GUI.total_time_label.text = time.strftime("%M:%S", time.gmtime(Audio().get_total()))

    def open_menu(self, button):
        self.menu.caller = button
        self.menu.open()

    def create_menu(self):
        from kivy.metrics import dp
        from kivymd.uix.menu import MDDropdownMenu

        menu_items = [
            {
                "viewclass": "OneLineListItem",
                "text": f"Open a new file",
                "on_press": lambda *args: Clock.schedule_once(lambda *args: asyncio.run(self.load_song())),
                "on_release": lambda *args: self.menu.dismiss()
            },
            {
                "viewclass": "OneLineListItem",
                "text": f"New stream",
                "on_press": lambda *args: self.new_stream(),
                "on_release": lambda *args: self.menu.dismiss()
            }
        ]

        self.menu = MDDropdownMenu(
            items=menu_items,
            width_mult=4,
            max_height=dp(100),
        )

    def new_stream(self, _stream_key: str = None):
        if _stream_key:
            return self.parse(_stream_key)
        from kivymd.uix.dialog import MDDialog
        from kivymd.uix.textfield import MDTextField
        from kivymd.uix.button import MDFlatButton
        from kivy.clock import Clock

        cont_cls = pakedWidget().boxlayout(size_hint_y = None,
                                           height = "40dp")
        
        cont_cls.add_widget(MDTextField(hint_text = 'url:'))

        self.dialog = MDDialog(
            title = 'Enter a youtube link:',
            type="custom",
            content_cls=cont_cls,
            buttons=[
                    MDFlatButton(
                        text="CANCEL",
                        on_press = lambda *args: [self.dialog.dismiss()]
                    ),
                    MDFlatButton(
                        text="OK",
                        on_press= lambda *args: [self.dialog.dismiss(), 
                        Clock.schedule_once(lambda *arsg: self.parse(cont_cls.children[0].text), .5)]
                    ),
            ],   
        )

        self.dialog.open()

    def parse(self, text):

        if text != '':
            try:
                Audio.pause()
            except (RuntimeError, AttributeError):
                asyncio.run(Audio().async_initiallize())

            GUI.time_slider.value = 0

            url = text
            Audio.from_stream(Youtube(url).get_stream())
            Audio.play()

            GUI.download_button.disabled = False

            _waiter = Clock.schedule_interval(lambda *args: [setattr(GUI.loading, 'opacity', 0), Clock.unschedule(_waiter)] if Audio().is_playing() else setattr(GUI.loading, 'opacity', GUI.title.opacity), .5)

    async def download(self, *args):
        if Audio().is_stream():
            from tkinter import Tk
            from tkinter.filedialog import asksaveasfilename
            Tk().withdraw()
            try:
                from core.graphics import MUSICDIR
            except ImportError:
                MUSICDIR = 'C:\\Music'

            if False:
                from winrt.windows.storage.pickers import FileOpenPicker

                pk = FileOpenPicker()
                pk.file_type_filter.append('.m4a')
                
                try:
                    f = await pk.pick_single_file_async()
                except RuntimeError:
                    import win32api
                    print(win32api.GetLastError())
                    os._exit(0)
            else:
                f = asksaveasfilename(filetypes=[('Music file', '.m4a')], title='Select the save path', initialdir=MUSICDIR, defaultextension='.m4a')

            if f:
                if not f.endswith('.m4a'):
                    f += '.m4a'
            
                f = os.path.realpath(f)

                try:
                    from libs.LibWin import IconStatusIter
                    GUI.ici = IconStatusIter()
                    GUI.ici.init(MDApp.get_running_app().title, None)
                except ImportError:
                    logging.warning('Iconstatus not aviable')
                if Audio().is_stream():
                    Thread(target=Audio().get_stream().download_audio, args=(f, True, GUI.dlcb), daemon=True).start()
            return

    def dlcb(total, recvd, ratio, rate, eta):
        if GUI.downlod_progress.max != total:
            try:
                GUI.downlod_progress.hide = False
            except TypeError:
                pass
            GUI.downlod_progress.max = total
        elif total == round(recvd):
            if hasattr(GUI, 'ici'):
                GUI.ici.quit()
                del GUI.ici
            try:
                GUI.downlod_progress.hide = True
            except TypeError:
                pass
        else:
            if hasattr(GUI, 'ici'):
                GUI.ici.setProgress(round(recvd), total)
            GUI.downlod_progress.value = round(recvd)


    async def load_song(self):
        from tkinter import Tk
        from tkinter.filedialog import askopenfilename
        Tk().withdraw()
        from winrt.windows.media.core import MediaSource
        from winrt.windows.storage import StorageFile
        from winrt.windows.media.playback import MediaPlaybackItem

        try:
            from core.graphics import MUSICDIR
        except ImportError:
            MUSICDIR = 'C:\\Music'

        f = askopenfilename(filetypes=(('Music file', '.mp3'), ('Music file', '.m4a')), initialdir=MUSICDIR)

        if f:
            try:
                Audio.pause()
            except (RuntimeError, AttributeError):
                await asyncio.create_task(Audio().async_initiallize())
            if hasattr(Audio, 'duration'):
                del Audio.duration
            file = await StorageFile.get_file_from_path_async(os.path.realpath(f))
            source = MediaSource.create_from_storage_file(file)
            Audio.mediaplayer.source = MediaPlaybackItem(source)
            Audio.title = file.display_name
            Audio.source = source
            Audio.play()
            time.sleep(.5)
            GUI.download_button.disabled = True
            try:
                MDApp.get_running_app().eleve()
            except AttributeError:
                import win32gui
                win32gui.ShowWindow(win32gui.FindWindow(MDApp.get_running_app().title), 1)


    def slider_pressed(self, motion):
        if GUI.time_slider.pos[1] * -1 - 20 < motion.pos[1] < GUI.time_slider.pos[1] * -1 + 20:
            GUI.time_slider.pressed = True
        else:
            try:
                GUI.time_slider.value = Audio().get_pos()
            except AttributeError:
                pass

    def slider_released(self, motion, value):
        if GUI.time_slider.pos[1] * -1 - 20 < motion.pos[1] < GUI.time_slider.pos[1] * -1 + 20 or GUI.time_slider.pressed == True:
            Audio().set_pos(value)
            GUI.time_slider.pressed = False
        else:
            try:
                GUI.time_slider.value = Audio().get_pos()
            except AttributeError:
                pass

    def on_slider_move(slider):
        GUI.current_time_label.text = time.strftime("%M:%S", time.gmtime(slider.value))

    def source_changed():
        time.sleep(.5)
        GUI.title.text = Audio.title
        GUI.time_slider.max = Audio().get_total()
        GUI.total_time_label.text = time.strftime("%M:%S", time.gmtime(Audio().get_total()))

    def on_backward_button_pressed(*args, **kwargs):
        pass

    def on_backward_button_released(*args, **kwargs):
        pass

    def on_forward_button_pressed(*args, **kwargs):
        pass

    def on_forward_button_released(*args, **kwargs):
        pass

class Music_Player_GUI(MDApp):

    def build(self):
        
        self.title = 'Music Player'
        app = Screen(name='main')
        gui = GUI()
        gui.bind(on_forward_button_pressed=lambda *args: print('pressed'))
        app.add_widget(gui)
        gui.new_stream('https://www.youtube.com/watch?v=LZMDuDvP3r4')
        self.sm = ScreenManager()
        self.sm.add_widget(app)

        return self.sm

if __name__ == '__main__':
    try:
        Music_Player_GUI().run()
    except KeyboardInterrupt:
        pass
    Audio.quit()
