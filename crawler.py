import urlparse
import urllib2
import re
import regex
import time
from bs4 import BeautifulSoup


class Crawler(object):
    def __init__(self, max_depth_page=10, max_depth_search=3):
        self.visited = set([])
        self.to_crawl = set([])
        self.graph = {}
        self.max_depth_page = max_depth_page
        self.max_depth_search = max_depth_search
        self.files_re = re.compile(r"\.jpg|\.jpeg|\.png|\.tif|\.tiff|\.gif\
            |\.jpe|\.bmp|\.dib|\.swf|\.pdf|sl=EN|sl=DE|/en/|/de/|/al/|.mp3|\
            .wmv|.JPG|.JPEG|admin|.doc|.docx|.xls|.xlt|.xlm|.ppt|.pptx")

    def __str__(self):
        return "Crawled: " + str(len(self.visited) + " Max_depth_page: " /
                                 +str(self.max_depth_page) + " Max_depth_search: " /
                                 + str(self.max_depth_search))

    def add_to_crawl_urls(self, urls):
        if type(urls) == list:
            self.to_crawl += urls

    def cyrillic_words(self, content, words_dict, encoding):
        try:
            words = regex.findall(u"\p{Cyrillic}+", content.decode(encoding))

            for word in words:
                word = word.lower()
                words_dict[word] = words_dict.get(word, 0) + 1
            return True
        except:
            return False

    def get_content(self, url):
        try:
            if not self.files_re.search(url):
                return urllib2.urlopen(url, None, 3.0).read()
            return None
        except:
            return None

    def is_valid(self, domain):
        return 'http' in domain

    def get_domain(self, url):
        try:
            parsed_uri = urlparse.urlparse(url)
            domain = parsed_uri.netloc
            scheme = parsed_uri.scheme
            return scheme, domain
        except Exception:
            return None

    def is_mak_site(self, link):
        return '.mk' in link or 'macedonia' in link

    def print_dict(self, words_dict, url):
        try:
            if words_dict:
                s, d = self.get_domain(url)
                f = open(d, 'w')
                for key in words_dict.keys():
                    f.write(key.encode('utf-8') + ' ' + str(words_dict[key]) + '\n')
                f.close()
            else:
                self.write_content_to_file('errors', url, 'a')
            return True
        except:
            return False

    def get_encoding(self, soup):
        try:
            encod = soup.meta.get('charset')
            if encod == None:
                encod = soup.meta.get('content-type')
                if encod == None:
                    content = soup.meta.get('content')
                    match = re.search('charset=(.*)', content)
                    if match:
                        encod = match.group(1)
                    else:
                        return None
            return encod
        except:
            return None

    def get_all_links(self, url, max_inside_links=30):  # gi pominuva site linkovi od edna strana do max_depth
        inside_links_visited = set([])
        inside_links_tocrawl = [url]
        next_depth = []
        outside_links = set([])
        depth = 0
        inside_links_counter = 0
        words = {}
        while inside_links_tocrawl and depth <= self.max_depth_page:
            page = inside_links_tocrawl.pop()
            content = self.get_content(page)  # prajme request do url i ja zemame html sodrzinata
            print "Stranata sto ja krola", page

            if content != None:

                scheme_page, domain_page = self.get_domain(page)

                soup = BeautifulSoup(content)  # vo soup objekt ja predavame html sodrzinata
                encoding = self.get_encoding(soup)
                if encoding == None:
                    encoding = 'utf-8'

                self.cyrillic_words(content, words, encoding)

                for tag in soup.findAll('a', href=True):
                    link = urlparse.urljoin(page, tag['href'])  # urlparse  se spravuva so relativni i apsolutni adresi

                    if not self.is_valid(link) or not self.is_mak_site(link):
                        continue

                    scheme_link, domain_link = self.get_domain(link)
                    scheme_domain_link = scheme_link + '://' + domain_link

                    if domain_link == domain_page and depth < self.max_depth_page:
                        if max_inside_links > inside_links_counter and link not in inside_links_visited and link not in next_depth \
                                    and link not in inside_links_tocrawl and link != page:
                            # inside_links_visited.(link)
                            next_depth.append(link)
                            inside_links_counter += 1
                            print "V Add:", link
                    elif scheme_domain_link not in outside_links:
                        outside_links.add(scheme_domain_link)
                        print "N Add:", scheme_domain_link
                print "Ja iskrolav stranata"
                inside_links_visited.add(page)

            if not inside_links_tocrawl:
                print "Nema pojce linkoj za krolanje"
                inside_links_tocrawl, next_depth = next_depth, []  # swap
                depth += 1
                print len(inside_links_tocrawl)
        if self.print_dict(words, url):
            print 'Uspesno ispecaten recnik vo fajl!'
        else:
            print 'GRESKA DICT!'
        return outside_links

    def crawl_web(self, seed):
        self.to_crawl.add(seed)
        next_depth = set([])
        depth = 0
        write_content_counter = 100
        while self.to_crawl and depth <= self.max_depth_search:
            page = self.to_crawl.pop()
            print "ZEMI:", page
            write_content_counter -= 1
            all_links = self.get_all_links(page)

            for link in all_links:
                if link not in self.visited and link not in self.to_crawl:
                    next_depth.add(link)

            self.visited.add(page)
            self.graph[page] = all_links
            if not self.to_crawl:
                self.to_crawl, next_depth = next_depth, set([])
                depth += 1

            if write_content_counter == 0:
                self.write_content_to_file('1.tocrawl',   self.to_crawl,    'w')
                self.write_content_to_file('2.nextdepth', next_depth,       'w')
                self.write_content_to_file('3.graph',     self.graph,       'w')
                self.write_content_to_file('4.visited',   self.visited,     'w')
                write_content_counter = 100

        return self.visited

    def print_graph(self):
        padding = '   '
        for key in self.graph.keys():
            print key
            for l in self.graph[key]:
                print padding, l

    def write_content_to_file(self, file_name, content, opt):
        try:
            f = open(file_name, opt)
            f.write(content + '\n')
            f.close()
            return True
        except:
            return False


def main():
    main_link = 'http://www.macedonia.eu.org/'
    c = Crawler(max_depth_search=2, max_depth_page=1)
    start = time.time()
    c.crawl_web(main_link)
    end = time.time()
    print 'Crawled web for', round(end - start, 2), 'sec.'

if __name__=='__main__':
    main()
