from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.uix.tabbedpanel import TabbedPanel, TabbedPanelItem
from kivy.core.window import Window
from kivy.storage.jsonstore import JsonStore
from kivy.animation import Animation
from kivy.uix.popup import Popup
from kivy.clock import Clock
from datetime import datetime
import webbrowser
import urllib.request
import json

VERSION = "1.0.0"
GITHUB_REPO = "https://github.com/t0rR4/Sahar"
VERSION_URL = f"{GITHUB_REPO}/raw/main/version.json"

class InsulinCalculatorApp(App):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.store = JsonStore('insulin_data.json')
        self.load_data()
        self.update_checked = False

    def load_data(self):
        try:
            self.current_theme = self.store.get('theme')['name']
        except:
            self.current_theme = 'Светлая'
        try:
            self.insulin_factor = self.store.get('insulin_factor')['value']
        except:
            self.insulin_factor = 1.5

    def build(self):
        self.apply_theme()
        self.tabs = TabbedPanel(do_default_tab=False, tab_height=50)

        # --- Калькулятор ---
        self.tab_calc = TabbedPanelItem(text='Калькулятор')
        calc_layout = BoxLayout(orientation='vertical', padding=20, spacing=15)
        self.header = Label(text='Расчёт дозы инсулина', font_size='24sp', bold=True, size_hint_y=0.1)
        self.carbs_per_100 = TextInput(hint_text='Углеводы на 100 г (г)', input_filter='float', multiline=False, size_hint_y=0.1, font_size='18sp')
        self.weight = TextInput(hint_text='Вес порции (г)', input_filter='float', multiline=False, size_hint_y=0.1, font_size='18sp')
        self.calc_btn = Button(text='Рассчитать', size_hint_y=0.1, font_size='18sp')
        self.calc_btn.bind(on_press=self.calculate)
        self.result_dose = Label(text='Доза инсулина: -- ед', font_size='20sp', bold=True, size_hint_y=0.1)
        self.xe_label = Label(text='Хлебные единицы: --', size_hint_y=0.05)
        self.factor_info = Label(text=f'Коэффициент: {self.insulin_factor:.2f} ед/ХЕ', size_hint_y=0.05)
        for w in (self.header, self.carbs_per_100, self.weight, self.calc_btn,
                  self.result_dose, self.xe_label, self.factor_info):
            calc_layout.add_widget(w)
        self.tab_calc.add_widget(calc_layout)
        self.tabs.add_widget(self.tab_calc)

        # --- История ---
        self.tab_history = TabbedPanelItem(text='История')
        history_layout = BoxLayout(orientation='vertical', padding=20, spacing=10)
        self.history_title = Label(text='Последние расчёты (дата, вес, углеводы, ХЕ, инсулин):', font_size='14sp', bold=True, size_hint_y=0.07)
        self.history_container = GridLayout(cols=1, spacing=5, size_hint_y=None)
        self.history_container.bind(minimum_height=self.history_container.setter('height'))
        scroll = ScrollView(size_hint_y=0.85)
        scroll.add_widget(self.history_container)
        history_layout.add_widget(self.history_title)
        history_layout.add_widget(scroll)
        self.tab_history.add_widget(history_layout)
        self.tabs.add_widget(self.tab_history)

        # --- Настройки ---
        self.tab_settings = TabbedPanelItem(text='Настройки')
        settings_scroll = ScrollView(size_hint=(1,1))
        settings_layout = BoxLayout(orientation='vertical', padding=20, spacing=15, size_hint_y=None)
        settings_layout.bind(minimum_height=settings_layout.setter('height'))

        # Тема
        settings_layout.add_widget(Label(text='Цветовая тема:', font_size='18sp', bold=True, size_hint_y=None, height=40))
        theme_box = BoxLayout(spacing=15, size_hint_y=None, height=50)
        self.theme_light = Button(text='Светлая', font_size='16sp')
        self.theme_dark = Button(text='Тёмная', font_size='16sp')
        self.theme_auto = Button(text='Авто', font_size='16sp')
        self.theme_light.bind(on_press=lambda x: self.change_theme('Светлая'))
        self.theme_dark.bind(on_press=lambda x: self.change_theme('Тёмная'))
        self.theme_auto.bind(on_press=lambda x: self.change_theme('Авто'))
        theme_box.add_widget(self.theme_light)
        theme_box.add_widget(self.theme_dark)
        theme_box.add_widget(self.theme_auto)
        settings_layout.add_widget(theme_box)

        # Коэффициент
        settings_layout.add_widget(Label(text='Инсулиновый коэффициент (ед на 1 ХЕ):', font_size='18sp', bold=True, size_hint_y=None, height=40))
        self.factor_input = TextInput(text=str(self.insulin_factor), input_filter='float', multiline=False, size_hint_y=None, height=50, font_size='16sp')
        settings_layout.add_widget(self.factor_input)
        save_btn = Button(text='Сохранить коэффициент', size_hint_y=None, height=60, font_size='16sp')
        save_btn.bind(on_press=self.save_factor)
        settings_layout.add_widget(save_btn)

        # Очистка истории
        clear_btn = Button(text='Очистить историю', size_hint_y=None, height=60, font_size='16sp')
        clear_btn.bind(on_press=self.clear_history)
        settings_layout.add_widget(clear_btn)

        # Версия и обновления
        version_box = BoxLayout(orientation='vertical', spacing=10, size_hint_y=None, height=100)
        self.version_label = Label(text=f'Версия: {VERSION}', font_size='14sp', size_hint_y=0.5)
        update_btn = Button(text='Проверить обновления', size_hint_y=0.5, font_size='14sp')
        update_btn.bind(on_press=self.check_for_updates)
        version_box.add_widget(self.version_label)
        version_box.add_widget(update_btn)
        settings_layout.add_widget(version_box)

        # GitHub ссылка
        github_btn = Button(text='Открыть GitHub репозиторий', size_hint_y=None, height=60, font_size='16sp')
        github_btn.bind(on_press=lambda x: webbrowser.open(GITHUB_REPO))
        settings_layout.add_widget(github_btn)

        settings_scroll.add_widget(settings_layout)
        self.tab_settings.add_widget(settings_scroll)
        self.tabs.add_widget(self.tab_settings)

        # --- Инструкция ---
        self.tab_help = TabbedPanelItem(text='Инструкция')
        help_layout = BoxLayout(orientation='vertical', padding=20, spacing=15)
        help_text = "Всем любителям сахара привет. Приложение очень простое.\n\nСверху открываете настройки, выставляете свой коэффициент, сохраняете и пользуйтесь.\n\nНадеюсь никого не убью своей математикой. Пока."
        help_label = Label(text=help_text, font_size='16sp', halign='left', valign='middle')
        help_label.bind(size=help_label.setter('text_size'))
        help_layout.add_widget(help_label)
        self.tab_help.add_widget(help_layout)
        self.tabs.add_widget(self.tab_help)

        self.load_history()
        self.refresh_theme_buttons()
        self.refresh_all_colors()
        Clock.schedule_once(lambda dt: self.check_for_updates(auto=True), 2)
        return self.tabs

    def apply_theme(self):
        if self.current_theme == 'Тёмная':
            Window.clearcolor = (0.12,0.12,0.12,1)
            self.text_color = (1,1,1,1)
            self.input_bg = (0.2,0.2,0.2,1)
            self.btn_color = (0.3,0.6,0.9,1)
            self.result_color = (0.6,1,0.6,1)
        else:
            Window.clearcolor = (1,1,1,1)
            self.text_color = (0,0,0,1)
            self.input_bg = (0.98,0.98,0.98,1)
            self.btn_color = (0.2,0.6,1,1)
            self.result_color = (0,0.6,0,1)

    def refresh_theme_buttons(self):
        is_light = self.current_theme == 'Светлая'
        for btn, theme in ((self.theme_light,'Светлая'), (self.theme_dark,'Тёмная'), (self.theme_auto,'Авто')):
            active = (theme == self.current_theme)
            btn.background_color = (0.2,0.6,1,1) if active else ((0.9,0.9,0.9,1) if is_light else (0.3,0.3,0.3,1))
            btn.color = (1,1,1,1) if active else ((0,0,0,1) if is_light else (1,1,1,1))

    def refresh_all_colors(self):
        self.tabs.background_color = Window.clearcolor
        self.header.color = self.text_color
        for inp in (self.carbs_per_100, self.weight, self.factor_input):
            inp.background_color = self.input_bg
            inp.foreground_color = self.text_color
            inp.cursor_color = self.text_color
            inp.hint_text_color = (0.5,0.5,0.5,1)
        self.calc_btn.background_color = self.btn_color
        self.calc_btn.color = (1,1,1,1)
        self.result_dose.color = self.result_color
        self.xe_label.color = self.text_color
        self.factor_info.color = self.text_color
        self.history_title.color = self.text_color
        for label in self.history_container.children:
            label.color = self.text_color
        self.tabs.tab_header_label_color = self.text_color
        for tab in self.tabs.tab_list:
            tab.color = self.text_color

    def change_theme(self, theme):
        self.current_theme = theme
        if theme == 'Авто':
            self.current_theme = 'Светлая'
        self.apply_theme()
        self.store.put('theme', name=self.current_theme)
        self.refresh_theme_buttons()
        self.refresh_all_colors()

    def save_factor(self, instance):
        try:
            v = float(self.factor_input.text)
            if v <= 0: raise ValueError
            self.insulin_factor = v
            self.store.put('insulin_factor', value=v)
            self.factor_info.text = f'Коэффициент: {v:.2f} ед/ХЕ'
        except:
            self.factor_input.text = str(self.insulin_factor)

    def clear_history(self, instance):
        content = BoxLayout(orientation='vertical', spacing=10)
        content.add_widget(Label(text='Очистить всю историю расчётов?'))
        btn_box = BoxLayout(orientation='horizontal', size_hint_y=0.3, spacing=10)
        yes_btn = Button(text='Да')
        no_btn = Button(text='Нет')
        btn_box.add_widget(yes_btn)
        btn_box.add_widget(no_btn)
        content.add_widget(btn_box)
        popup = Popup(title='Подтверждение', content=content, size_hint=(0.7,0.4))
        yes_btn.bind(on_press=lambda x: self._do_clear_history(popup))
        no_btn.bind(on_press=popup.dismiss)
        popup.open()

    def _do_clear_history(self, popup):
        self.history_container.clear_widgets()
        self.store.put('history', entries=[])
        popup.dismiss()
        self.refresh_all_colors()

    def check_for_updates(self, instance=None, auto=False):
        def check():
            try:
                with urllib.request.urlopen(VERSION_URL) as response:
                    data = json.loads(response.read().decode())
                    latest = data.get('version', VERSION)
                    if latest != VERSION:
                        msg = f'Доступна новая версия {latest}\n\nСкачать с GitHub?'
                        popup = Popup(title='Обновление', size_hint=(0.8,0.4))
                        content = BoxLayout(orientation='vertical')
                        content.add_widget(Label(text=msg))
                        btn_box = BoxLayout(orientation='horizontal', size_hint_y=0.3, spacing=10)
                        ok_btn = Button(text='Перейти')
                        cancel_btn = Button(text='Отмена')
                        btn_box.add_widget(ok_btn)
                        btn_box.add_widget(cancel_btn)
                        content.add_widget(btn_box)
                        popup.content = content
                        ok_btn.bind(on_press=lambda x: (webbrowser.open(GITHUB_REPO), popup.dismiss()))
                        cancel_btn.bind(on_press=popup.dismiss)
                        popup.open()
                    elif not auto:
                        popup = Popup(title='Обновления', content=Label(text='У вас последняя версия'), size_hint=(0.6,0.3))
                        popup.open()
            except:
                if not auto:
                    popup = Popup(title='Ошибка', content=Label(text='Не удалось проверить обновления'), size_hint=(0.6,0.3))
                    popup.open()
        Clock.schedule_once(lambda dt: check(), 0)

    def add_history_entry(self, carbs_100, weight, total_carbs, xe, dose):
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        text = f'{now} | {weight}г | {carbs_100}г углеводов/100г → всего: {total_carbs:.1f}г, ХЕ: {xe:.2f}, инсулин: {dose:.1f} ед'
        label = Label(text=text, font_size='12sp', halign='left', valign='middle', size_hint_y=None, height=40)
        label.bind(size=label.setter('text_size'))
        label.color = self.text_color
        self.history_container.add_widget(label, index=0)
        label.opacity = 0
        Animation(opacity=1, duration=0.3).start(label)
        if len(self.history_container.children) > 50:
            self.history_container.remove_widget(self.history_container.children[-1])
        self.save_history()

    def save_history(self):
        entries = [child.text for child in self.history_container.children]
        self.store.put('history', entries=entries)

    def load_history(self):
        if self.store.exists('history'):
            entries = self.store.get('history')['entries']
            for entry in entries:
                label = Label(text=entry, font_size='12sp', halign='left', valign='middle', size_hint_y=None, height=40)
                label.bind(size=label.setter('text_size'))
                self.history_container.add_widget(label)
            while len(self.history_container.children) > 50:
                self.history_container.remove_widget(self.history_container.children[-1])

    def calculate(self, instance):
        try:
            carbs_100 = float(self.carbs_per_100.text)
            weight = float(self.weight.text)
            if carbs_100 < 0 or weight < 0:
                raise ValueError
            total_carbs = (carbs_100 * weight) / 100.0
            xe = total_carbs / 12.0
            dose = xe * self.insulin_factor
            self.result_dose.text = f'Доза инсулина: {dose:.1f} ед'
            self.xe_label.text = f'Хлебные единицы: {xe:.2f} ХЕ'
            self.add_history_entry(carbs_100, weight, total_carbs, xe, dose)
        except:
            self.result_dose.text = 'Ошибка: числа >=0'

if __name__ == '__main__':
    InsulinCalculatorApp().run()
