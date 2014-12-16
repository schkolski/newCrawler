import urlparse
import urllib
import re
import time
from bs4 import BeautifulSoup


class Crawler(object):
    def __init__(self, max_depth_page=10, max_depth_search=3):
        self.visited = set([])
        self.to_crawl = set([])
        self.graph = {}
        self.max_depth_page = max_depth_page
        self.max_depth_search = max_depth_search
        self.files_re = re.compile(r"\.jpg|\.jpeg|\.png|\.tif|\.tiff|\.gif|\.jpe|\.bmp|\.dib|\.swf|\.pdf|sl=EN|sl=DE|/en/|/de/")

    def __str__(self):
        return "Crawled: " + str(len(self.visited) + " Max_depth_page: " /
                                 +str(self.max_depth_page) + " Max_depth_search: " /
                                 + str(self.max_depth_search))

    def add_to_crawl_urls(self, urls):
        if type(urls) == list:
            self.to_crawl += urls

    def get_content(self, url):
        try:
            if not self.files_re.search(url):
                return urllib.urlopen(url).read()
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

    def get_all_links(self, url):  # gi pominuva site linkovi od edna strana do max_depth
        inside_links_visited = set([])
        inside_links_tocrawl = [url]
        next_depth = []
        outside_links = set([])
        depth = 0
        while inside_links_tocrawl and depth <= self.max_depth_page:
            page = inside_links_tocrawl.pop()
            content = self.get_content(page)  # prajme request do url i ja zemame html sodrzinata
            print "Stranata sto ja krola", page

            if content != None:

                scheme_page, domain_page = self.get_domain(page)
                self.write_content_to_file(domain_page, content)


                soup = BeautifulSoup(content)  # vo soup objekt ja predavame html sodrzinata

                for tag in soup.findAll('a', href=True):
                    link = urlparse.urljoin(page, tag['href'])  # urlparse  se spravuva so relativni i apsolutni adresi

                    if not self.is_valid(link) or not self.is_mak_site(link):
                        continue

                    scheme_link, domain_link = self.get_domain(link)
                    scheme_domain_link = scheme_link + '://' + domain_link

                    if domain_link == domain_page and depth < self.max_depth_page:
                        if link not in inside_links_visited and link not in next_depth \
                                    and link not in inside_links_tocrawl and link != page:
                            # inside_links_visited.(link)
                            next_depth.append(link)
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

        return outside_links

    def crawl_web(self, seed):
        self.to_crawl.add(seed)
        next_depth = set([])
        depth = 0
        while self.to_crawl and depth <= self.max_depth_search:
            page = self.to_crawl.pop()
            print "ZEMI:", page
            all_links = self.get_all_links(page)

            for link in all_links:
                if link not in self.visited and link not in self.to_crawl:
                    next_depth.add(link)

            self.visited.add(page)
            self.graph[page] = all_links
            if not self.to_crawl:
                self.to_crawl, next_depth = next_depth, set([])
                depth += 1

        self.write_content_to_file('1.tocrawl',   self.to_crawl)
        self.write_content_to_file('2.nextdepth', next_depth)
        self.write_content_to_file('3.graph',     self.graph)
        self.write_content_to_file('4.visited',   self.visited)
        return self.visited

    def print_graph(self):
        padding = '   '
        for key in self.graph.keys():
            print key
            for l in self.graph[key]:
                print padding, l

    def write_content_to_file(self, file_name, content):
        try:
            f = open(file_name, 'a')
            f.write(content + '\n')
            f.close()
            return True
        except:
            return False


if __name__=='__main__':
    main_link = 'http://www.macedonia.eu.org/'
    c = Crawler(max_depth_search=2, max_depth_page=1)
    start = time.time()
    c.crawl_web(main_link)
    end = time.time()
    print 'Crawled web for', round(end - start, 2), 'sec.'
# print c.visited
