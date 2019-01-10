import os

class PyMacroParser:
    """
        解析宏文件
    """
    tree = []
    branch = tree

    def load(self, f):
        """
        从指定文件中读取CPP宏定义，存为python内部数据，以备进一步解析使用。
        若在初步解析中遇到宏定义格式错误 或 常量类型数据定义错误应该抛出异常。
        :param f:文件路径，文件操作失败抛出异常
        :return:无返回值
        """
        with open(f, 'r', encoding='utf-8') as cpp_file:
            line_list = cpp_file.readlines()

        node_id = 0
        for raw_line in line_list:
            print("当前行:", raw_line)
            # 去掉空行
            if not len(raw_line.strip()) or raw_line[:2] == '//':
                continue
            comment_stack = ['#']
            line = ''
            i = 0
            length = len(raw_line.strip())
            # 分解单词，去除注释信息
            while i < length:
                if raw_line[i:i+2] == '//':
                    break
                # 当前字符是左注释
                elif raw_line[i:i+2] == '/*':
                    # 栈顶字符是'#'或者是左注释
                    if comment_stack[-1] == '#' or comment_stack[-1] == 'L':
                        # 字符入栈
                        comment_stack.append('L')
                # 当前字符是右注释
                elif raw_line[i:i+2] == '*/':
                    # 栈顶字符是左注释
                    if comment_stack[-1] == 'L':
                        comment_stack.pop()
                        i = i + 1
                else:
                    # 如果栈顶不是/*，说明字符有效
                    if comment_stack[-1] != 'L':
                        # 加入字符
                        line = line + str(raw_line[i])
                i = i + 1

            print("去掉注释信息的行:", line)

            # 分解单词
            word_list = line.split(maxsplit=2)
            current_word = word_list[0]
            length = len(word_list)
            i = 0
            while i < length:
                current_word = word_list[i]
                # 单词匹配
                if current_word == '#ifndef':
                    i = i + 1
                    key_name = word_list[i]
                    added_list = [node_id, {key_name: ''}, [], []]
                    self.branch.append(added_list)
                    self.branch = self.branch[-1][3]
                    node_id = node_id + 1
                elif current_word == '#ifdef':
                    i = i + 1
                    key_name = word_list[i]
                    added_list = [node_id, {key_name: ''}, [], []]
                    self.branch.append(added_list)
                    self.branch = self.branch[-1][2]
                    node_id = node_id + 1
                    pass
                elif current_word == '#else':
                    pass
                elif current_word == '#define':
                    i = i + 1
                    key_name = word_list[i]
                    if i + 1 < length:
                        i = i + 1
                        value_name = word_list[i]
                        added_item = [{key_name: value_name}]
                    else:
                        added_item = [{key_name: ''}]
                    self.branch.append(added_item)

                elif current_word == '#endif':
                    pass
                elif current_word == '#undef':
                    pass
                elif current_word[:2] == '/*':
                    pass
                print('tree:', self.tree)
                print('branch:', self.branch)
                i = i + 1

        pass

    def preDefine(self, s):
        """
        输入一堆预定义宏名串，宏名与宏名之间以”;” 分割。
        而空串"" 表示没有任何预定义宏
        :param s:
        :return:
        """
        pass

    def dumpDict(self):
        """
        返回一个dict， 结合类中存储的CPP宏定义与预定义的宏序列，解析输出所有的可用宏到一个字典，
        其中宏名转为字符串后作为字典的key,
        若有与宏名对应的常量转为python数据对象，无常量则存为None, 注意不要返回类中内置的对象的引用。
        :return:
        """
        pass

    def dump(self, f):
        """
        结合类中的CPP宏定义数据与预定义宏序列，解析输出所有可用宏存储到新的CPP源文件，
        f为CPP文件路径，文件若存在则覆盖，文件操作失败抛出异常。
        :param f: f为CPP文件路径
        :return:
        """
        pass
