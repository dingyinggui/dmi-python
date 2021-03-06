#!/usr/bin/env python
# -*- encoding=utf8 -*-

'''
FileName:   parser.py
Author:     Fasion Chan
@contact:   fasionchan@gmail.com
@version:   $Id$

Description:

Changelog:

'''

import platform
import struct

from collections import (
    OrderedDict,
)

from .type import (
    DMIType,
)


class SMBIOSEntryPointParser(object):

    SM_FMT = struct.Struct('=4s4BHB5s5sBHIHB')
    SM_SIZE = SM_FMT.size

    ANCHOR_STRING = b'_SM_'
    ENTRY_POINT_LENGTH = SM_SIZE
    INTERMEDIATE_ANCHOR_STRING = b'_DMI_'

    fields = (
        'anchor_string',
        'entry_point_structure_checksum',
        'entry_point_length',
        'smbios_major_version',
        'smbios_minor_version',
        'maximum_structure_size',
        'entry_point_revision',
        'formatted_area',
        'intermediate_anchor_string',
        'intermediate_checksum',
        'structure_table_length',
        'structure_table_address',
        'number_of_smbios_structures',
        'smbios_bcd_revision',
    )

    def parse(self, content, offset=0):
        content = content[offset:offset+self.SM_SIZE]
        if len(content) != self.SM_SIZE:
            return

        values = self.SM_FMT.unpack(content)
        info = OrderedDict(zip(self.fields, values))

        if info['anchor_string'] != self.ANCHOR_STRING:
            return

        if info['entry_point_length'] != self.ENTRY_POINT_LENGTH:
            return

        if info['intermediate_anchor_string'] != self.INTERMEDIATE_ANCHOR_STRING:
            return

        return info


class DMIParser(object):

    DMI_HEADER_FMT = struct.Struct('@2BH')
    DMI_HEADER_SIZE = DMI_HEADER_FMT.size

    get_parser = DMIType.get_parser

    def parse_string_area(self, content, start=0):
        '''
            Parse string area right after and DMI table item.
            String area is end of two '\0' bytes, strings are stored one by one.
        '''
        idx = content.find(b'\0\0', start)
        strs = content[start:idx].split(b'\0')
        if  platform.python_version_tuple()[0] == '3':
            strs = [s.decode('utf8') for s in strs]
        return idx-start+2, strs

    def iter_dmi_table(self, content):
        '''
        '''
        cursor = 0
        content_size = len(content)

        while cursor < content_size:
            header = content[cursor:cursor+self.DMI_HEADER_SIZE]

            # parse header
            _type, length, _ = self.DMI_HEADER_FMT.unpack(header)

            # load the whole item by length found
            item_content = content[cursor:cursor+length]
            cursor += length

            # parse string area if any
            area_size, strs = self.parse_string_area(content, cursor)
            cursor += area_size

            # get parser for the specific type
            parser = self.get_parser(_type)
            if not parser:
                continue

            # call type parse to do further parsing
            item = parser().parse(content=item_content, strs=strs)
            yield item

    def parse(self, content):
        '''
        '''
        return [
            dmi
            for dmi in self.iter_dmi_table(content=content)
        ]
