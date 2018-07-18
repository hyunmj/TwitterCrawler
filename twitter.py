#-*- coding: utf-8 -*-
from bs4 import BeautifulSoup
import requests
from selenium import webdriver
from selenium.webdriver.firefox.firefox_binary import  FirefoxBinary
from selenium.webdriver.common.desired_capabilities import  DesiredCapabilities
import time
from selenium.webdriver.common.keys import Keys
import datetime as dt
import pickle
import pymongo
from pymongo import MongoClient


binary=FirefoxBinary('C:/Program Files/Mozilla Firefox/firefox.exe')
browser=webdriver.Firefox(executable_path='C:/Users/a/Desktop/geckodriver-v0.20.1-win64/geckodriver.exe',firefox_binary=binary)

# 검색할 영화 리스트 파일 열기
f=open('movies2.txt', 'r')

# 한 줄씩 읽기
while True:
    line=f.readline()

    if not line:
        break

    pair=line.split('\t')

    moviename=pair[0]

    # :과 -는 OR로 바꿈
    tmp=pair[0].replace(':', ' OR')
    tmp=tmp.replace(',', '')
    tmp=tmp.replace('-',' OR ')

    # 검색어
    keyword=tmp

    released_date=pair[1].replace('\n','').split('-')

    # 검색할 기간 설정, untildate는 커서 역할
    startdate=dt.date(year=int(released_date[0]),month=int(released_date[1]),day=int(released_date[2]))
    untildate=startdate+dt.timedelta(days=1)
    enddate=startdate+dt.timedelta(days=2)



    # startdate ~ untildate 의 트윗 크롤링 반복
    while not enddate==startdate:
        url='https://twitter.com/search?q='+keyword+'%20since%3A'+str(startdate)+'%20until%3A'+str(untildate)+'&amp;amp;amp;amp;amp;amp;lang=ko'
        browser.get(url)
        html = browser.page_source
        soup=BeautifulSoup(html,'html.parser')

        lastHeight = browser.execute_script("return document.body.scrollHeight")
        # 맨 밑까지 스크롤다운
        while True:
                browser.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(4)

                newHeight = browser.execute_script("return document.body.scrollHeight")

                # 맨 밑까지 내려왔으면
                if newHeight == lastHeight:
                    html = browser.page_source
                    soup=BeautifulSoup(html,'html.parser')
                    tweets=soup.find_all("p", {"class": "TweetTextSize"})
                    reply_html=soup.find_all("div", {"class": "ProfileTweet-action--reply"})
                    favorite_html=soup.find_all("div", {"class": "ProfileTweet-action--favorite"})
                    retweet_html=soup.find_all("div", {"class": "ProfileTweet-action--retweet"})
                    username=soup.select("span.username.u-textTruncate")

                    replies=[]
                    favorites=[]
                    retweets=[]
                    usernames=[]


                    for i in range(len(reply_html)):
                        replies.append(reply_html[i].find("span", {"class": "ProfileTweet-actionCountForPresentation"}))
                        favorites.append(favorite_html[i].find("span", {"class": "ProfileTweet-actionCountForPresentation"}))
                        retweets.append(retweet_html[i].find("span", {"class": "ProfileTweet-actionCountForPresentation"}))
                        usernames.append(username[i].find("b"))


                    # 딕셔너리 생성 후 리스트에 삽입
                    for i in range(len(tweets)):
                        dic={}
                        dic['tweet']=tweets[i].getText()
                        dic['reply']=replies[i].getText()
                        dic['favorite']=favorites[i].getText()
                        dic['retweet']=retweets[i].getText()
                        dic['username']=usernames[i].getText()

                        if dic['reply']=='':
                            dic['reply']=0
                        else:
                            dic['reply']=int(dic['reply'].replace(',', ''))

                        if dic['favorite']=='':
                            dic['favorite']=0
                        else:
                            dic['favorite']=int(dic['favorite'].replace(',', ''))

                        if dic['retweet']=='':
                            dic['retweet']=0
                        else:
                            dic['retweet']=int(dic['retweet'].replace(',', ''))

                        dic['date'] = dt.datetime.combine(startdate, dt.time(0,0,0))
                        dic['moviename']=moviename

                        conn = MongoClient('127.0.0.1')
                        db = conn.sns_db

                        collect = db.twitter

                        collect.insert(dic)

                    # 커서 이동
                    startdate=untildate
                    untildate=untildate+dt.timedelta(days=1)

                    break

                lastHeight = newHeight
