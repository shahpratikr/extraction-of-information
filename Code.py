# -*- coding: utf-8 -*-
import BeautifulSoup
from urllib import urlopen
import re
import os
import json
import sys
import time
import pymongo

regex = re.compile(r'(?:http|ftp)s?://'
                   r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'
                   r'localhost|'
                   r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'
                   r'(?::\d+)?'
                   r'(?:/?|[/?]\S+)$', re.IGNORECASE)
flag = 1
reviewNumber = 1
postRating = ""
postDate = ""
reviewLink = ""
splitValue = ""


def isValidUrl(url):
    if regex.match(url) is not None:
        return True
    return False


def Mongo():
    try:
        conn = pymongo.Connection('localhost', 27017)
        db = conn["ReviewDB"]
        reviewCollection = db["ReviewTable"]
        return reviewCollection
    except:
        print("Error in database connection")
        exit(0)


def removeTag(text):
    removedTag = re.compile(r'<[^>]+>')
    text = text.__str__()
    removedText = removedTag.sub('', text)
    removedText = re.sub('[ ]+', ' ', removedText)
    return removedText


def getProsCons(json_data, value, reviewPage):
    try:
        selector = json_data['reviewDetail']['Fields'][value]
        if re.match(".*pros.*", value, re.I):
            prosRE = json_data['reviewDetail']['Selectors']['ProsRE']
            RE = re.search(prosRE, reviewPage.__str__(), re.I)
            tags = RE.group(1)
            tags = BeautifulSoup(tags)
        elif re.match(".*cons.*", value, re.I):
            consRE = json_data['reviewDetail']['Selectors']['ConsRE']
            RE = re.search(consRE, reviewPage.__str__(), re.I)
            tags = RE.group(1)
            tags = BeautifulSoup(tags)
        text = tags.select(selector)[0]
        text = removeTag(text)
        return text.replace((value+":"), "")
    except:
        print("Error:", sys.exc_info()[0])


def getNextPageLink(content):
    for link in content.find_all('a'):
        if re.match('Next.*', link.text):
            a = link.attrs['href']
            if a.__contains__("\'"):
                a = a.replace("\\'", "")
            return a
            break
    return 0


def getPage(url):
    try:
        byteHtml = urlopen(url).read().__str__()
        byteHtml = BeautifulSoup(byteHtml)
        return byteHtml
    except IOError:
        print("Error opening {}".format(url))
        exit()


def getRating(value, postRating):
    value = value.__str__()
    value = BeautifulSoup(value)
    value = value.find(attrs={"itemprop": "ratingValue"})
    return value[postRating]


def splitFunction(value, splitValue):
    return value.split(splitValue)[0].replace("[", "")


def getDetails(url, json_data):
    global flag, reviewNumber, postRating, postDate, reviewLink, splitValue

    try:
        productPage = getPage(url)
        if flag:
            for post in json_data['postMethod']:
                if re.match("split", post, re.I):
                    splitValue = json_data['postMethod'][post]
                if re.match("postRating", post, re.I):
                    postRating = json_data['postMethod'][post]

            for field in json_data['productDetail']:
                selector = json_data['productDetail'][field]
                value = productPage.select(selector)

                #to do in future
                if postRating and re.match("Rating", field, re.I):
                    value = getRating(value, postRating)

                print("Product", field, ":", removeTag(value))

            for selectorField in json_data['reviewDetail']['Selectors']:
                if re.match("ReviewLink", selectorField, re.I):
                    reviewLink = json_data['reviewDetail']['Selectors'][selectorField]
            flag = 0

        for reviewInfo in productPage.select(json_data['reviewDetail']['Selectors']["Iterator"]):
            print("\nPlease wait.... Processing review link", reviewNumber)
            time.sleep(json_data['time'])
            if reviewLink:
                link = reviewInfo.select(reviewLink)[0]
                link = link.attrs['href']
                if not link.__contains__("http://"):
                    link = json_data['url'].replace(".*", "")+link
                reviewPage = getPage(link)
            else:
                reviewPage = reviewInfo

            for reviewFields in json_data['reviewDetail']['Fields']:
                selector = json_data['reviewDetail']['Fields'][reviewFields]

                #to do in future
                if re.match(".*pros.*", reviewFields, re.I) or re.match(".*cons.*", reviewFields, re.I):
                    value = getProsCons(json_data, reviewFields, reviewPage)
                else:
                    value = reviewPage.select(selector).__str__()

                #to do in future
                if splitValue and (re.match("Date", reviewFields, re.I) or re.match("AuthorName", reviewFields, re.I)):
                    value = splitFunction(value, splitValue)

                #to do in future
                if postRating and re.match("Rating", reviewFields, re.I):
                    value = getRating(value, postRating)

                print("Review", reviewFields, ":", removeTag(value))
            reviewNumber = reviewNumber + 1

        if getNextPageLink(productPage):
            url = getNextPageLink(productPage)
            if not url.__contains__("http://"):
                url = json_data['url'].replace(".*", "")+url
            getDetails(url, json_data)
        else:
            exit

    except KeyError:
        print("Key not found:", sys.exc_info()[0])
        raise
    except ValueError:
        print("Value error occurred:", sys.exc_info()[0])
        raise

if __name__ == '__main__':
    counter = 1
    url = input("Enter URL: ")
    if isValidUrl(url) and url.__contains__("reviews"):
        path = os.getcwd()
        for file in os.listdir(path):
            if file.endswith('.txt'):
                with open(file) as json_file:
                    json_data = json.load(json_file)
                    urlSelector = json_data['url']
                    if re.match(urlSelector, url, re.I):
                        counter = 0
                        getDetails(url, json_data)
        if counter:
            print("No configuration file is matched for {}".format(url))
            exit()
    else:
        print("Something went wrong. Please check following things in URL and try again.")
        print("1. URL doesn't contain any reviews in it. Please provide URL which has reviews in it.")
        print("2. Entered URL is in invalid form")
        exit()
