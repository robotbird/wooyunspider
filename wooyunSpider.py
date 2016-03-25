#!C:\Python27\python
# -*- coding: utf-8 -*-
import re,os
import urllib2
from bs4 import BeautifulSoup
import time
import MySQLdb
import socket

 
def getHtml(url):
    #print 'spider:'+url
    page_num=0;
    hds=[{'User-Agent':'Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US; rv:1.9.1.6) Gecko/20091201 Firefox/3.5.6'},\
         {'User-Agent':'Mozilla/5.0 (Windows NT 6.2) AppleWebKit/535.11 (KHTML, like Gecko) Chrome/17.0.963.12 Safari/535.11'},\
         {'User-Agent': 'Mozilla/5.0 (compatible; MSIE 10.0; Windows NT 6.2; Trident/6.0)'}]
    
    time.sleep(1)
  
    socket.setdefaulttimeout(2)
    try:
        request=urllib2.Request(url,None,headers=hds[page_num%len(hds)])
        response=urllib2.urlopen(request)
        text=response.read()
    except Exception as e:
        print u'抓取'+url+u'超时'
        conn=getMysqlConn()    
        cursor = conn.cursor()
        
        param=(url,'超时')
        cursor.execute('insert into wy_urls(url,status) values(%s,%s)',param)
        cursor.close()
        conn.close()
        print e
        return ""
            
    return text
 
def mkDir():
    date=time.strftime('%Y-%m-%d',time.localtime(time.time()))
    os.mkdir(str(date))
    
def removeChar(text):
    return text.replace('\r\n','').replace(' ','').replace('\t','')

def getMysqlConn():
    return MySQLdb.connect(host="localhost",user="root",passwd="root",db="wooyun",charset="utf8")

def dbexecute(sql,param):
    conn=getMysqlConn()    
    cursor = conn.cursor()
    cursor.execute(sql,param)
    cursor.close()
    conn.close()
 

def getCurrentTime():
    return time.strftime('%Y-%m-%d %H:%M:%S',time.localtime(time.time()))
     
def saveText(text,url):
    if text == "":
        return ""
    
    soup=BeautifulSoup(text)
    if soup.get_text()=='':
        print '抓取错误'
    else:
        
        try:
            fields=soup.select('.content > h3')
            id=re.findall('<a .*?>(W.*?)</a>',str(soup.select('h3 > a')))[0]
            #title = removeChar(soup.find('h3',class_='wybug_title').get_text()[5:])
            title = removeChar(fields[1].get_text())[5:]
            corps=removeChar(fields[2].get_text())[5:]
            author=removeChar(fields[3].get_text())[5:]
            bug_date=removeChar(fields[4].get_text())[5:]
            bug_open_date=removeChar(fields[5].get_text())[5:]
            bug_type=removeChar(fields[6].get_text())[5:]
            bug_level=removeChar(fields[7].get_text())[5:]
            bug_status=removeChar(fields[8].get_text())[5:]
            bug_tags=''
            
            div_description=soup.find('p',class_='detail wybug_description')
            bug_description =''
            if div_description is not None:
                bug_description=removeChar(div_description.get_text()[5:])
            bug_detail=soup.find('div',"wybug_detail")
            html = text
            addtime=getCurrentTime()
            #url=re.findall('"(/bugs/wooyun-.*?[0-9])"',str(soup.select('h3 > a')))[0]
            #print '解析：'+url
            
            conn=getMysqlConn()
            
            cursor = conn.cursor()
            query='select * from wy_bugs where id="%s"'%id
            cursor.execute(query)
            existid=cursor.fetchall()
            if not existid:
                sql = "insert into wy_bugs(id,title,corps,author,bug_date,bug_open_date,bug_type,bug_level,bug_status,bug_tags,bug_description,bug_detail,addtime,url,html) values(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)"     
                param = (id,title,corps,author,bug_date,bug_open_date,bug_type,bug_level,bug_status,bug_tags,bug_description,bug_detail,addtime,url,html)      
                n = cursor.execute(sql,param)      
                #print param
            else:
                print '已经抓取：'+id
            cursor.close()      
            conn.close()
        except Exception as e:
            param=(url,'解析错误')
            sql ='insert into wy_urls(url,status) values(%s,%s)'
            dbexecute(sql, param)
            print e
 
def getUrl(url):
    html=getHtml(url) 
     
#   print html
    soup=BeautifulSoup(html)
    urls_page=soup.find('div',"content")
    #print urls_page
    pages = soup.find('p','page')
 
   # urls=re.findall('"((http)://.*?)"',str(urls_page))
    urls = re.findall('"(/bugs/wooyun-.*?[0-9])"',str(urls_page))
    return urls 
 
def main():
    

    page="http://www.wooyun.org/bugs/new_public/page/"
    rooturl="http://www.wooyun.org"
    
    conn=getMysqlConn()    
    cursor = conn.cursor()
    
    errpage=""
    #获取所有超时或者抓取错误的页面
    cursor.execute("select * from wy_urls")
    for row in cursor.fetchall():
   
        errpage=row[1]
        #如果是内容页直接获取
        if 'page' not in errpage:
            if 'http' not in errpage:
                errpage = rooturl+errpage
            text=getHtml(errpage)
            saveText(text, errpage)
        else:
            #如果是列表页，遍历获取
            urls=getUrl(errpage)
            for url in urls:
                text=getHtml(rooturl+url)
                saveText(text, url)
        #获取成功后删除此页面
        print 'respider '+errpage
        cursor.execute("delete from wy_urls where id="+str(row[0]))
        print "delete from wy_urls where id="+str(row[0]) 
    
    
    cursor.execute("select * from wy_config")      
    for row in cursor.fetchall():      
        spidered_page=row[0]     
    
    for i in range(spidered_page+1,10):
       
        urls=getUrl(page+str(i))
        print '开始抓取第  '+str(i)+' 页'+getCurrentTime()
        for url in urls:
            print '抓取: '+url
            text=getHtml(rooturl+url)
            saveText(text,url)
        param=(str(i))
        cursor.execute('update wy_config set spidered_page=%s',param)
        print '抓取结束第   '+str(i)+' 页'+getCurrentTime()
            
    cursor.close()
    conn.close()
 
if __name__=="__main__":
    main()
