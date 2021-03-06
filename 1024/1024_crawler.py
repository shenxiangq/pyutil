#! /usr/bin/env python

from concurrent.futures import ThreadPoolExecutor
import urllib2, lxml.html, re, os, uuid, sys
from datetime import datetime
from util import retry, to_unicode


MAX_SIZE = 5*1024*1024 # 5MB

main_domain = 'http://cl.recl.pw/'
catalog = [
    'thread0806.php?fid=16',
    'thread0806.php?fid=16&page=2',
    ]

html_template = u'''
    <html>
    <head>
    <meta http-equiv="Content-Type" content="text/html; charset=gbk">
    <title>%s</title>
    <style type="text/css">
		img {
			max-height: 600px;
		}
	</style>
    </head>
    <body>
        <div align="center">
        <a target="_blank" href="%s">show source link</a>
        %s
        </div>
    </body>
    </html>
'''

class CLSpider(object):

    def __init__(self, max_workers=5):
        self.executor = ThreadPoolExecutor(max_workers)
        self.parser = lxml.html.HTMLParser(encoding='gbk')
        self.exists_list = []
        try:
            with open('exists.txt') as fin:
                for line in fin:
                    line = line.strip()
                    self.exists_list.append(line)
        except IOError:
            pass
        self.exists = set(self.exists_list)

    @retry(max_tries=3)
    def download(self, url, max_size=MAX_SIZE):
        print url
        req = urllib2.Request(url)
        req.add_header('User-Agent', 'Mozilla/5.0 (Windows NT 6.3; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/45.0.2454.93 Safari/537.36')
        rsp = urllib2.urlopen(req, timeout=30)
        length = rsp.headers.get('content-length')
        if length and int(length) > max_size:
            return None
        return rsp.read()

    def check_hub(self, hub_url):
        body = self.download(hub_url)
        #tree = lxml.html.document_fromstring(body)
        tree = lxml.html.document_fromstring(body, parser=self.parser)
        tree.make_links_absolute(base_url=main_domain)
        als = tree.xpath('//table[@id="ajaxtable"]/tbody/tr')
        futures = []
        for e in als:
            a = e.xpath('./td[2]/h3/a')
            number = e.xpath('./td[4]')
            if not a or not number:
                continue

            a = a[0]
            number = number[0]
            title = '-%s %s' % (number.text_content(), a.text_content())
            url = a.get('href')
            page_id = re.search('/(\d+)\.html', url)
            if page_id:
                page_id = page_id.group(1)
            if page_id in self.exists or page_id is None:
                continue
            futures.append((self.executor.submit(self.detail_page, url, title, page_id), page_id))
            #self.detail_page(url, title, page_id)

        for f, page_id in futures:
            e = f.exception()
            print e
            self.exists_list.insert(0, page_id)
            with open('exists.txt', 'w') as fout:
                fout.write('\n'.join(self.exists_list))

        #self.executor.shutdown(wait=True)

    def start(self):
        for curl in catalog:
            hub_url = main_domain + curl
            date = datetime.now().strftime('%Y-%m-%d')
            self.date_dir = os.path.join('data', date)
            if not os.path.exists(self.date_dir):
                os.mkdir(self.date_dir)
                os.mkdir(os.path.join(self.date_dir, 'imgs'))
            self.check_hub(hub_url)


    def detail_page(self, url, title, page_id):
        #import pdb;pdb.set_trace()
        body = self.download(url)
        tree = lxml.html.document_fromstring(body, parser=self.parser)
        article = tree.xpath('//div[@class="tpc_content do_not_catch"]')
        if not article:
            return
        article = article[0]
        inputs = article.xpath('.//input')
        for input in inputs:
            src = input.get('src')
            if not src:
                continue
            img = tree.makeelement('img', dict(src=src))
            input.addnext(img)
            input.drop_tree()

        imgs = article.xpath('.//img')
        for img in imgs:
            src = img.get('src')
            format = re.search('(\.\w{2,5})$', src) or ''
            if format:
                format = format.group(1)
            image_id = page_id + '-' + str(uuid.uuid1()) + format
            data = self.download(src)
            image_path = os.path.join(self.date_dir, 'imgs', image_id)
            if data:
                with open(image_path, 'wb') as fout:
                    fout.write(data)
            img.set('src', 'imgs' + '/' + image_id)
            #img.set('height', '600')

        html_body = html_template % (title, url, lxml.html.tostring(article))
        filename = page_id + ' ' + title + '.html'
        with open(os.path.join(self.date_dir, filename.encode('gbk')), 'w') as fout:
            fout.write(html_body.encode('gbk', 'ignore'))

    def one_page(self, url):
        #url = 'http://cl.recl.pw/htm_data/7/1601/1813658.html'
        self.date_dir = os.path.join('data', 'temp')
        page_id = re.search('/(\d+)\.html', url) or ''
        if page_id:
            page_id = page_id.group(1)
        self.detail_page(url, page_id, page_id)

if __name__ == '__main__':
    spider = CLSpider()
    if len(sys.argv) <= 1:
        spider.start()
    else:
        spider.one_page(sys.argv[1])
