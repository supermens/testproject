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
    def __init__(self):
        pass

    def get_url(self):
        # 获取选电影中的电影地址
        start_url = "https://movie.douban.com/j/new_search_subjects?sort=U&range=0,10&tags=&start=20"
        response = requests.get(start_url)
        hjson = json.loads(response.content)
        for info in hjson["data"]:
            url = info["url"]
            movie_name = info["title"]
            print("正在保存%s电影评论..."%movie_name)
            saved_movie = []
            with open("finish.txt","r",encoding="utf-8") as f:
                infos = f.readlines()
                for info in infos:
                    saved_movie.append(info.strip())
            # print(saved_movie)
            if movie_name in saved_movie:
                print("%s已经获取完毕" % movie_name)
            else:
                self.start_spider(movie_name,url)
                time.sleep(sleep_time)

    def start_spider(self,movie_name,url):
        # 获取每一页评论的网页信息
        for page in range(0,1):
            comment_url = f"{url}comments?start={20*page}"
            print(comment_url)  # 评论页面的url
            time.sleep(sleep_time)
            html = self.get_html(comment_url)  # 获取评论页面信息
            print("正在保存%s电影信息的第%d页评论数据" % (movie_name,int(page + 1)))
            self.parse_html(movie_name,html)
            print("休息一会，防止被反爬")
            time.sleep(sleep_time)

    def get_html(self,url):
        # 获取指定的url界面，返回的etree解析后的html页面
        proxy = {
            # "http":"110.52.235.63:9999",
            # "https":"115.151.7.29:9999",
        }
        response = requests.get(url=url, headers=headers)
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
            star = comment.xpath('.//span[contains(@class,"rating")]/@title')  # 评分可能为空
            user_url = comment.xpath('.//span[@class="comment-info"]/a/@href')[0].strip()  # 用户url
            user_address = self.user_info(user_url)  # 用户的地址可能获取不到
            short = comment.xpath('.//span[@class="short"]/text()')  # 用户可能没有发表评论
            if star and user_address and short:
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
        # 当信息存储完毕后，将电影名保存到finish.txt文件中
        with open("finish.txt", "a", encoding="utf-8") as f:
            f.write(movie_name + "\n")

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