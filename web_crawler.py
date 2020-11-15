#!/usr/local/bin/python3


import os,json
import signal
import subprocess
import time
from nyawc.Options import Options
from nyawc.Crawler import Crawler
from nyawc.CrawlerActions import CrawlerActions
from nyawc.http.Request import Request
import pathlib
from collections import defaultdict
import signal
import sys


if len(sys.argv)!=2:
	print("Usage : python web_crawler.py http(s)://website.com")
	exit()


options = Options()

###############################
#Local Server Configuration

port=8089
cmd="python -m SimpleHTTPServer "+str(port)+" 2>/dev/null"

#Crawling Configurations

host=sys.argv[1]
crawled_urls_to_check_dups=[]
#ignored_extensions=["css"]
ignored_extensions=["gif","jpg","png","css","jpeg","woff","ttf","eot","svg","woff2","ico"]
js_extensions=["js"]
static_extensions=["html","htm","xhtml","xhtm","shtml"]
scripts_extensions=["php","jsp","asp","aspx","py","pl","ashx","php1","php2","php3","php4"]



#Scope Configurations

options.scope.protocol_must_match = False
options.scope.subdomain_must_match = False
options.scope.hostname_must_match = True
options.scope.tld_must_match = True
options.scope.max_depth = None
options.scope.request_methods = [
    Request.METHOD_GET,
    Request.METHOD_POST,
    Request.METHOD_PUT,
    Request.METHOD_DELETE,
    Request.METHOD_OPTIONS,
    Request.METHOD_HEAD
]

## Headers Configurations

#options.identity.cookies.set(name='tasty_cookie', value='yum', domain='example.com', path='/cookies')

#options.identity.headers.update({"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.87 Safari/537.36"})


# For More: https://github.com/tijme/not-your-average-web-crawler/tree/master/docs/source

###############################

domain=host[host.find("://")+3:]

if "/" in domain: # when whole path is specified
	domain=domain[:domain.find("/")]

open("domain.js","w").write("domain='"+domain+"';"+"disallowed_ext=\""+str(ignored_extensions)+"\";"+"static_extensions=\""+str(static_extensions)+"\";"+"scripts_extensions=\""+str(scripts_extensions)+"\";")



path_js=defaultdict(list)
path_static=defaultdict(list)
path_scripts=defaultdict(list)
path_other=defaultdict(list)

path=""
query=""

p = subprocess.Popen(cmd, stdout=subprocess.PIPE,shell=True, preexec_fn=os.setsid)


print("\nServer started \n Check :  http://127.0.0.1:"+str(port)+"\n\nPress Ctrl+Z to exit\n\n")

print("--"*30)
print("\nJS Extension : "+str(js_extensions))
print("HTML Extension : "+str(static_extensions))
print("Server Scripts Extension : "+str(scripts_extensions))
print("Disallowed Extension : "+str(ignored_extensions))


print("--"*30)

def signal_handler(signal, frame):
  print("Press Ctrl+Z to exit")
  try:
    p.kill()  
    print("Server stopped.")
    exit()
  except:
    pass



def extension(str):
	if "?" in str:
		str=str[0:str.find("?")]
	str=pathlib.Path(str).suffix
	return str[1:len(str)]


def cb_crawler_before_start():
  try :
    signal.signal(signal.SIGINT, signal_handler)

  except:
    print("\nCheck if port is already open in case server is not started.")
		#exit(1)
	

  print("\nHost : "+domain)
  print("--"*30)

  print("\nCrawling started.")

def cb_crawler_after_finish(queue):
  print("Crawling finished.")
  print("Server will be still running in background.")

  #print("Crawled " + str(len(queue.get_all(QueueItem.STATUS_FINISHED))) + " URLs")
  #try:
   # p.kill()  
    #print("Server stopped.")
  #except:
   # pass

def cb_request_before_start(queue, queue_item):
  if queue_item.request.url in crawled_urls_to_check_dups: # To avoid duplicate links crawling
    return CrawlerActions.DO_SKIP_TO_NEXT
  if extension(queue_item.request.url) in ignored_extensions: # Don't crawl gif, jpg , etc
    return CrawlerActions.DO_SKIP_TO_NEXT
  return CrawlerActions.DO_CONTINUE_CRAWLING

def cb_request_after_finish(queue, queue_item, new_queue_items):
	global query,path
	crawled_urls_to_check_dups.append(queue_item.request.url) # Add newly obtained URL in list

	if extension(queue_item.request.url).lower() in js_extensions :
		if("?" in queue_item.request.url):
			path=queue_item.request.url[:queue_item.request.url.find("?")]
			query=queue_item.request.url[queue_item.request.url.find("?"):]
		else:
			path=queue_item.request.url
			query=""

		path_js[path].append(query)

		open(domain+"_JS_Links.json","w").write(str(json.dumps(path_js)))
		print(" JS > {}".format(queue_item.request.url))

	elif extension(queue_item.request.url).lower() in static_extensions:		
		if("?" in queue_item.request.url):
			path=queue_item.request.url[:queue_item.request.url.find("?")]
			query=queue_item.request.url[queue_item.request.url.find("?"):]
		else:
			path=queue_item.request.url

		path_static[path].append(query)

		open(domain+"_HTML_Links.json","w").write(str(json.dumps(path_static)))

		print(" HTML > {}".format(queue_item.request.url))

	elif extension(queue_item.request.url).lower() in scripts_extensions :

		if("?" in queue_item.request.url):
			path=queue_item.request.url[:queue_item.request.url.find("?")]
			query=queue_item.request.url[queue_item.request.url.find("?"):]
		else:
			path=queue_item.request.url

		path_scripts[path].append(query)

		open(domain+"_ServerScripts_Links.json","w").write(str(json.dumps(path_scripts))) # Json format was not valid 
		print(" ServerScripts > {}".format(queue_item.request.url))


	else:

		if("?" in queue_item.request.url):
			path=queue_item.request.url[:queue_item.request.url.find("?")]
			query=queue_item.request.url[queue_item.request.url.find("?"):]
		else:
			path=queue_item.request.url

		path_other[path].append(query)

		open(domain+"_Others_Links.json","w").write(str(json.dumps(path_other)))
		print(" Others> {}".format(queue_item.request.url))

	return CrawlerActions.DO_CONTINUE_CRAWLING

options.callbacks.crawler_before_start = cb_crawler_before_start # Called before the crawler starts crawling. Default is a null route.
options.callbacks.crawler_after_finish = cb_crawler_after_finish # Called after the crawler finished crawling. Default is a null route.
options.callbacks.request_before_start = cb_request_before_start # Called before the crawler starts a new request. Default is a null route.
options.callbacks.request_after_finish = cb_request_after_finish # Called after the crawler finishes a request. Default is a null route.

crawler = Crawler(options)
crawler.start_with(Request(host))
