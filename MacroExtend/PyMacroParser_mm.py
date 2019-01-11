# -*- coding: utf-8 -*
class PyMacroParser(object):

    def __init__(self):
        # file input handle
        self.__fis = None
        self.__filename = None
        # for preDefine
        self.__pre_macros = {}
        # all the identifier and value
        self.__macros = {}
        # identifier letters
        self.__id_alphs = ['_']
        # float letters
        self.__float_alphs = ('e', 'E', '.')
        # 16 based number letters
        self.__base16_alphs = ['x', 'X', 'a', 'A',
                               'b', 'B', 'c', 'C',
                               'd', 'D', 'e', 'E',
                               'f', 'F']
        # 8 based number letters
        self.__base8_alphs = ('0', '1', '2', '3',
                              '4', '5', '6', '7')
        # number letters
        self.__digit_alphs = ['-', '+', 'l', 'L', 'f', 'F']
        for ch in xrange(ord('a'), ord('z') + 1):
            self.__id_alphs.append(chr(ch))
        for ch in xrange(ord('A'), ord('Z') + 1):
            self.__id_alphs.append(chr(ch))
        for ch in xrange(ord('0'), ord('9') + 1):
            self.__id_alphs.append(chr(ch))
            self.__digit_alphs.append(chr(ch))
            self.__base16_alphs.append(chr(ch))

    def __readline(self):
        # read line without comments
        line = self.__fis.readline()
        if line == '':
            return
        return self.__remove_comment(line).strip()

    def __remove_comment(self, line):
        # remove comments
        ret = ''
        in_quotes = False
        while True:
            if line is None or line == '':
                return ret
            length = len(line)
            content = None
            for i in xrange(length):
                if i == length - 1:
                    return ret + ' ' + line
                if (line[i] == '"' or line[i] == "'") \
                        and (i == 0 or line[i - 1] != '\\'):
                    in_quotes = not in_quotes
                if not in_quotes and line[i] == '/':
                    if line[i + 1] == '/':
                        return ret + ' ' + line[0:i]
                    if line[i + 1] == '*':
                        ret += ' ' + line[0:i]
                        content = line[i + 2:]
                        break
            contents = content.split('*/', 1)
            while len(contents) < 2:
                line = self.__fis.readline()
                if line == '':
                    self.__fis.close()
                    raise SyntaxError('Missing */')
                contents = line.strip().split('*/', 1)
            line = contents[1]

    def __get_identifier(self, content):
        # split the id and value
        # just read until the character is not a identifier character
        if content is None or content == '' \
                or str.isdigit(content[0]) \
                or content[0] not in self.__id_alphs:
            return None, content
        for i in xrange(len(content)):
            if content[i] not in self.__id_alphs:
                return content[:i], content[i:]
        return content, None

    def __parse_escape(self, value, index):
        # deal with '\'
        # note: limit all value in [0, 255]
        index += 1
        if index == len(value):
            self.__fis.close()
            raise SyntaxError('Unexpected value: ' + value)
        if value[index] == 'a':
            return 0X07, index + 1
        if value[index] == 'b':
            return 0X08, index + 1
        if value[index] == 'f':
            return 0X0C, index + 1
        if value[index] == 'n':
            return 0X0A, index + 1
        if value[index] == 'r':
            return 0X0D, index + 1
        if value[index] == 't':
            return 0X09, index + 1
        if value[index] == 'v':
            return 0X0B, index + 1
        if value[index] == 'x':
            index += 1
            if index < len(value) and value[index] in self.__base16_alphs:
                index += 1
                if index < len(value) and value[index] in self.__base16_alphs:
                    index += 1
                    return int(value[index - 2:index], 16), index
                return int(value[index - 1], 16), index
            return ord(value[index - 1]), index
        if value[index] in self.__base8_alphs:
            index += 1
            if index < len(value) and value[index] in self.__base8_alphs:
                index += 1
                if index < len(value) and value[index] in self.__base8_alphs:
                    index += 1
                    return int(value[index - 3:index], 8) & ((1 << 8) - 1), index
                return int(value[index - 2:index], 8), index
            return int(value[index - 1], 8), index
        return ord(value[index]), index + 1

    def __parse_apos(self, value, index):
        # deal with "'"
        # note: Multicharacter literals => '\01\02\03\04'
        index += 1
        if value[index] == "'":
            self.__fis.close()
            raise SyntaxError('Unexpected value: ' + value)
        length = len(value)
        bits = 0
        ret = 0
        while index < length:
            if value[index] == "'":
                return ret, index + 1
            if bits == 32:
                break
            if value[index] == '\\':
                ch, index = self.__parse_escape(value, index)
                ret += (ch << bits)
            else:
                ret += (ord(value[index]) << bits)
                index += 1
            bits += 8
        self.__fis.close()
        raise SyntaxError('Unexpected value: ' + value)

    def __parse_quotes(self, value, index, unicode=False):
        # deal with '"'
        length = len(value)
        index += 1
        string = ""
        outer = False
        while index < length - 1:
            if outer:
                if str.isspace(value[index]):
                    index += 1
                    continue
                elif value[index] == '"':
                    index += 1
                    outer = False
                    continue
                elif unicode:
                    return string.decode('utf-8'), index
                else:
                    return string, index
            if value[index] == '\\':
                num, index = self.__parse_escape(value, index)
                string += chr(num)
                continue
            if value[index] == '"':
                outer = True
                index += 1
                continue
            string += value[index]
            index += 1
        if index == len(value) or value[index] != '"':
            self.__fis.close()
            raise SyntaxError('Missing " in ' + value)
        if unicode:
            return string.decode('utf-8'), index + 1
        else:
            return string, index + 1

    def __parse_tuple(self, value, index):
        # deal with initialize list
        # note: {} and {1,} is ok but {1,,} not
        index += 1
        tpl = []
        v = None
        length = len(value)
        while index < length:
            if str.isspace(value[index]):
                index += 1
                continue
            if value[index] == '}':
                if v is not None:
                    tpl.append(v)
                return tuple(tpl), index + 1
            if value[index] == ',':
                if v is None:
                    self.__fis.close()
                    raise SyntaxError('Unexpected value: ' + value)
                tpl.append(v)
                v = None
                index += 1
                continue
            v, index = self.__parse_value(value, index)
        self.__fis.close()
        raise SyntaxError('Missing } in ' + value)

    def __parse_digit(self, value, index):
        length = len(value)
        # deal with sign
        sign = 1
        last_sign = False
        if value[index] == '-':
            last_sign = True
        while index < length:
            if not last_sign and value[index] == '+':
                last_sign = not last_sign
                index += 1
            elif last_sign and value[index] == '-':
                last_sign = not last_sign
                index += 1
                sign = -sign
            else:
                break
        if index == length or value[index] == '+' or value[index] == '-':
            self.__fis.close()
            raise SyntaxError('Unexpected value: ' + value)
        pass
        # deal with data
        s_index = index
        is_float = False
        while index < length:
            if value[index] in self.__float_alphs:
                is_float = True
                index += 1
                continue
            if value[index] in self.__digit_alphs \
                    or value[index] in self.__base16_alphs:
                index += 1
                continue
            break
        if index - s_index > 2 and value[s_index] == '0' \
                and (value[s_index + 1] == 'X' or value[s_index + 1] == 'x'):
            if value[index - 1] != 'l' and value[index - 1] != 'L':
                return int(value[s_index:index], 16) * sign, index
            else:
                return int(value[s_index:index - 1], 16) * sign, index
        if is_float:
            if value[index - 1] not in ('f', 'F', 'L', 'l'):
                return float(value[s_index:index]) * sign, index
            else:
                return float(value[s_index:index - 1]) * sign, index
        if value[s_index] == '0':
            if value[index - 1] != 'l' and value[index - 1] != 'L':
                return int(value[s_index:index], 8) * sign, index
            else:
                return int(value[s_index:index - 1], 8) * sign, index
        else:
            if value[index - 1] != 'l' and value[index - 1] != 'L':
                return int(value[s_index:index]) * sign, index
            else:
                return int(value[s_index:index - 1]) * sign, index

    def __parse_value(self, value, index):
        # parse the value for define
        if value is None or value == '':
            return None, index
        length = len(value)
        while index < length:
            if str.isspace(value[index]):
                index += 1
                continue
            if value[index] == "'":
                return self.__parse_apos(value, index)
            if value[index] == '"':
                return self.__parse_quotes(value, index)
            if value[index:index + 2] == 'u"':
                return self.__parse_quotes(value, index + 1)
            if value[index:index + 3] == 'u8"':
                return self.__parse_quotes(value, index + 2)
            if value[index:index + 2] == 'L"':
                return self.__parse_quotes(value, index + 1, True)
            if value[index] == '{':
                return self.__parse_tuple(value, index)
            if value[index] == '.' or str.isdigit(value[index]) \
                    or value[index] == '-' or value[index] == '+':
                return self.__parse_digit(value, index)
            if value[index] in self.__id_alphs:
                identifier = self.__get_identifier(value[index:])[0]
                if identifier == 'true' and identifier not in self.__macros:
                    return True, index + 4
                if identifier == 'false' and identifier not in self.__macros:
                    return False, index + 5
                return self.__macros[identifier], index + len(identifier)
            self.__fis.close()
            raise SyntaxError('Unexpected value: ' + value)
        return None, index

    def __parse_ifdef(self, is_def, else_used, is_filter):
        # parse #if[n]def macro
        """
        :param is_def: whether the next block needs parse
        :param else_used: whether #else is used
        :param is_filter: whether it's in inactive preprocessor block
        :return:
        """
        if is_def and not is_filter:
            is_filter = True
            content = self.__parse_line()
        else:
            content = self.__parse_with_filter()
        if content == '#else':
            if else_used:
                self.__fis.close()
                raise SyntaxError('Unexpected #else')
            else:
                self.__parse_ifdef(not is_def, True, is_filter)
        elif content == '#endif':
            return
        else:  # end of file or something else
            self.__fis.close()
            raise SyntaxError('Mismatched #if/#endif pair')

    def __parse_header(self, line):
        # skip the first word, assume it is '#'
        # parse the macro at head
        # note: #    define is ok
        header = line[0]
        for i in xrange(1, len(line)):
            if str.isspace(line[i]):
                if len(header) > 1:
                    return header, line[i + 1:].strip()
                continue
            header += line[i]
        return header, ''

    def __parse_with_filter(self):
        # parse the inactive preprocessor block
        # note: you can skip most of the data
        # except comment and (#ifdef, #ifndef, #else,
        # #endif) macros.(just parse macros is ok, no need for identifier)
        while True:
            line = self.__readline()
            if line is None:
                return  # end of file
            if line == '':
                continue
            header, content = self.__parse_header(line)
            if header.startswith('#else') \
                    and (len(header) == 5
                         or header[5] not in self.__id_alphs):
                # back to last level
                return '#else'
            elif header.startswith('#endif') \
                    and (len(header) == 6
                         or header[6] not in self.__id_alphs):
                # back to last level
                return '#endif'
            elif header == '#ifdef' or header == '#ifndef':
                self.__parse_ifdef(False, False, True)

    def __parse_line(self):
        # parse the active preprocessor block
        while True:
            line = self.__readline()
            if line is None:
                return  # end of file
            if line == '':
                # No data in this line
                continue
            header, content = self.__parse_header(line)
            if header.startswith('#else') \
                    and (len(header) == 5
                         or header[5] not in self.__id_alphs):
                # back to last level
                return '#else'
            if header.startswith('#endif') \
                    and (len(header) == 6
                         or header[6] not in self.__id_alphs):
                # back to last level
                return '#endif'
            pass
            identifier, value = self.__get_identifier(content)
            if identifier is None:
                self.__fis.close()
                raise SyntaxError("Unexpected identifier: " + content)
            if header == '#define':
                self.__macros[identifier] = self.__parse_value(value, 0)[0]
            elif header == '#undef':
                self.__macros.pop(identifier, '')
            elif header == '#ifdef':
                if identifier in self.__macros:
                    self.__parse_ifdef(True, False, False)
                else:
                    self.__parse_ifdef(False, False, False)
            elif header == '#ifndef':
                if identifier not in self.__macros:
                    self.__parse_ifdef(True, False, False)
                else:
                    self.__parse_ifdef(False, False, False)
            else:
                # other wrong data at begin
                self.__fis.close()
                raise SyntaxError('Unexpected value: ' + header)

    def __dump_tuple(self, tpl):
        if len(tpl) == 0:
            return '{}'
        string = '{'
        for value in tpl:
            string += self.__dump_value(value) + ', '
        return string[:-2] + '}'

    def __dump_value(self, value):
        if value is None:
            return ''
        if isinstance(value, bool):
            return str(value).lower()
        if isinstance(value, unicode):
            # remember to convert escape character
            return 'L"' + value.encode('utf-8')\
                .replace('\\', r'\\')\
                .replace('\a', r'\a')\
                .replace('\b', r'\b')\
                .replace('\f', r'\f')\
                .replace('\n', r'\n')\
                .replace('\r', r'\r')\
                .replace('\t', r'\t')\
                .replace('\v', r'\v')\
                .replace("\'", r"\'")\
                .replace('\"', r'\"')\
                + '"'
        if isinstance(value, str):
            return '"' + value\
                .replace('\\', r'\\')\
                .replace('\a', r'\a')\
                .replace('\b', r'\b')\
                .replace('\f', r'\f')\
                .replace('\n', r'\n')\
                .replace('\r', r'\r')\
                .replace('\t', r'\t')\
                .replace('\v', r'\v')\
                .replace("\'", r"\'")\
                .replace('\"', r'\"')\
                + '"'
        if isinstance(value, (int, long, float)):
            return str(value)
        if isinstance(value, tuple):
            return self.__dump_tuple(value)

    def load(self, filename):
        self.__filename = filename
        self.__fis = open(filename, 'r')
        self.__macros = self.__pre_macros.copy()
        pass
        line = self.__parse_line()
        # may be return #else or #endif
        if line is not None:
            self.__fis.close()
            raise SyntaxError('Unexpected ' + line)
        print('File load successfully!')
        self.__fis.close()

    def dump(self, filename):
        fos = open(filename, 'w+')
        for identifier, value in self.__macros.items():
            fos.write('#define ' + identifier
                      + ' ' + self.__dump_value(value)
                      + '\n')
        fos.close()

    def preDefine(self, s):
        # assume s is correct identifier set
        self.__pre_macros = {}
        identifiers = s.split(';')
        for identifier in identifiers:
            # identifier cannot be empty
            if len(identifier) > 0:
                self.__pre_macros[identifier] = None
        self.load(self.__filename)

    def dumpDict(self):
        # there is no variable data in values
        # so shallow copy is OK.
        return self.__macros.copy()

    
