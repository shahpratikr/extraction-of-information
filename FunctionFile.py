import pymongo, re, sys
from bs4 import BeautifulSoup
from urllib import request

'''
Function object: Connect to the MongoDB
Function Parameters: None
Returns: Collection name
'''
def Mongo():
    try:
        conn = pymongo.Connection('localhost', 27017)
        db = conn["ReviewDB"]
        reviewCollection = db["ReviewTable"]
        return reviewCollection
    except:
        print("Error in database connection")
        exit(0)

'''
Function object: Check whether URL is valid or not
Function Parameters: URL entered by user
Returns: True if URL is valid otherwise false
'''
def isValidUrl(url):
    regex = re.compile(
        r'^(?:http|ftp)s?://'
        r'(?:(?:[A-Z0-9](?:[A-Z0-9-]{0,61}[A-Z0-9])?\.)+(?:[A-Z]{2,6}\.?|[A-Z0-9-]{2,}\.?)|'
        r'localhost|'
        r'\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})'
        r'(?::\d+)?'
        r'(?:/?|[/?]\S+)$', re.IGNORECASE)

    if regex.match(url) is not None:
        return True;
    return False

'''
Function object: Remove HTML tags to get plain text
Function Parameters: HTML tags
Returns: Plain text
'''
def removeTag(text):
    removedTag = re.compile(r'<[^>]+>')
    text = text.__str__()
    removedText = removedTag.sub('', text)
    removedText = re.sub('[ ]+',' ',removedText)
    return removedText

'''
Function object: Get pros and cons if available
Function Parameters: json_data, field from json_file, HTML contents
Returns: Pros and/or cons
'''
def getProsCons(json_data, value, reviewPage):
    try:
        selector = json_data['reviewDetail']['Fields'][value]
        if re.match(".*pros.*",value,re.I):
            prosRE = json_data['reviewDetail']['Selectors']['ProsRE']
            RE = re.search(prosRE,reviewPage.__str__(),re.I)
            tags = RE.group(1)
            tags = BeautifulSoup(tags)
        elif re.match(".*cons.*",value,re.I):
            consRE = json_data['reviewDetail']['Selectors']['ConsRE']
            RE = re.search(consRE,reviewPage.__str__(),re.I)
            tags = RE.group(1)
            tags = BeautifulSoup(tags)
        text = tags.select(selector)[0]
        text = removeTag(text)
        return text.replace((value+":"),"")
    except:
        print("Error:",sys.exc_info()[0])

'''
Function object: Get next page's link
Function Parameters: HTML contents of URL entered by user
Returns: Next page's link if available otherwise 0
'''
def getNextPageLink(content):
    for link in content.find_all('a'):
        if re.match('Next.*',link.text):
            a = link.attrs['href']
            if a.__contains__("\'"):
                a = a.replace("\\'","")
            return a
            break
    return 0

'''
Function object: Get HTML contents of URL entered by user
Function Parameters: URL entered by user
Returns: HTML contents
'''
def getPage(url):
    try:
        byteHtml = request.urlopen(url).read().__str__()
        byteHtml = BeautifulSoup(byteHtml)
        return byteHtml
    except IOError:
        print("Error opening {}".format(url))
        exit()

'''
Function Object: Find rating value
Function parameter: Value found, postRating from JSON file
Returns: Rating value
'''
def getRating(value, postRating):
    value = BeautifulSoup(value)
    value = value.find(attrs={"itemprop":"ratingValue"})
    return value[postRating]

'''
Function Object: Split the value
Function parameters: Value found and splitValue from JSON file
Returns: First split value
'''
def splitFunction(value, splitValue):
    return value.split(splitValue)[0].replace("[","").replace("]","")