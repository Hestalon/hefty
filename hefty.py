#! python3

import json
import logging
import os
import re
from argparse import ArgumentParser
from functools import reduce
from typing import List, Text, TextIO, Union

logging.basicConfig(format='%(levelname)-10s%(message)s', level=logging.INFO)


class Hefty(object):
    operators: List[Text] = ["<", "<=", ">", ">=", "="]

    def __init__(self):
        super(Hefty, self).__init__()
        self.config: dict = dict()
        self.conditions: dict = dict()
        self.themes: dict = dict()
        self.styles: dict = dict()
        self.filter_file: Union[TextIO, None] = None

    def read_configs(self, config: Text, strict: Text, condition: Text, style: Text, theme: Text) -> None:
        self.config = self.read_files(self.walk_files(os.path.join('configs', config), strict))
        self.styles = self.read_files(self.walk_files(os.path.join('styles', style)))
        self.themes = self.read_files(self.walk_files(os.path.join('themes', theme)))
        self.conditions = self.read_files(self.walk_files(os.path.join('conditions', condition)))

    def generate_filter(self, folder: Text, file: Text):
        folder = os.path.expandvars(folder)
        os.makedirs(folder, exist_ok=True)
        file = os.path.join(folder, file + '.filter')
        self.filter_file = open(file, 'w')
        logging.info('writing to "{}"'.format(file))

        toc: List[Text] = []
        content: List[Text] = []
        chapter_id: int = 0
        for (chapter_name, chapter) in self.config.items():
            logging.info('generating chapter "{}"'.format(chapter_name))
            chapter_id += 1000
            chapter_header = '{:>9} {}'.format('[[{}]]'.format(chapter_id), chapter_name)
            toc.append(chapter_header)
            content.extend(self.format_header(chapter_header, '='))
            content.append('')

            section_id: int = chapter_id
            for (section_name, section) in chapter.items():
                logging.info('generating section "{}"'.format(section_name))
                section_id += 1

                # make everything to a list for iteration
                if type(section) is dict:
                    section = [section]

                section_header = '{:>8}  {}'.format('[{}]'.format(section_id), section_name)
                toc.append(section_header)
                content.extend(self.format_header(section_header, '-'))

                for part in section:
                    conditions: dict = dict()
                    actions: dict = dict()
                    condition = self.get_extended_data('condition', part.pop('condition', None), self.conditions)
                    if condition is not None:
                        # adding the conditions
                        self.add_entry(conditions, 'ItemLevel', condition.get('itemLevel'))
                        self.add_entry(conditions, 'DropLevel', condition.get('dropLevel'))
                        self.add_entry(conditions, 'Class', condition.get('class'), True)
                        self.add_entry(conditions, 'BaseType', condition.get('type'), True)
                        self.add_entry(conditions, 'Rarity', condition.get('rarity'))
                        self.add_entry(conditions, 'Sockets', condition.get('sockets'))
                        self.add_entry(conditions, 'LinkedSockets', condition.get('links'))
                        self.add_entry(conditions, 'SocketGroup', condition.get('socketColors'))
                        self.add_entry(conditions, 'Height', condition.get('height'))
                        self.add_entry(conditions, 'Width', condition.get('width'))
                        self.add_entry(conditions, 'StackSize', condition.get('stackSize'))
                        self.add_entry(conditions, 'Quality', condition.get('quality'))
                        self.add_entry(conditions, 'GemLevel', condition.get('gemLevel'))
                        self.add_entry(conditions, 'Prophecy', condition.get('prophecy'), True)
                        self.add_entry(conditions, 'Identified', condition.get('identified'))
                        self.add_entry(conditions, 'Corrupted', condition.get('corrupted'))
                        self.add_entry(conditions, 'ElderItem', condition.get('elder'))
                        self.add_entry(conditions, 'ShaperItem', condition.get('shaper'))
                        self.add_entry(conditions, 'HasExplicitMod', condition.get('mod'), True)
                        self.add_entry(conditions, 'AnyEnchantment', condition.get('enchanted'))
                        self.add_entry(conditions, 'HasEnchantment', condition.get('enchantment'), True)
                        self.add_entry(conditions, 'FracturedItem', condition.get('fractured'))
                        self.add_entry(conditions, 'SynthesisedItem', condition.get('synthesised'))
                        self.add_entry(conditions, 'ShapedMap', condition.get('shaped'))
                        self.add_entry(conditions, 'MapTier', condition.get('tier'))

                    theme = self.get_extended_data('theme', part.pop('theme', None), self.themes)
                    if theme is not None:
                        # adding the actions

                        # handle the colors special for contrast calculation
                        text_color = self.get_style(theme, 'text', 'color')
                        background_color = self.get_style(theme, 'background', 'color')
                        border_color = self.get_style(theme, 'border', 'color')
                        self.check_contrast('text', text_color, background_color)
                        self.check_contrast('border', border_color, background_color)

                        self.add_entry(actions, 'SetTextColor', text_color)
                        self.add_entry(actions, 'SetBackgroundColor', background_color)
                        self.add_entry(actions, 'SetBorderColor', border_color)

                        self.add_entry(actions, 'SetFontSize', self.get_style(theme, 'size', 'size'))
                        self.add_entry(actions, 'PlayEffect', self.get_style(theme, 'beam', 'beam'))
                        self.add_entry(actions, 'MinimapIcon', self.get_style(theme, 'icon', 'icon'))
                        self.add_entry(actions, 'PlayAlertSoundPositional', self.get_style(theme, 'sound', 'sound'))
                        self.add_entry(actions, 'DisableDropSound', self.get_style(theme, 'dropSound', 'dropSound'))

                    if len(actions) == 0 and len(conditions) == 0:
                        logging.warning('section "{}" ignored, no actions and conditions found'.format(section_name))
                        continue

                    # append the configuration first the Show/Hide
                    content.append('Show' if part.get('show', True) else 'Hide')
                    # followed by the filtering conditions
                    for (key, value) in conditions.items():
                        content.append('\t{:30}{}'.format(key, value))
                    # finally the styling
                    for (key, value) in actions.items():
                        content.append('\t{:30}{}'.format(key, value))
                    # and a empty line
                    content.append('')

        # write the header
        self.write_lines(self.format_header('Generated with HEFTY (https://github.com/Hestalon/hefty)', '*'))
        # write the TOC
        self.write_lines(self.format_header(toc, '*'))
        self.write_line('')
        # write the filter
        self.write_lines(content)
        self.filter_file.close()

    def write_lines(self, lines: List[Text]) -> None:
        [self.write_line(line) for line in lines]

    def write_line(self, *text: Text) -> None:
        # write the text finished with a new line
        if len(text):
            self.filter_file.write(''.join(text))
        self.filter_file.write('\n')

    @staticmethod
    def format_comment(*text: Text) -> Text:
        return '# {}'.format(' '.join(text))

    def format_header(self, lines: Union[Text, List[Text]], separator: Text):
        if type(lines) is Text:
            lines = [lines]
        lines.insert(0, separator * 120)
        lines.append(separator * 120)
        return [self.format_comment(line) for line in lines]

    @staticmethod
    def add_entry(data: dict, name: Text, value: Union[Text, int, bool, List[Text]], escape: bool = False) -> None:
        if value is not None:
            # make it a list if not already
            if type(value) is Text or type(value) is int or type(value) is bool:
                value = [value]
            # escape if necessary otherwise convert it to text
            value = map(lambda x: '"{}"'.format(x) if escape else Text(x), value)
            # join all types in quotes and spaces
            data[name] = ' '.join(value)

    def read_files(self, files: List[Text]) -> dict:
        # read all files and merge everything together
        return reduce(lambda l, r: dict(**l, **r), map(self.read_file, files))

    @staticmethod
    def read_file(path: Text) -> dict:
        logging.info('reading file "{}"'.format(path))
        with open(path) as file:
            data: dict = json.load(file)
            return data

    @staticmethod
    def walk_files(folder: Text, file_name: Text = '.*') -> List[Text]:
        result = []
        matcher = re.compile('{}\\.json'.format(file_name))
        for subdir, dirs, files in os.walk(folder):
            for file in files:
                if matcher.match(file):
                    result.append(os.path.join(subdir, file))
        return result

    def validate_numeric(self, value: Union[int, Text], value_validation: classmethod) -> bool:
        # TODO currently not used
        if type(value) is Text:
            split = value.split()
            if len(split) == 2:
                if split[0] not in self.operators:
                    logging.error('validation failed for "{}"'.format(value))
                    return False
                value = split[1]
            elif len(split) != 1:
                logging.error('validation failed for "{}"'.format(value))
                return False
        return value_validation(value)

    def get_extended_data(self, data_type: Text, name: Text, data: dict) -> Union[dict, None]:
        if name is None:
            logging.info('{} is not defined'.format(data_type))
            return None
        result: dict = data.get(name)
        if result is None:
            logging.warning('{} "{}" not defined'.format(data_type, name))
            return None
        # check if this is extending
        # this also removes the extends to prevent further computation of the inheritance
        extends: Union[Text, List] = result.pop('extends', None)
        if extends is None:
            # no extension just return it
            logging.debug('{} "{}" found'.format(data_type, name))
            return result

        if type(extends) is Text:
            extends = [extends]
        for extension in extends:
            # get over each parent theme and update this theme
            logging.debug('{} "{}" extends "{}"'.format(data_type, name, extension))
            parent = self.get_extended_data(data_type, extension, data)
            if parent is None:
                continue
            result = {**parent, **result}
        data[name] = result
        logging.debug('{} "{}" found and updated'.format(data_type, name))
        return result

    def get_style(self, theme: dict, theme_type: Text, style_type: Text) -> Text:
        theme_name: Text = theme.get(theme_type)
        if theme_name is not None:
            return self.styles.get(style_type, {}).get(theme_name)

    def check_contrast(self, contrast_type: Text, foreground: Text, background: Text):
        if foreground is None or background is None:
            return
        # https://www.w3.org/TR/WCAG21/#dfn-contrast-ratio
        # https://www.w3.org/TR/WCAG21/#contrast-minimum
        lfg = self.luminance(foreground) + .05
        lbg = self.luminance(background) + .05
        ratio = lfg / lbg if lfg > lbg else lbg / lfg
        if ratio < 4.5:
            logging.warning(
                'contrast ratio for "{}" should be at least 4.5 but is {:.3}'.format(contrast_type, ratio))

    @staticmethod
    def luminance(color: Text):
        # https://www.w3.org/TR/WCAG21/#dfn-relative-luminance
        rgb = [float(x) for x in color.split()]
        for i, value in enumerate(rgb):
            if i < 3:
                value /= 255
                rgb[i] = value / 12.92 if value < .03928 else pow((value + .055) / 1.055, 2.4)
        return .2126 * rgb[0] + .7152 * rgb[1] + .0722 * rgb[2]


if __name__ == '__main__':
    parser = ArgumentParser(description='generation of a loot filter')
    parser.add_argument('--config', help='name of the configuration folder', default='hestalon')
    parser.add_argument('--strict', help='name of the strictness in the configuration folder', default='regular')
    parser.add_argument('--condition', help='name of the condition folder', default='hestalon')
    parser.add_argument('--style', help='name of the style file', default='hestalon')
    parser.add_argument('--theme', help='name of the theme folder', default='hestalon')
    parser.add_argument('--folder', help='name of the resulting folder', default='dist')
    parser.add_argument('--file', help='name of the resulting file', default='hestalon')

    args = parser.parse_args()

    gen = Hefty()
    gen.read_configs(args.config, args.strict, args.condition, args.style, args.theme)
    gen.generate_filter(args.folder, '{}-{}'.format(args.file, args.strict))
