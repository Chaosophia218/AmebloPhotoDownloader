from urllib.request import urlopen
from urllib import request
from urllib import error
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor
import sys
import getopt
import re
import os

OP = "https://ameblo.jp/officialpress/entry-12147471110.html"
entlist = "entrylist-1.html"
pages = set()


'''
judge the version of ameblo page
url:.../entry-....html
return 1:new version
	   2:old version
'''
def versionJudge(url):
	html = urlopen(url)
	bsObj = BeautifulSoup(html, "html.parser")
	ver = bsObj.find("nav", {"class" : "skin-blogHeaderNavInner"})
	if ver:
		return 1
	else :
		return 2


'''
download images
path:save route
imgs:img links
'''
def imgDownload(path, imgs):
	openAgent()
	if not os.path.isdir(path):
		os.makedirs(path)
	for img in imgs:
		imgsrc = img["src"]
		if imgsrc.find("?caw=800") != -1:
			temp = imgsrc[:-8]
			imgsrc = temp
		paths = path + imgsrc.split('/')[-1]
#		print(imgsrc)
		i = len(imgs)
		try:
			request.urlretrieve(imgsrc, paths) 
		except error.URLError as err:
			print(err)
			print(imgsrc)
		except error.ContentTooShortError:
			request.urlretrieve(imgsrc, paths) 


'''
use agent to visit the site
'''
def openAgent():
	proxy = {'http':'1.195.250.190:61234'}
	proxySupport = request.ProxyHandler(proxy)
	opener = request.build_opener(proxySupport)
	opener.addheaders =  [('User-Agent','Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.87 Safari/537.36')]
	request.install_opener(opener)


'''
get blog nickname
fullUrl:.../entrylist-1.html
version:1/2
path:savepath
'''
def getName(fullUrl, version, path):
	html = urlopen(fullUrl)
	bsObj = BeautifulSoup(html, "html.parser")
	if version == 1:
		name = bsObj.find("p", {"class" : "skin-profileName"}).text
#		print(name)
	else :
		name = bsObj.find("li", {"class" : "nickname"}).find("a").text
#		print(name)
	path = path + name.replace('\n', '') + "\\"
	return path


'''
download all the images(used in thread pool)
'''
def getImgs(path, singlePage, pagesLen, count, version):
	print("downloading no.%d in total %d pages"%(count, pagesLen), end = "\r")
	html = urlopen(singlePage)
	bsObj = BeautifulSoup(html, "html.parser")
	if version == 1:
		imgs = bsObj.find("div", {"class":"skin-entryBody"}).findAll("img")
	else :
		imgs = bsObj.find("div", {"class":"subContentsInner"}).findAll("img")
	imgDownload(path, imgs)


'''
get all the "/entry-....html" from "/entrylist-*.html" add into pages
pageUrl:.../entrylist-*.html
'''
def getLinks(pageUrl):
	global pages
	html = urlopen(pageUrl)
	bsObj = BeautifulSoup(html, "html.parser")
	for link in bsObj.findAll("a", href = re.compile("(https)(.*)(/entry\-\d{11}\.html)(?!#)")):
		if 'href' in link.attrs:
			if link.attrs['href'] not in pages:
				newPage = link.attrs['href']
				if newPage != OP:
#					print(newPage)
					pages.add(newPage)


'''
get the num of entrylist pages
entryList:.../entrylist-1.html
version:1/2
return:page(int)
'''
def getLists(entryList, version):
	html = urlopen(entryList)
	bsObj = BeautifulSoup(html, "html.parser")
	if version == 1:
		lastPage = bsObj.find("a", {"class":"skin-paginationEnd skin-btnIndex js-paginationEnd"})
#		print(str(lastPage))
	else :
		lastPage = bsObj.find("a", {"class":"lastPage"})
#		print(str(lastPage))
	pageNum = re.sub("\D", "", str(lastPage))
	print(pageNum)
	page = int(pageNum)
	return page


def main():
	path = ""
	amebloUrl = ""

	try:
		opts, args = getopt.getopt(sys.argv[1:], "ha:p:", ["help", "amebloUrl=", "path="])
	except getopt.GetoptError:
		print("Usage: ameblo.py -a https://ameblo.jp/.../ -p C:\\...\\")
		sys.exit(2)
	for opt, arg in opts:
		if opt == "-h":
			print("Usage: ameblo.py -a https://ameblo.jp/.../ -p C:\\...\\")
			sys.exit(2)
		elif opt in ("-a", "--amebloUrl"):
			amebloUrl = arg
		elif opt in ("-p", "--path"):
			path = arg		

	fullUrl = amebloUrl + entlist
	print(fullUrl)
	version = versionJudge(fullUrl)
	path = getName(fullUrl, version, path)
	print(path)

	page = getLists(fullUrl, version)
	i = 1
	while (i <= page):
		entryUrl = amebloUrl + "entrylist-" + str(i) + ".html"
		getLinks(entryUrl)
		i += 1
	print(len(pages))

	p = ThreadPoolExecutor()
	count = 1
	for singlePage in pages:
		p.submit(getImgs, path, singlePage, len(pages), count, version)
#		getImgs(path, singlePage, len(pages), count, version)
		count += 1
	p.shutdown()
	print("completed")

if __name__ == "__main__":
	main()