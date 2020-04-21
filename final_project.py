'''
Jack Lyons
lyonjack
'''

from bs4 import BeautifulSoup
import requests
import json
import secrets
import sqlite3
import csv
import plotly.graph_objs as go

CACHE_FILE_NAME = 'cache_proj.json'
client_key = secrets.api_key
CACHE_DICT = {}


def create_movies_csv():
    '''
    prints the api call for the top 100 movies that will allow to be manipulated into a csv
    '''
    titles = []
    years = []

    url = 'https://www.imdb.com/list/ls068082370/'

    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    for movie in soup.find_all(class_ = 'lister-item-header'):
        title = movie.find('a').contents[0]
        titles.append(title)
        year = movie.find('span', class_ = 'lister-item-year text-muted unbold').text.strip()
        years.append(year)
        movies_data = dict(zip(titles, years))

    for k,v in movies_data.items():
        loc={'t':k }
        response = requests.get('http://www.omdbapi.com/?i=tt3896198&apikey=e1f94c56', params=loc).json()
        print(response)
        with open('data.csv', 'w', encoding='utf-8') as file_obj:
            json.dump(response, file_obj, ensure_ascii=False, indent=2)
    return response

def load_cache():
    ''' Opens the cache file if it exists and loads the JSON into
    the CACHE_DICT dictionary.
    if the cache file doesn't exist, creates a new cache dictionary

    Parameters
    ----------
    None

    Returns
    -------
    The opened cache: dict
    '''
    try:
        cache_file = open(CACHE_FILE_NAME, 'r')
        cache_file_contents = cache_file.read()
        cache = json.loads(cache_file_contents)
        cache_file.close()
    except:
        cache = {}
    return cache


def save_cache(cache):
    ''' Saves the current state of the cache to disk

    Parameters
    ----------
    cache_dict: dict
        The dictionary to save

    Returns
    -------
    None
    '''

    cache_file = open(CACHE_FILE_NAME, 'w')
    contents_to_write = json.dumps(cache)
    cache_file.write(contents_to_write)
    cache_file.close()


def make_url_request_using_cache(url, cache):
    '''Check the cache for a saved result for this url+cache
    combo. If the result is found, return it. Otherwise send a new
    request, save it, then return it.

    Parameters
    ----------
    baseurl: string
        The URL for the national sites endpoint
    params: dict
        A dictionary of param:value pairs

    Returns
    -------
    dict
        the results of the query as a dictionary loaded from cache
        JSON
    '''
    if (url in cache.keys()):
        print("Using cache")
        return cache[url]
    else:
        print("Fetching")
        response = requests.get(url)
        cache[url] = response.text
        save_cache(cache)
        return cache[url]

def create_movie_dict():
    ''' Makes a Dictionary the movie title and year"

    Parameters
    ----------
    None

    Returns
    -------
    dict
        key is a movie title and value is the year
        e.g. {'michigan':'https://www.nps.gov/state/mi/index.htm', ...}
    '''

    titles = []
    years =[]

    url = 'https://www.imdb.com/list/ls068082370/'
    response = make_url_request_using_cache(url, load_cache())
    soup = BeautifulSoup(response, 'html.parser')
    for movie in soup.find_all(class_ = 'lister-item-header'):
        title = movie.find('a').contents[0]
        titles.append(title)
        year = movie.find('span', class_ = 'lister-item-year text-muted unbold').text.strip()
        years.append(year)
        movies_data = dict(zip(titles, years))
    return(movies_data)


def create_csv(movies_data):
    '''Function creates a csv file from a dictionary.

        Parameters:
        -----------
        Dictionary

        Returns:
        --------
        CSV File
        '''
    with open('dict_2.csv', 'w', newline="") as csv_file:
        writer = csv.writer(csv_file)
        for key, value in movies_data.items():
            writer.writerow([key, value])


