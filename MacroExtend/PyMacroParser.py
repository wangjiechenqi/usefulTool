import os
from pprint import pprint
import logging
from path import Path
'''
打印日志
'''
current_path = Path('.')

log_file = current_path / 'xxx.log'
logging.basicConfig(filename=str(log_file), filemode='w', level=logging.DEBUG)


class PyMacroParser:
    """
        解析宏文件
    """
    tree = []
    branch = tree
    node_count = 0
    pre_macro = set()
    macro_list = {}

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
        parent_id = 0
        pos = 1
        comment_stack = ['#']
        for raw_line in line_list:
            print("当前行:", raw_line)
            logging.debug("当前行:" + str(raw_line))
            # 去掉空行
            if not len(raw_line.strip()) or raw_line[:2] == '//':
                logging.debug('not valid line' + str(len(raw_line.strip())) + str(raw_line[:2]))
                continue

            line = ''
            i = 0
            length = len(raw_line.strip())
            logging.debug('length:' + str(length))
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
                        logging.debug('pop L')
                        i = i + 1
                else:
                    # 如果栈顶不是/*，说明字符有效
                    if comment_stack[-1] != 'L':
                        # 加入字符
                        line = line + str(raw_line[i])
                i = i + 1

            print("去掉注释信息的行:", line)
            logging.debug("去掉注释信息的行:" + str(line))

            # 分解单词,主循环
            word_list = line.split(maxsplit=2)
            length = len(word_list)
            i = 0
            while i < length:
                current_word = word_list[i]
                # 单词匹配
                if current_word == '#ifndef':
                    i = i + 1
                    key_name = word_list[i]
                    self.node_count = self.node_count + 1
                    parent_id = node_id
                    node_id = self.node_count
                    node_pos = 2
                    added_list = [{'id': node_id, 'parent': parent_id, 'pos': node_pos}, {key_name: ''}, [], []]
                    self.branch.append(added_list)
                    self.branch = self.branch[-1][3]

                elif current_word == '#ifdef':
                    i = i + 1
                    key_name = word_list[i]
                    self.node_count = self.node_count + 1
                    parent_id = node_id
                    node_id = self.node_count
                    node_pos = 1
                    added_list = [{'id': node_id, 'parent': parent_id, 'pos': node_pos}, {key_name: ''}, [], []]
                    self.branch.append(added_list)
                    self.branch = self.branch[-1][2]

                    pass
                elif current_word == '#else':
                    # 找到当前编号的右节点
                    if node_pos == 1:
                        node_pos = 2
                    else:
                        node_pos = 1
                    result, new_branch = self.__search(self.tree, node_id, node_pos)
                    print('new branch:', str(result), str(new_branch))
                    logging.debug('new branch:' + str(result) + str(new_branch))
                    self.branch = new_branch[3]
                    parent_id = new_branch[1]
                    node_id = new_branch[0]

                elif current_word == '#define':
                    i = i + 1
                    key_name = word_list[i]
                    if i + 1 < length:
                        i = i + 1
                        value_name = word_list[i]
                        added_item = {key_name: value_name}
                    else:
                        added_item = {key_name: ''}
                    self.branch.append(added_item)

                elif current_word == '#endif':
                    # 找到当前编号的右节点
                    result, new_branch = self.__search(self.tree, parent_id, -1)
                    print('new branch:', str(result), str(new_branch))
                    logging.debug('new branch:' + str(result) + str(new_branch))
                    self.branch = new_branch[3]
                    node_pos = new_branch[2]
                    parent_id = new_branch[1]
                    node_id = new_branch[0]
                    pass
                elif current_word == '#undef':
                    i = i + 1
                    added_dict = {}
                    key_name = word_list[i]
                    if i + 1 < length:
                        i = i + 1
                        value_name = word_list[i]
                        added_item = {key_name: value_name}
                    else:
                        added_item = {key_name: ''}
                    added_dict.update(added_item)
                    added_dict.update({'reverse': 1})
                    self.branch.append(added_dict)
                    pass

                print('tree:')
                pprint(self.tree, indent=2)
                logging.debug('tree:')
                logging.debug(self.tree)
                print('branch:')
                pprint(self.branch, indent=2)
                logging.debug('branch:')
                logging.debug(self.branch)
                logging.debug('next node_id:')
                logging.debug(str(node_id))
                print('total_count node_id parent_id:', self.node_count, ' ', node_id, ' ', parent_id)
                i = i + 1

    def preDefine(self, s):
        """
        输入一堆预定义宏名串，宏名与宏名之间以”;” 分割。
        而空串"" 表示没有任何预定义宏
        :param s:
        :return:
        """
        pre_macro_list = s.split(';')
        if self.pre_macro:
            self.pre_macro.clear()
        self.pre_macro.update(pre_macro_list)

        if self.macro_list:
            self.macro_list.clear()
        pre_dict = {}
        tmp_list = list(self.pre_macro)
        item = {}
        for macro in tmp_list:
            item[macro] = ''
            pre_dict.update(item)
        self.macro_list.update(pre_dict)

    def dumpDict(self):
        """
        返回一个dict， 结合类中存储的CPP宏定义与预定义的宏序列，解析输出所有的可用宏到一个字典，
        其中宏名转为字符串后作为字典的key,
        若有与宏名对应的常量转为python数据对象，无常量则存为None, 注意不要返回类中内置的对象的引用。
        :return:
        """
        stack = []
        if self.tree:
            stack.append(self.tree)

        while len(stack):
            current_node = stack.pop()
            for item in current_node:
                if isinstance(item, list):
                    # 获取 分支变量
                    print('item', item)
                    branch_value = item[1]

                    if list(dict(branch_value).keys())[0] in self.pre_macro:
                        stack.append(item[2])
                    else:
                        stack.append(item[3])
                elif isinstance(item, dict):
                    if 'reverse' in item.keys():
                        macro_key = [item_key for item_key in item.keys() if item_key != 'reverse'][0]
                        del self.macro_list[macro_key]
                        self.pre_macro.remove(macro_key)
                    else:
                        self.macro_list.update(item)
                        self.pre_macro.add(list(item.keys())[0])
        print('predefine_macro:')
        pprint(self.pre_macro, indent=2)
        print('macro list:')
        pprint(self.macro_list, indent=2)
        return self.macro_list



    def dump(self, f):
        """
        结合类中的CPP宏定义数据与预定义宏序列，解析输出所有可用宏存储到新的CPP源文件，
        f为CPP文件路径，文件若存在则覆盖，文件操作失败抛出异常。
        :param f: f为CPP文件路径
        :return:
        """
        macro_list = []
        result_dict = self.dumpDict()
        if result_dict:
            key_list = result_dict.keys()
            value_list = result_dict.values()
            for item_key, item_value in zip(key_list, value_list):
                macro_item = '#define' + ' ' + str(item_key) + ' ' + str(item_value) + '\r\n'
                macro_list.append(macro_item)
        with open(f, 'w', encoding='utf-8') as cpp_file:
            cpp_file.writelines(macro_list)


    def __search(self, branch, node_id, node_type):
        """
        搜索指定节点号的根节点、左节点、右节点的引用
        :param node_id: 分支的引用
        :param type: 0:根节点 1 左节点 2 右节点
        :return: 分支的引用
        """
        print('search branch:', node_id, ' ', node_type)
        # pprint(branch, indent=2)
        # logging.debug('search node_id node_type:' + str(node_id) + str(node_type))
        # logging.debug('search:' + str(branch))
        # 分析当前分支
        if not branch:
            return 0, [0, 0, 0, []]
        # 获得左右分支
        sub_branch_list = [item for item in branch if isinstance(item, list)]
        if len(sub_branch_list) == 2:
            print('left:', sub_branch_list[0])
            print('right:', sub_branch_list[1])

        # 获得宏节点
        sub_define_list = [item for item in branch if isinstance(item, dict)]
        current_dict = [item for item in sub_define_list if 'id' in dict(item).keys()]
        print('currrent dict', current_dict)
        if current_dict:
            current_id = current_dict[0]['id']
            current_parent = current_dict[0]['parent']
            current_pos = current_dict[0]['pos']
            # print('current_id, node_id:', current_id, node_id)
            if current_id == node_id:
                print('match ok', node_id)
                # logging.debug('match ok' + str(node_id))
                if node_type in [1, 2]:
                    return 1, [current_id, current_parent, current_pos, sub_branch_list[node_type - 1]]
                # -1
                else:
                    return 1, [current_id, current_parent, current_pos, sub_branch_list[current_pos - 1]]

        # 如果左子树不空
        if len(sub_branch_list) >= 1:
            # 分析左分支
            result, result_branch = self.__search(sub_branch_list[0], node_id, node_type)
            if result != 0:
                return result, result_branch

        # 如果右子树不空
        if len(sub_branch_list) == 2:
            # 分析右分支
            result, result_branch = self.__search(sub_branch_list[1], node_id, node_type)
            if result != 0:
                return result, result_branch

        return 0, [0, 0, 0, []]

