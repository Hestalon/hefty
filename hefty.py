#! python3

from argparse import ArgumentParser
import json
import os
import re

from typing import Text, TextIO, Union


class Heft(object):

    def __init__(self):
        super(Heft, self).__init__()
        self.configs: dict = dict()
        self.themes: dict = dict()
        self.styles: dict = dict()
        self.filter_file: Union[TextIO, None] = None

    def write_line(self, *text: Text) -> None:
        # write the text finished with a new line
        if len(text):
            self.filter_file.write(''.join(text))
        self.filter_file.write('\n')

    @staticmethod
    def format_comment(*text: Text) -> Text:
        return '# {}'.format(' '.join(text))

    @staticmethod
    def add_entry(data: dict, name: Text, value: Union[Text, int, list],
                  escape: bool = False) -> None:
        if value is not None:
            # make it a list if not already
            if isinstance(value, Text) or isinstance(value, int):
                value = [value]
            # make sure everything is a str
            value = map(str, value)
            # escape if necessary
            if escape:
                value = map(lambda x: '"{}"'.format(str(x)), value)
            # join all types in quotes and spaces
            data[name] = ' '.join(value)

    @staticmethod
    def read_file(path: Text) -> dict:
        print('reading file', path)
        with open(path) as file:
            data: dict = json.load(file)
            return data

    @staticmethod
    def walk_files(folder: Text, consumer: classmethod, pattern: Text = '.*\\.json') -> None:
        matcher = re.compile(pattern)
        for subdir, dirs, files in os.walk(folder):
            for file in files:
                if matcher.match(file):
                    path: Text = os.path.join(subdir, file)
                    consumer(path)

    def handle_config(self, path) -> None:
        config: dict = self.read_file(path)
        self.configs = {**self.configs, **config}

    def handle_theme(self, path) -> None:
        theme: dict = self.read_file(path)
        self.themes = {**self.themes, **theme}

    def read_configs(self, config: Text, style: Text, theme: Text) -> None:
        self.walk_files(os.path.join('configs', config), self.handle_config)
        self.walk_files('styles', self.handle_theme, '{}\\.json'.format(style))
        self.walk_files(os.path.join('themes', theme), self.handle_theme)
        # finished reading themes now extend the themes
        self.themes = dict((theme, self.get_theme(theme)) for theme in self.themes)

    def get_theme(self, name: Text) -> Union[dict, None]:
        # update themes
        theme: dict = self.themes.get(name)
        if theme is None:
            print('theme "{}" not defined'.format(name))
            return theme
        # check if this is extending other themes
        # this also removes the extends to prevent further computation of the inheritance
        extends: Union[Text, list] = theme.pop('extends', None)
        if extends is None:
            # no extension just return it
            print('theme "{}" found'.format(name))
            return theme

        if isinstance(extends, Text):
            extends = [extends]
        for extension in extends:
            # get over each parent theme and update this theme
            print('theme "{}" extends "{}"'.format(name, extension))
            parent_theme = self.get_theme(extension)
            if parent_theme is None:
                continue
            theme = {**parent_theme, **theme}
        self.themes[name] = theme
        print('theme "{}" found and updated'.format(name))
        return theme

    def generate_filter(self, path: str):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        self.filter_file = open(path, 'w')
        # sort all configs based on the priority
        for (chapter, definition) in sorted(self.configs.items(), key=lambda x: x[1].get('priority', 0)):
            self.write_definitions(chapter, definition)
        self.filter_file.close()

    def write_definitions(self, chapter: Text, definition: dict) -> None:
        print('generating chapter', '"{}"'.format(chapter))

        filler_length: int = 120
        # header
        self.write_line(self.format_comment('=' * filler_length))
        self.write_line(self.format_comment('[[{}]]'.format(definition.get('priority', 0)), chapter))
        self.write_line(self.format_comment('=' * filler_length))

        for (name, section) in definition.get('section', {}).items():
            section = {**definition, **section}
            theme = self.themes.get(section.get('theme'))
            if theme is None:
                print('tried to use theme', '"{}"'.format(section.get('theme')), 'but it\'s not defined')
                continue
            # by default show it
            display = 'Show' if section.get('show', True) else 'Hide'

            # adding the conditions
            conditions: dict = dict()
            self.add_entry(conditions, 'ItemLevel', section.get('itemLevel'))
            self.add_entry(conditions, 'DropLevel', section.get('dropLevel'))
            self.add_entry(conditions, 'Quality', section.get('quality'))
            self.add_entry(conditions, 'Rarity', section.get('rarity'))
            self.add_entry(conditions, 'Class', section.get('class'), True)
            self.add_entry(conditions, 'BaseType', section.get('type'), True)
            self.add_entry(conditions, 'Prophecy', section.get('prophecy'), True)
            self.add_entry(conditions, 'Sockets', section.get('sockets'))
            self.add_entry(conditions, 'LinkedSockets', section.get('links'))
            self.add_entry(conditions, 'SocketGroup', section.get('socketColors'))
            self.add_entry(conditions, 'Height', section.get('height'))
            self.add_entry(conditions, 'Width', section.get('width'))
            self.add_entry(conditions, 'HasExplicitMod', section.get('mod'), True)
            self.add_entry(conditions, 'AnyEnchantment', section.get('enchanted'))
            self.add_entry(conditions, 'HasEnchantment', section.get('enchantment'), True)
            self.add_entry(conditions, 'StackSize', section.get('stackSize'))
            self.add_entry(conditions, 'GemLevel', section.get('gemLevel'))
            self.add_entry(conditions, 'Identified', section.get('identified'))
            self.add_entry(conditions, 'Corrupted', section.get('corrupted'))
            self.add_entry(conditions, 'ElderItem', section.get('elder'))
            self.add_entry(conditions, 'ShaperItem', section.get('shaper'))
            self.add_entry(conditions, 'FracturedItem', section.get('fractured'))
            self.add_entry(conditions, 'SynthesisedItem', section.get('synthesised'))
            self.add_entry(conditions, 'ShapedMap', section.get('shaped'))
            self.add_entry(conditions, 'MapTier', section.get('tier'))

            # adding the actions
            actions: dict = dict()
            self.add_entry(actions, 'SetBorderColor', theme.get('border'))
            self.add_entry(actions, 'SetTextColor', theme.get('text'))
            self.add_entry(actions, 'SetBackgroundColor', theme.get('background'))
            self.add_entry(actions, 'SetFontSize', theme.get('size'))
            self.add_entry(actions, 'PlayAlertSoundPositional', theme.get('sound'))
            self.add_entry(actions, 'DisableDropSound', theme.get('dropSound'))
            self.add_entry(actions, 'MinimapIcon', theme.get('icon'))
            self.add_entry(actions, 'PlayEffect', theme.get('beam'))

            if len(actions) == 0 and len(conditions) == 0:
                print('ignoring, no actions and conditions found')
                continue

            # now write the actual values to the file
            self.write_line(self.format_comment('-' * filler_length))
            self.write_line(self.format_comment('{:10}'.format('Section:'), name))
            self.write_line(self.format_comment('{:10}'.format('Theme:'), section.get('theme')))
            self.write_line(self.format_comment('-' * filler_length))
            self.write_line(display)

            self.write_line('\t', self.format_comment('conditions'))
            for (key, value) in conditions.items():
                self.write_line('\t{:30} {}'.format(key, value))

            self.write_line('\t', self.format_comment('actions'))
            for (key, value) in actions.items():
                self.write_line('\t{:30} {}'.format(key, value))

            self.write_line()


if __name__ == '__main__':
    parser = ArgumentParser(description='generation of a loot filter')
    parser.add_argument('--config', help='name of the configuration folder', default='hestalon')
    parser.add_argument('--style', help='name of the style file', default='hestalon')
    parser.add_argument('--theme', help='name of the theme folder', default='hestalon')

    args = parser.parse_args()

    gen = Heft()
    gen.read_configs(args.config, args.style, args.theme)
    gen.generate_filter('dist/hestalon.filter')
