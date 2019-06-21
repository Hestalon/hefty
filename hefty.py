#! python3

import json
import os
import re
from argparse import ArgumentParser
from typing import List, Text, TextIO, Union


class Heft(object):

    def __init__(self):
        super(Heft, self).__init__()
        self.configs: dict = dict()
        self.themes: dict = dict()
        self.styles: dict = dict()
        self.filter_file: Union[TextIO, None] = None
        self.matcher = re.compile('.*\\.json')

    def write_line(self, *text: Text) -> None:
        # write the text finished with a new line
        if len(text):
            self.filter_file.write(''.join(text))
        self.filter_file.write('\n')

    @staticmethod
    def format_comment(*text: Text) -> Text:
        return '# {}'.format(' '.join(text))

    def write_comment(self, *text: Text) -> None:
        self.write_line(self.format_comment(*text))

    def write_comment_header(self, lines: List[List[Text]], separator: Text):
        self.write_comment(separator * 120)
        for line in lines:
            self.write_comment(*line)
        self.write_comment(separator * 120)

    @staticmethod
    def add_entry(data: dict, name: Text, value: Union[Text, int, List], escape: bool = False) -> None:
        if value is not None:
            # make it a list if not already
            if isinstance(value, Text) or isinstance(value, int):
                value = [value]
            # make sure everything is text
            value = map(Text, value)
            # escape if necessary
            if escape:
                value = map(lambda x: '"{}"'.format(Text(x)), value)
            # join all types in quotes and spaces
            data[name] = ' '.join(value)

    @staticmethod
    def read_file(path: Text) -> dict:
        print('reading file', path)
        with open(path) as file:
            data: dict = json.load(file)
            return data

    def walk_files(self, folder: Text, consumer: classmethod) -> None:
        for subdir, dirs, files in os.walk(folder):
            for file in files:
                if self.matcher.match(file):
                    path: Text = os.path.join(subdir, file)
                    consumer(path)

    def handle_config(self, path: Text) -> None:
        config: dict = self.read_file(path)
        self.configs = {**self.configs, **config}

    def handle_theme(self, path: Text) -> None:
        theme: dict = self.read_file(path)
        self.themes = {**self.themes, **theme}

    def handle_style(self, path: Text) -> None:
        style: dict = self.read_file(path)
        self.styles = {**self.styles, **style}

    def read_configs(self, config: Text, style: Text, theme: Text) -> None:
        self.walk_files(os.path.join('configs', config), self.handle_config)
        self.walk_files(os.path.join('styles', style), self.handle_style)
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
        extends: Union[Text, List] = theme.pop('extends', None)
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

    def generate_filter(self, path: Text):
        os.makedirs('dist', exist_ok=True)
        self.filter_file = open(os.path.join('dist', path + '.filter'), 'w')

        sorted_config: List = sorted(self.configs.items(), key=lambda x: x[1].get('priority', 0))
        self.write_introduction(sorted_config)
        # sort all configs based on the priority
        for (chapter, definition) in sorted_config:
            self.write_definitions(chapter, definition)
        self.filter_file.close()

    def write_introduction(self, sorted_config: List):
        self.write_comment('Generated with HEFTY')
        # generate the table of content
        toc: List[List[Text]] = []
        for (chapter, definition) in sorted_config:
            priority = definition.get('priority', 0)
            toc.append(['{:>8}'.format('[[{}]]'.format(priority)), chapter])
            section_id: int = priority
            for (name, section) in definition.get('section', {}).items():
                section_id += 1
                toc.append(['{:>8}'.format('[{}]'.format(section_id)), name])
        self.write_comment_header(toc, '*')

    def get_style(self, theme: dict, theme_type: Text, style_type: Text) -> Text:
        theme_name: Text = theme.get(theme_type)
        if theme_name is not None:
            value = self.styles.get(style_type, {}).get(theme_name)
            if value is not None:
                # found a value so format it and format it as string
                return '{:20}{}'.format(Text(value), self.format_comment(theme_name))

    def write_definitions(self, chapter: Text, definition: dict) -> None:
        # TODO build the definition and gather the TOC here too => don't need to iterate twice
        print('generating chapter', '"{}"'.format(chapter))

        # header
        priority = definition.get('priority', 0)
        self.write_comment_header([['[[{}]]'.format(priority), chapter]], '=')

        section_id: int = priority
        for (name, section) in definition.get('section', {}).items():
            section_id += 1
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
            self.add_entry(actions, 'SetBorderColor', self.get_style(theme, 'border', 'color'))
            self.add_entry(actions, 'SetTextColor', self.get_style(theme, 'text', 'color'))
            self.add_entry(actions, 'SetBackgroundColor', self.get_style(theme, 'background', 'color'))
            self.add_entry(actions, 'SetFontSize', self.get_style(theme, 'size', 'size'))
            self.add_entry(actions, 'PlayAlertSoundPositional', self.get_style(theme, 'sound', 'sound'))
            self.add_entry(actions, 'DisableDropSound', self.get_style(theme, 'dropSound', 'dropSound'))
            self.add_entry(actions, 'MinimapIcon', self.get_style(theme, 'icon', 'icon'))
            self.add_entry(actions, 'PlayEffect', self.get_style(theme, 'beam', 'beam'))

            if len(actions) == 0 and len(conditions) == 0:
                print('ignoring, no actions and conditions found')
                continue

            # now write the actual values to the file
            self.write_comment_header([['{:10}'.format('Section:'), '[{}]'.format(section_id), name],
                                       ['{:10}'.format('Theme:'), section.get('theme')]], '-')

            self.write_line(display)
            for (key, value) in conditions.items():
                self.write_line('\t{:30}{}'.format(key, value))

            for (key, value) in actions.items():
                self.write_line('\t{:30}{}'.format(key, value))

            self.write_line()


if __name__ == '__main__':
    parser = ArgumentParser(description='generation of a loot filter')
    parser.add_argument('--config', help='name of the configuration folder', default='hestalon')
    parser.add_argument('--style', help='name of the style file', default='hestalon')
    parser.add_argument('--theme', help='name of the theme folder', default='hestalon')
    parser.add_argument('--file', help='name of the resulting file', default='hestalon')

    args = parser.parse_args()

    gen = Heft()
    gen.read_configs(args.config, args.style, args.theme)
    gen.generate_filter(args.file)
