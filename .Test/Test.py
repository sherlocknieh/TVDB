from bs4 import BeautifulSoup

with open('.Test/Test.html', 'r', encoding='utf-8') as f:
    soup = BeautifulSoup(f.read(), 'lxml')

x = soup.stripped_strings
x = list(x)
print(x)

