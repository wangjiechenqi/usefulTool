# coding:utf-8
import requests
from lxml import etree

url = "https://www.smzdm.com/fenlei/bijibendiannao/"

headers = {"User-Agent":
           'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/68.0.3440.106 Safari/537.36'}
sourceHtml = requests.get(url, headers=headers)
print(sourceHtml.headers, sourceHtml.encoding)
selector = etree.HTML(sourceHtml.content)
# //*[@id="feed-main-list"]/li[1]/h5/a
print(etree.tostring(selector))
price_list = selector.xpath('//*[@id="feed-main-list"]/li[1]/h5/a')
for price in price_list:
    print('price: ', etree.tostring(price, encoding='unicode'))
    for item in price:
        print('price: ', etree.tostring(price, encoding='unicode'))