import pandas as pd
from bs4 import BeautifulSoup as bs
import csv
import requests


test_file = requests.get(
    'https://www.imdb.com/search/title/?genres=sci-fi&explore=title_type,genres&title_type=movie').text
titles = []
years = []
ratings = []
genres = []
runtimes = []
imdb_ratings = []
metascores = []
votes = []
reviews = []
review1 = []
title1 = []
rat =[]
s = bs(test_file, 'html.parser')
containers = s.find_all('div', class_="lister-item-content")
for container in containers:
    title = container.find('a').text
    titles.append(title)
    if container.find('span', class_="lister-item-year text-muted unbold") is not None:
        year = container.find('span', class_="lister-item-year text-muted unbold").text.replace('(', '').replace(')',
                                                                                                                 '')
        years.append(year)
    else:
        years.append(None)
    if container.find('span', class_='certificate') is not None:
        rating = container.find('span', class_='certificate').text
        ratings.append(rating)
    else:
        ratings.append(None)
    if container.find('span', class_='genre') is not None:
        genre = container.find('span', class_='genre').text
        genres.append(genre)
    else:
        genres.append(None)
    if container.find('span', class_='runtime') is not None:
        runtime = int(container.find('span', class_='runtime').text.split()[
                          0])  # hedhy en min ama habyt nhotha haka 3al visualisation baad
        runtimes.append(runtime)
    else:
        runtimes.append(None)
    if container.find('div', class_='inline-block ratings-imdb-rating') is not None:
        imdb = container.find('div', class_='inline-block ratings-imdb-rating').strong.text
        imdb_ratings.append(imdb)
    else:
        imdb_ratings.append(None)
    if container.find('div', class_='inline-block ratings-metascore') is not None:
        metascore = int(container.find('div', class_='inline-block ratings-metascore').span.text)
        metascores.append(metascore)
    else:
        metascores.append(None)
    if container.find('span', attrs={'name': 'nv'}) is not None:
        vote = int(container.find('span', attrs={'name': 'nv'}).text.replace(',', ''))
        votes.append(vote)
    else:
        votes.append(None)
    rev = container.h3.a['href']
    review = requests.get(f'http://www.imdb.com{rev}reviews').text
    T = bs(review, 'html.parser')
    l = T.find_all('div', class_='lister-item-content')
    #links = requests.get(f'http://www.imdb.com{l}').text
    #K = bs(links, 'html.parser')
    #kview = K.find_all('div', class_='lister-item-content')
    for k in l:
      title1.append(title)
      if k.find('span',class_='rating-other-user-rating') is not None:
         r = k.find('span',class_='rating-other-user-rating').text.replace('/10','').replace('\n','').replace(' ','')
         rat.append(r)
      else :
         rat.append(None)
      tit = k.find('a').text.replace('\n', '').replace(',',' ')
      titi = k.find('div', class_='text show-more__control').text
      c = tit + ':' + titi
      review1.append(c)
      #print(review1)

revvvv = pd.DataFrame({
    'title' : title1,
    'rating': rat,
    'review': review1
})
revvvv.to_csv('rev.csv')
films = pd.DataFrame({'movie': titles,
'year': years,
'rating': ratings,
'genre': genres,
'runtime_min': runtimes,
'imdb': imdb_ratings,
'metascore': metascores,
'votes': votes,
})
films.to_csv('Films.csv')