def create_db():
    conn = sqlite3.connect('movies_2.sqlite')
    cur = conn.cursor()

    drop_imdb_sql = 'DROP TABLE IF EXISTS "IMDb"'
    drop_movies_sql = 'DROP TABLE IF EXISTS "Movies"'

    create_imdb_sql = '''
        CREATE TABLE IF NOT EXISTS "IMDb" (
            "Id" INTEGER PRIMARY KEY AUTOINCREMENT,
            "Title" TEXT NOT NULL,
            "Year" TEXT NOT NULL,
            "Box Office" TEXT NOT NULL
        )
    '''
    create_movies_sql = '''
        CREATE TABLE IF NOT EXISTS 'Movies'(
            'Id' INTEGER PRIMARY KEY AUTOINCREMENT,
            'Title' TEXT NOT NULL,
            'IMDb' TEXT NOT NULL,
            'Metascore' TEXT NOT NULL,
            'Rotten Tomatoes' TEXT NOT NULL
            )
    '''
    cur.execute(drop_imdb_sql)
    cur.execute(drop_movies_sql)
    cur.execute(create_movies_sql)
    cur.execute(create_imdb_sql)
    conn.commit()
    conn.close()

create_db()

def load_movies():
    file_contents = open('data.csv', 'r')
    csv_reader = csv.reader(file_contents)
    next(csv_reader)


    insert_movie_sql = '''
        INSERT INTO Movies
        VALUES (NULL, ?, ?, ?, ?)
    '''

    conn = sqlite3.connect('movies_2.sqlite')
    cur = conn.cursor()
    for row in csv_reader:

        cur.execute(insert_movie_sql, [
            row[0],
            row[15],#IMDB
            row[16], #META
            row[18], #ROTTEN
        ])
    conn.commit()
    conn.close()

load_movies()

def load_imdb():
    file_contents = open('dict_2.csv', 'r')
    csv_reader = csv.reader(file_contents)
    next(csv_reader)


    insert_movie_sql = '''
        INSERT INTO IMDb
        VALUES (NULL, ?, ?, ?)
    '''

    conn = sqlite3.connect('movies_2.sqlite')
    cur = conn.cursor()
    for row in csv_reader:

        cur.execute(insert_movie_sql, [
            row[0],
            row[1],
            row[2],
        ])
    conn.commit()
    conn.close()

load_imdb()


def construct_unique_key(baseurl, params):
    ''' constructs a key that is guaranteed to uniquely and
    repeatably identify an API request by its baseurl and params

    Parameters
    ----------
    baseurl: string
        The URL for the API endpoint
    params: dict
        A dictionary of param:value pairs

    Returns
    -------
    string
        the unique key as a string
    '''

    param_strings = []
    connector = '_'
    for k in params.keys():
        param_strings.append(f'{k}_{params[k]}')
    param_strings.sort()
    unique_key = baseurl + connector +  connector.join(param_strings)
    return unique_key

def make_request_with_cache(baseurl, params):
    '''Check the cache for a saved result for this baseurl+params
    combo. If the result is found, return it. Otherwise send a new
    request, save it, then return it.

    Parameters
    ----------
    baseurl: string
        The URL for the API endpoint
    params: dict
        A dictionary of param:value pairs

    Returns
    -------
    dict
        the results of the query as a dictionary loaded from cache
        JSON
    '''

    request_key = construct_unique_key(baseurl, params)

    if request_key in CACHE_DICT.keys():
        print("using cache")
        return CACHE_DICT[request_key]
    else:
        print("fetching")
        response = requests.get(baseurl, params)
        CACHE_DICT[request_key] = response.json()
        save_cache(CACHE_DICT)
        return CACHE_DICT[request_key]

def info_from_OMDb_results(search_term):
    '''Obtain API data from OMDb API.

    Parameters
    ----------
    site_object: search_term
        a movie title

    Returns
    -------
        Formatted movie scores
    '''

    baseurl = 'http://www.omdbapi.com/?i=tt3896198&apikey=e1f94c56'
    params = {'t': search_term}
    response = make_request_with_cache(baseurl, params = params)

    search_results = response['Ratings']

    for items in search_results:
            if items['Value'] != '':
                value= items['Value'][0:][0:]
            else:
                value = 'no value'
            if items['Source'] != '':
                source = items['Source'][0:][0:]
            else:
                source = 'no source'
            print(f"- {source}: {value}")

