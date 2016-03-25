# -*- coding: utf-8 -*-
import re, os, json, sys, time, FunctionFile

flag = 1
reviewNumber = 1
postRating=""
postDate=""
reviewLink=""
splitValue=""
collection = FunctionFile.Mongo()

'''
Function object: Get required details from web page
Function Parameters: json_data and URL
'''
def getDetails(url, json_data):
    global flag, reviewNumber, postRating, postDate, reviewLink, splitValue, collection

    try:
        productPage = FunctionFile.getPage(url)
        if flag:
            for post in json_data['postMethod']:
                if re.match("split",post,re.I):
                    splitValue = json_data['postMethod'][post]
                if re.match("postRating",post,re.I):
                    postRating = json_data['postMethod'][post]
            post = {}        
            for field in json_data['productDetail']:
                selector = json_data['productDetail'][field]
                value = productPage.select(selector).__str__()

                if postRating and re.match("Rating",field,re.I):
                    value = FunctionFile.getRating(value, postRating)

                value = FunctionFile.removeTag(value)
                stringConv = json.dumps({field:value})
                post.update(json.loads(stringConv))
            collection.insert(post)
            print("Product Details inserted successfully into the database!!!")

            for selectorField in json_data['reviewDetail']['Selectors']:
                if re.match("ReviewLink",selectorField,re.I):
                    reviewLink = json_data['reviewDetail']['Selectors'][selectorField]
            flag=0

        for reviewInfo in productPage.select(json_data['reviewDetail']['Selectors']["Iterator"]):
            post = {}
            print("\nPlease wait.... Processing review link",reviewNumber)
            time.sleep(json_data['time'])
            if reviewLink:
                link = reviewInfo.select(reviewLink)[0]
                link = link.attrs['href']
                if not link.__contains__("http://"):
                    link = json_data['url'].replace(".*","")+link
                reviewPage = FunctionFile.getPage(link)
            else:
                reviewPage = reviewInfo

            for reviewFields in json_data['reviewDetail']['Fields']:
                selector = json_data['reviewDetail']['Fields'][reviewFields]
                
                if re.match(".*pros.*",reviewFields,re.I) or re.match(".*cons.*",reviewFields,re.I):
                    value = FunctionFile.getProsCons(json_data, reviewFields, reviewPage)
                else:
                    value = reviewPage.select(selector).__str__()
                    
                if splitValue and (re.match("Date",reviewFields,re.I) or re.match("AuthorName",reviewFields,re.I)):
                    value = FunctionFile.splitFunction(value, splitValue)

                if postRating and re.match("Rating",reviewFields,re.I):
                    value = FunctionFile.getRating(value, postRating)

                value = FunctionFile.removeTag(value)
                stringConv = json.dumps({reviewFields:value})
                post.update(json.loads(stringConv))
            collection.insert(post)
            print("Review Details inserted successfully into the database!!!")

            reviewNumber = reviewNumber + 1
            
        if FunctionFile.getNextPageLink(productPage):
            url = FunctionFile.getNextPageLink(productPage)
            if not url.__contains__("http://"):
                url = json_data['url'].replace(".*","")+url
            getDetails(url, json_data)
        else:
            exit

    except KeyError:
        print("Key not found:",sys.exc_info()[0])
        raise
    except ValueError:
        print("Value error occurred:",sys.exc_info()[0])
        raise

if __name__ == '__main__':
    counter = 1
    url = input("Enter URL: ")
    if FunctionFile.isValidUrl(url) and url.__contains__("reviews"):
        path = os.getcwd()
        for file in os.listdir(path):
            if file.endswith('.txt'):
                with open(file) as json_file:
                    json_data = json.load(json_file)
                    urlSelector = json_data['url']
                    if re.match(urlSelector,url,re.I):
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