import re
from performance import timetest

rx_greed = re.compile('<img\b.*?src="([^"]*)"[^>]*>')
rx_non_greed = re.compile('<img\b.*?src="(.*?)".*?>')
rx_zero = re.compile('<img\b(?:(?!src=).)*src="([^"]*)"[^>]*>')
html = '<img class="test.main" src="/img/logo.gif" title="html_title_test" />'


@timetest(1)
def test_greed():
    for _ in xrange(10**6):
        rx_greed.search(html)

@timetest(1)
def test_non_greed():
    for _ in xrange(10**6):
        rx_non_greed.search(html)

@timetest(1)
def test_zero():
    for _ in xrange(10**6):
        rx_zero.search(html)


test_greed()
test_non_greed()
test_zero()
