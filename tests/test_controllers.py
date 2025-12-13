import builtins
from ui.controllers.gallery import GalleryController
from ui.controllers.menu_actions import MenuActions
from ui.controllers.window_state import WindowStateController


class PrefsMock:
    def __init__(self):
        self.store = {}

    def get(self, k, default=None):
        return self.store.get(k, default)

    def set(self, k, v):
        self.store[k] = v


def test_gallery_controller_behavior():
    class FakeGallery:
        def __init__(self):
            self.loaded = None
            self.refreshed = False

        def load_characters(self, chars):
            self.loaded = chars

        def _refresh_display(self):
            self.refreshed = True

    class FakeMainPaned:
        def __init__(self):
            self.inserted = False
            self.removed = False

        def insert(self, idx, frame, weight=0):
            self.inserted = True

        def forget(self, frame):
            self.removed = True

    class FakeCharsTab:
        def __init__(self):
            self.added = None

        def add_character_from_gallery(self, name):
            self.added = name

    class App:
        pass

    app = App()
    app.character_gallery = FakeGallery()
    app.gallery_frame = object()
    app.main_paned = FakeMainPaned()
    app.prefs = PrefsMock()
    app.characters_tab = FakeCharsTab()

    scheduled = {'ok': False}

    def schedule():
        scheduled['ok'] = True

    app.schedule_preview_update = schedule

    controller = GalleryController(app)

    chars = {'Alice': {}}
    controller.load_characters(chars)
    assert app.character_gallery.loaded is chars

    controller.apply_theme({'bg': '#fff'})
    assert app.character_gallery.refreshed

    controller.toggle_visibility(True, chars)
    assert app.main_paned.inserted

    controller.toggle_visibility(False)
    assert app.main_paned.removed

    controller.on_character_selected('Bob')
    assert app.characters_tab.added == 'Bob'
    assert scheduled['ok'] is True


def test_menu_actions_delegation():
    class App:
        def __init__(self):
            self.called = []

        def _save_preset(self):
            self.called.append('save')

        def _load_preset(self):
            self.called.append('load')

        def _export_config(self):
            self.called.append('export')

        def _import_config(self):
            self.called.append('import')

        def _undo(self):
            self.called.append('undo')
            return True

        def _redo(self):
            self.called.append('redo')
            return True

        def _clear_all_characters(self):
            self.called.append('clear')

        def _reset_all_outfits(self):
            self.called.append('reset')

        def _apply_same_pose_to_all(self):
            self.called.append('apply_pose')

        def _increase_font(self):
            self.called.append('inc')

        def _decrease_font(self):
            self.called.append('dec')

        def _reset_font(self):
            self.called.append('reset_font')

        def randomize_all(self):
            self.called.append('randomize')

        def _change_theme(self, t):
            self.called.append(('theme', t))

        def _toggle_auto_theme(self):
            self.called.append('auto')

        def _on_closing(self):
            self.called.append('closing')

    app = App()
    ma = MenuActions(app)
    ma.save_preset()
    ma.load_preset()
    ma.export_config()
    ma.import_config()
    ma.undo()
    ma.redo()
    ma.clear_all_characters()
    ma.reset_all_outfits()
    ma.apply_same_pose_to_all()
    ma.increase_font()
    ma.decrease_font()
    ma.reset_font()
    ma.randomize_all()
    ma.change_theme('Dark')
    ma.toggle_auto_theme()
    ma.on_closing()

    assert 'save' in app.called and 'load' in app.called and ('theme', 'Dark') in app.called


def test_window_state_controller_restore_and_save():
    class FakeRoot:
        def __init__(self):
            self._geom = None
            self._state = 'normal'

        def geometry(self, g=None):
            if g is None:
                return self._geom or '800x600+100+100'
            self._geom = g

        def state(self, s=None):
            if s is None:
                return self._state
            self._state = s

    class App:
        pass

    app = App()
    app.root = FakeRoot()
    prefs = PrefsMock()
    prefs.set('window_geometry', '1024x768+10+10')
    prefs.set('window_state', 'zoomed')
    app.prefs = prefs

    wsc = WindowStateController(app)
    restored = wsc.restore_geometry_and_state()
    assert restored is True

    # test save
    app.root.geometry('123x234+1+2')
    app.root.state('normal')
    wsc.save_geometry_and_state()
    assert prefs.get('window_geometry') == '123x234+1+2'
    assert prefs.get('window_state') == 'normal'
