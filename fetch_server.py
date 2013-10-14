
#import wsgiref.handlers
import logging
import urllib
import time
from google.appengine.api import urlfetch
from google.appengine.runtime import apiproxy_errors

http_code_map = {

  "100":"Continue",
  "101":"Switching Protocols",
  "200":"OK",
  "201":"Created",
  "202":"Accepted",
  "203":"Non-Authoritative Information",
  "204":"No Content",
  "205":"Reset Content",
  "206":"Partial Content",
  "300":"Multiple Choices",
  "301":"Moved Permanently",
  "302":"Moved Temporarily",
  "303":"See Other",
  "304":"Not Modified",
  "305":"Use Proxy",
  "400":"Bad Request",
  "401":"Unauthorized",
  "402":"Payment Required",
  "403":"Forbidden",
  "404":"Not Found",
  "405":"Method Not Allowed",
  "406":"Not Acceptable",
  "407":"Proxy Authentication Required",
  "408":"Request Time-out",
  "409":"Conflict",
  "410":"Gone",
  "411":"Length Required",
  "412":"Precondition Failed",
  "413":"Request Entity Too Large",
  "414":"Request-URI Too Large",
  "415":"Unsupported Media Type",
  "500":"Server Error",
  "501":"Not Implemented",
  "502":"Bad Gateway",
  "503":"Service Unavailable",
  "504":"Gateway Time-out",
  "505":"HTTP Version not supported"                                                                                                                                                             
}


def application(environ, start_response):

	method = environ['REQUEST_METHOD']
	
	if method == 'GET':
		start_response('200 OK', [('Content-type','text/plain; charset=utf-8')])
		yield "fetch server is working ..."
	elif method == 'POST':

		wsgi_input = environ['wsgi.input']
		try:
			request_body_size = int(environ.get('CONTENT_LENGTH', 0))
		except (ValueError):
			request_body_size = 0
		request_body = wsgi_input.read(request_body_size)
		#request_body = wsgi_input.read()

		#request body include origin header and body separated by '\r\n\r\n'
		request_parts = request_body.split('\r\n\r\n',1)
		if('\r\n\r\n' in request_body):
			part_header = request_parts[0]
			form_data = request_parts[1]
		else:
			part_header = request_body
			form_data = None
		
		origin_request_method = environ['HTTP_ORIGIN_METHOD']
		fetch_url = environ['HTTP_FETCH_URL']
		

		logging.info("================= fetch server request  ==================== \n") 
		logging.info("fetch url: %s",fetch_url)
		logging.info("orgin request method: %s",origin_request_method)
		#logging.info("content-len: %d",request_body_size)
		logging.info(part_header)
		logging.info("================= fetch server request body==================== \n") 
		logging.info(form_data)

		#parse to head string to dict
		req_headers = dict(x.split(":",1) for x in part_header.splitlines() if x)

		for i in range(3):
			try: 
				response = urlfetch.fetch(fetch_url,form_data,origin_request_method,req_headers,allow_truncated=False, follow_redirects=False, deadline=60,validate_certificate=True)
				break

				
			except apiproxy_errors.OverQuotaError as e:
				logging.info(">>>>> catch Exception: OverQuotaError")
				time.sleep(1)
			except urlfetch.DeadlineExceededError as e:
				logging.info(">>>>> catch Exception: DeadlineExceededError")

			except urlfetch.DownloadError as e:
				logging.info(">>>>> catch Exception: DownloadError")
				time.sleep(1)
			except urlfetch.ResponseTooLargeError as e:
				logging.info(">>>>> catch Exception: ResponseTooLargeError")
				time.sleep(1)
			except urlfetch.SSLCertificateError as e:
				logging.info(">>>>> catch Exception: ResponseTooLargeError")
				time.sleep(1)
			except Exception as e:
				logging.info(">>>>> catch Exception")
				time.sleep(1)

		if(response):

			res_header = rewrite_response_header(response.headers)

			status_code = response.status_code
			logging.info("================= fetch server origin response  ==================== \n") 
			logging.info("HTTP STATUS:%d\n",status_code)
			logging.info(res_header)

			start_response("%d %s"%(status_code,http_code_map[str(status_code)]),res_header.items())
			yield response.content
		else:
			start_response("%d %s"%(status_code,http_code_map[str(100)]), [('Content-type','text/plain; charset=utf-8')])
			yield "over max retry times"


	else:
		start_response('204 No Content', [])

#delete some hop-by-hop header and rewrite some head
def rewrite_response_header(response_header):
	#now remove Hop-by-hop headers 
	#http://www.w3.org/Protocols/rfc2616/rfc2616-sec13.html  (13.5.1 End-to-end and Hop-by-hop Headers)
	if response_header.has_key("connection"):
		del response_header["connection"]

	if response_header.has_key("transfer-encoding"):
		del response_header["transfer-encoding"]

	new_header = {}
	for k,v in response_header.iteritems():
		#sometimes some   standard head will be removed in gae wsgi  ,to avoid 
		#filter out by gae wsgi we rewrite some head with prefix '_'
		if(k in ['content-encoding']):
			new_header["_" + k] = v
		else:
			new_header[k] = v
	return new_header;




# def main():
# 	wsgiref.handlers.CGIHandler().run(application)

# if __name__ == '__main__':
# 	main()
