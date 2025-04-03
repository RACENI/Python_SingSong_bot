import requests
from bs4 import BeautifulSoup as bs

def parseSong(arg):
    page = requests.get(f"https://www.youtube.com/results?search_query={arg}&sp=EgIQAQ%253D%253D")
    soup = bs(page.text, "html.parser")

    elements = soup.select('//*[@id="video-title"]')

    for index, element in enumerate(elements, 1):
            print("{} 번째 게시글의 제목: {}".format(index, element.text))


page = requests.get(f"https://www.youtube.com/results?search_query=개구릿대")
soup = bs(page.text, "html.parser")

elements = soup.findAll("a", {"id":"video-title"})

print(soup)
print(elements)
for i in elements:
    print(i)