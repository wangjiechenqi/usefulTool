# coding:utf-8
import requests
from lxml import etree
import csv
import re

url = "https://www.smzdm.com/fenlei/nuanshoubao/"
url_list = ['https://www.smzdm.com/fenlei/nuanshoubao',
            'https://www.smzdm.com/fenlei/nuanshoubao/p2/#feed-main'
            'https://www.smzdm.com/fenlei/nuanshoubao/p3/#feed-main',
            'https://www.smzdm.com/fenlei/nuanshoubao/p4/#feed-main',
            'https://www.smzdm.com/fenlei/nuanshoubao/p5/#feed-main',
            'https://www.smzdm.com/fenlei/nuanshoubao/p6/#feed-main',
            'https://www.smzdm.com/fenlei/nuanshoubao/p7/#feed-main']

headers = {"User-Agent":
           'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/68.0.3440.106 Safari/537.36'}

# 字典列表
notebook_list = []


for url in url_list:


    sourceHtml = requests.get(url, headers=headers)
    # print(sourceHtml.headers, sourceHtml.encoding)
    selector = etree.HTML(sourceHtml.content)
    # //*[@id="feed-main-list"]/li[1]/h5/a
    # print(etree.tostring(selector))
    price_list = selector.xpath('//*[@id="feed-main-list"]/li/h5/a')
    for index, price in enumerate(price_list):
        notebook = {}
        # print('index, price: ', index, etree.tostring(price, encoding='unicode'))

        href = price.xpath('@href')[0]

        name = price.xpath('text()')
        format_name = ' '.join(name[1].split())
        item_list = price.xpath('span')
        format_price = item_list[1].text
        # if re.findall(format_price, r'^[^\d]\w+'):
        #    format_price = re.findall(format_price, r'^\w+$')[0]
        # print('价格：', re.sub(r'\D', '', format_price))
        format_price1 = re.sub(r'\D', '', format_price)
        # print('item_list', len(item_list), item_list)
        # print('index: ', index)
        # print('href: ', href)
        # print('name: ', )
        print(','.join([str(index), format_name, format_price, format_price1, href]))
        notebook['name'] = format_name
        notebook['price'] = format_price
        notebook['price1'] = int(format_price1)
        notebook['href'] = href
        notebook_list.append(notebook)

# 排序第三个字段
notebook_list.sort(key=lambda k: (k.get('price1', 0)))

with open('..\output\\nuanshoubao.csv', 'w', newline='', encoding='utf-8') as csvfile:
    fieldnames = ['name', 'href', 'price', 'price1']
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    writer.writeheader()

    for row in notebook_list:
        writer.writerow(row)



