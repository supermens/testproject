import csv
import json
import random
import time

import requests
from user_agent import get_ua
from lxml import etree
# 从ua池中获取USER-AGENT信息
header = get_ua()
headers = {
            'USER-AGENT':header
        }
sleep_time = random.randint(4,6)
class DoubanSpider():
    # url = "https://movie.douban.com/subject/30331149/comments?status=P"
    # base_url = "https://movie.douban.com/subject/30331149/comments?"
    """
       https://movie.douban.com/subject/30331149/comments?start=20&limit=20&sort=new_score&status=P
       https://movie.douban.com/subject/30331149/comments?start=40&limit=20&sort=new_score&status=P
    """


    def __init__(self):
        pass

    def get_url(self):
        # 获取选电影中的电影地址
        start_url = "https://movie.douban.com/j/new_search_subjects?sort=U&range=0,10&tags=&start=0"
        response = requests.get(start_url)
        hjson = json.loads(response.content)
        for info in hjson["data"]:
            url = info["url"]
            movie_name = info["title"]
            print("正在保存%s电影评论..."%movie_name)
            saved_movie = ["大黄蜂", "狗十三", "毒液：致命守护者", "无名之辈", "白蛇：缘起",
                           "我不是药神", "“大”人物", "无双","头号玩家","泰坦尼克号","密室逃生",
                           "碟中谍6：全面瓦解","这个杀手不太冷","大江大河"]
            if movie_name in saved_movie:
                print("%s已经获取完毕" % movie_name)
            else:
                self.start_spider(movie_name,url)
                time.sleep(sleep_time)
            # yield (url,self.start_spider())

        # print(type(html))

    def start_spider(self,movie_name,url):
        # 获取每一页评论的网页信息
        for page in range(0,11):
            # url = f"https://movie.douban.com/subject/26752088/comments?start={20*page}"
            comment_url = f"{url}comments?start={20*page}"
            print(comment_url)  # 评论页面的url
            time.sleep(sleep_time)
            html = self.get_html(comment_url)  # 获取评论页面信息
            print("正在保存%s电影信息的第%d页评论数据" % (movie_name,int(page + 1)))
            # saved_movie = ["大黄蜂","狗十三","毒液：致命守护者","无名之辈","白蛇：缘起","我不是药神","“大”人物","无双"]
            # if movie_name in saved_movie:
            #     print("%s已经获取完毕"%movie_name)
            #     return None
            self.parse_html(movie_name,html)
            print("休息5秒，防止被反爬")
            time.sleep(sleep_time)

    def get_html(self,url):
        # 获取指定的url界面，返回的etree解析后的页面
        proxy = {
            "http":"119.101.115.88:9999",
            # "https":"115.151.7.29:9999",
        }
        response = requests.get(url=url, headers=headers,proxies=proxy)
        if response.status_code == 200:
            charset = response.headers.get("Content-Type").split(";")[-1].split("=")[-1]
            response.encoding = charset
            html = etree.HTML(response.text)
            return html

    def parse_html(self,movie_name,html):
        # 解析评论页面的信息
        comments = html.xpath('//div[@class="comment-item"]')  # 一页中的所有评论对象
        movie_time = html.xpath('//span[@class="attrs"]/p[5]/text()')[-1].strip().split("分")[0]
        movie_show = html.xpath('//span[@class="attrs"]/p[6]/text()')[-1].strip().split("(")[0]

        for comment in comments:
            items = {}
            star = comment.xpath('.//span[contains(@class,"rating")]/@title')  # 评分
            user_url = comment.xpath('.//span[@class="comment-info"]/a/@href')[0].strip()  # 用户url
            user_address = self.user_info(user_url)
            if star and user_address:
                # 有的用户没有给出评分，有的用户地址违法获取
                items["name"] = movie_name
                items["movie_show"] = movie_show
                items["movie_time"] = movie_time
                items["user_address"] = user_address[0]
                items["votes"] = comment.xpath('.//span[@class="votes"]/text()')[0]
                items["author"] = comment.xpath('.//span[@class="comment-info"]/a/text()')[0]
                # 将评星的title属性用数值表示
                star = star[0]
                star_list = ["很差", "较差", "还行", "推荐", "力荐"]
                if star in star_list:
                    items["star"] = str(star_list.index(star) + 1)
                items["time"] = comment.xpath('.//span[@class="comment-time "]/text()')[0].strip()
                items["short"] = comment.xpath('.//span[@class="short"]/text()')[0].strip()
                print(items)
                time.sleep(sleep_time)

                self.save_info_to_csv(movie_name,items)
            else:
                continue



    def user_info(self,user_url):
        # 获取评论用户的地址
        html = self.get_html(user_url)
        user_address = html.xpath("//div[@class='user-info']/a/text()")
        if user_address:
            # 有的用户地址为空或者获取不到信息，则舍弃
            return user_address
        else:
            return None

    def save_info_to_csv(self,movie_name,items):
        # 将信息保存到csv文件中
        with open("./comments/"+movie_name+".csv",'a',newline="",encoding="utf-8") as f:
            write = csv.DictWriter(f,fieldnames=items.keys())
            write.writerow(items)


if __name__ == '__main__':
    spider = DoubanSpider()
    spider.get_url()