def plot_year():
    '''
    Creates a bar graph of the most common years in the IMDb top 100 list

    Parameters
    ----------
    none

    Returns
    -------
        bar graph

    '''
    xvals = ['2001', '2003', '1994', '1995', '1999', '2000', '2008', '1980']
    yvals = [7, 5, 4, 4, 4, 4, 4, 3]

    bar_data = go.Bar(x=xvals, y=yvals)
    basic_layout = go.Layout(title="Most Common Years of Movies in the Top 100")
    fig = go.Figure(data=bar_data, layout=basic_layout)

    fig_ = fig.show()
    return fig_

def plot_top_ratings():
    '''
    Creates a bar graph of the top 5 movies and there ratings

    Parameters
    ----------
    none

    Returns
    -------
        bar graph

    '''
    ratings=['IMNDb', 'Rotten Tomatoes', 'Metacritic']

    fig = go.Figure(data=[
        go.Bar(name='The Shawshank Redemption', x=ratings, y=[93, 90, 80]),
        go.Bar(name='The Godfather', x=ratings, y=[92, 98, 100]),
        go.Bar(name='The Dark Knight', x =ratings, y=[90, 94, 84]),
        go.Bar(name='The Godfather: Part II', x =ratings, y=[90, 97, 90]),
        go.Bar(name='Pulp Fiction', x =ratings, y=[89, 92, 94]),
    ])

    fig.update_layout(barmode='group' )
    fig_ = fig.show()
    return fig_

def plot_bottom_ratings():
    '''
    Creates a bar graph of the bottom 5 movies and there ratings

    Parameters
    ----------
    none

    Returns
    -------
        bar graph

    '''
    ratings=['IMNDb', 'Rotten Tomatoes', 'Metacritic']

    fig = go.Figure(data=[
        go.Bar(name='Once Upon a Time in America', x=ratings, y=[84, 86, 0]),
        go.Bar(name='3 Idiots', x=ratings, y=[84, 100, 67]),
        go.Bar(name='Princess Mononoke', x =ratings, y=[84, 93, 76]),
        go.Bar(name='Vertigo', x =ratings, y=[83, 95, 100]),
        go.Bar(name='Citezen Kane', x =ratings, y=[83, 100, 100])
    ])

    fig.update_layout(barmode='group')
    fig_ = fig.show()
    return fig_

def plot_boxoffice():
    '''
    Creates a line graph of the the total box office of the top five movies

    Parameters
    ----------
    none

    Returns
    -------
        bar graph

    '''
    xvals = ['The Shawshank Redemption','The Godfather', 'The Dark Knight','The Godfather: Part II', 'Pulp Fiction' ]
    yvals = [2834000, 134940000, 534860000, 57300000, 107930000]

    scatter_data = go.Scatter(x=xvals, y=yvals)
    basic_layout = go.Layout(title="Total Box Office for the Top 5 Movies on IMDb")
    fig = go.Figure(data=scatter_data, layout=basic_layout)

    fig_ = fig.write_html("scatter.html", auto_open=True)
    return fig_

if __name__ == "__main__":

    count  = 0
    while count >= 0:
        count += 1
        search_term = input("Enter a movie title to get movie ratings, 'graph' for plots, or 'quit' to exit, \n")
        while search_term == 'graph':
            new_search = input("Enter 'year' for most common years , or 'ratings', or 'box'   \n")
            if new_search == 'box':
                plot_boxoffice()
                break
            if new_search == 'year':
                plot_year()
                break
            if new_search == 'ratings':
                second_search = input("Enter 'top' for the top 5 movies, or 'bottom' for the bottom 5 movies \n")
                if second_search == 'top':
                    plot_top_ratings()
                    break
                elif second_search == 'bottom':
                    plot_bottom_ratings()
                    break
        if search_term == "quit":
            exit()
        if search_term != 'quit':
            try:
                info_from_OMDb_results(search_term)
            except KeyError:
                print('invalid movie')
        else:
            print('[Error] Enter a proper Movie title')
