# coding:utf-8
import requests
from lxml import etree
import csv
import re
import urllib
import json
import csv


def format_name(origin_names):
    name_list = re.split(',', origin_names)
    promise_name_list = []
    modify_name_list = [name for name in name_list if len(name) > 0]
    for name in modify_name_list:
        # print('name ', name)
        promise_name = ''
        if name.strip() == 'et al':
            promise_name = name
        else:
            field_list = re.split(' ', name)
            modify_field_list = [field for field in field_list if len(field) > 0]
            for x in modify_field_list:
                # print('x ', x)
                if len(x) == 1:
                    x = x + '. '
                elif x == 'et al':
                    promise_name = x + ' '
                    continue
                elif x == 'al':
                    promise_name = x
                    continue
                promise_name = x + promise_name
                # print('promise name', promise_name)
        promise_name_list.append(promise_name.strip())
    promise_names = ', '.join(promise_name_list)
    # print('dest_name', promise_names)
    return promise_names

paper_names = []
full_refernames = []
with open('reference.csv', 'r', newline='') as csv_file:
    reader = csv.DictReader(csv_file, delimiter='|')
    for row in reader:
        # print('row:', row)
        paper_name = row['reference_name']
        paper_names.append(paper_name)
        paper_id = row['paper_id']

        base_url = 'http://xueshu.baidu.com/usercenter/paper/citation'

        _token = '6cc69dfcce816dac7b3a3497b4d716de081ffb1f36f6abf03106c736c61702b4'
        _ts = '1543043050'
        _sign = '192a2bc3ba601070091ff55839dbaa53'
        url = 'http://link.springer.com/content/pdf/10.1007/978-3-642-59412-0_26.pdf'
        sign = '1904e06c474000a0c8b4b8c5d7c248d3'
        paper_type = 'cite'
        # paper_id = '793f8e087a64fc0e733d3ff9096089ef'
        params_dict = {}
        params_dict['_token'] = _token
        params_dict['_ts'] = _ts
        params_dict['_sign'] = _sign
        params_dict['url'] = url
        params_dict['sign'] = sign
        params_dict['type'] = paper_type
        params_dict['paperid'] = paper_id

        params = urllib.parse.urlencode(params_dict)
        url = base_url + '?%s' % params

        headers = {"User-Agent":
                   'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/68.0.3440.106 Safari/537.36'}
        print('url ', url)
        sourceHtml = requests.get(url, headers=headers)
        # print(sourceHtml.headers, sourceHtml.encoding)
        selector = etree.HTML(sourceHtml.content)
        # //*[@id="feed-main-list"]/li[1]/h5/a
        print(etree.tostring(selector))
        reference_p = selector.xpath('//p')[0].text
        # print('reference:', reference_p, )
        refer_dict = json.loads(reference_p)
        print('special info', json.dumps(refer_dict, indent=4))
        gb_refer_str = refer_dict['sc_GBT7714']
        print('\norigin refer:\n', gb_refer_str)
        fields = re.split('\. ', gb_refer_str)
        for x in fields:
             print('\nx:', x)
        # print(fields[1][1])
        print('\npaper name: \n', paper_name)
        if '[J]' in gb_refer_str:
            print('=J==')
            author_name = format_name(fields[0])
            refer_name = fields[1].strip()
            journal_name = fields[2].strip()
            end_str_list = []
            for field in fields[3:]:
                end_str_list.append(field.strip())
            full_refer = ('. ').join([author_name, refer_name, journal_name] + end_str_list)
            print('\nfull refer:\n', full_refer)
        elif '[M]' in gb_refer_str:
            print('=M==')
            author_name = format_name(fields[0])
            refer_monograph = fields[1].strip()
            refer_monograph_list = re.split('\/\/', refer_monograph)
            refer_name = refer_monograph_list[0].strip()
            monograph_name = refer_monograph_list[1].strip()
            end_str_list = []
            for field in fields[2:]:
                end_str_list.append(field.strip())
            full_refer = ('. ').join([author_name, refer_name, monograph_name] + end_str_list)
            print('\nfull refer:\n', full_refer)
        elif '[C]' in gb_refer_str:
            print('=C==')
            author_name = format_name(fields[0])
            refer_meeting = fields[1].strip()
            refer_meeting_list = re.split('\/\/', refer_meeting)
            refer_name = refer_meeting_list[0].strip()
            meeting_name = refer_meeting_list[1].strip()
            end_str_list = []
            for field in fields[2:]:
                end_str_list.append(field.strip())
            full_refer = ('. ').join([author_name, refer_name, meeting_name] + end_str_list)
            print('\nfull refer:\n', full_refer)
        full_refernames.append(full_refer)

for x, y in zip(paper_names, full_refernames):
    print(' | '.join([x, y]))



