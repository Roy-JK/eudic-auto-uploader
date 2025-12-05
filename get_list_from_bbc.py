import re
import requests
from bs4 import BeautifulSoup
from datetime import datetime
import importlib
import get_article_from_bbc


def fetch_bbc_6min_english_list(url):
    headers = {
        "User-Agent": "Mozilla/5.0"
    }
    resp = requests.get(url, headers=headers)
    resp.encoding = resp.apparent_encoding
    soup = BeautifulSoup(resp.text, "html.parser")
    articles = []
    seen_urls = set()
    for text_div in soup.find_all('div', class_='text'):
        # 标题和链接
        h2a = text_div.find('h2')
        title = ''
        href = ''
        if h2a and h2a.a:
            title = h2a.a.get_text(strip=True)
            href = h2a.a['href']
            if href.startswith('/'):
                href = 'https://www.bbc.co.uk' + href
        # 时间
        date = ''
        h3 = text_div.find('h3')
        if h3:
            m = re.search(r'\d{1,2} \w+ \d{4}', h3.get_text())
            if m:
                date = m.group(0)
        if href in seen_urls or not href:
            continue
        seen_urls.add(href)
        articles.append({'title': title, 'date': date, 'url': href})
    return articles

def parse_date(date_str):
    try:
        return datetime.strptime(date_str, '%d %b %Y')
    except Exception:
        return datetime.min

if __name__ == "__main__":
    list_url = "https://www.bbc.co.uk/learningenglish/english/features/real-easy-english"
    # list_url = "https://www.bbc.co.uk/learningenglish/english/features/6-minute-english_2025"
    articles = fetch_bbc_6min_english_list(list_url)
    # 按日期降序排序
    articles.sort(key=lambda x: parse_date(x['date']), reverse=True)
    lines = []
    print(f"共获取到 {len(articles)} 篇文章")
    for art in articles:
        lines.append(art['title'])
        lines.append(art['date'])
        lines.append(art['url'])
        get_article_from_bbc.fetch_article(art['url'])
        lines.append('')
    with open('bbc_6min_list.txt', 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))
    print("已保存为 list.txt")



