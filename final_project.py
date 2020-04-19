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

class Movie:
    '''a Movie

    Instance Attributes
    -------------------
    title: string
        the the title of the Movie (e.g. 'Rambo')

    year: string
        year the Movie was released

    rating_value: string
        the IMDb rating of the Movie

    count: string
        the total votes on IMDb

    summary: string
        the summary of the Movie's plot
    '''

    def __init__(self, title = 'no title', year = 'no year', rating_value = 'no rating' , metascore = 'no metascore', genre = 'no genre' ):
                self.title = title
                self.year =  year
                self.rating_value = rating_value
                self.metascore = metascore
                self.genre = genre


    def info(self):
        '''Function retrieves information on self. Formats the information into a readable str.

        Parameters:
        -----------
        None

        Returns:
        --------
        str: formatted string
        '''
        return  self.title + ' (' + self.year + ')' + ': ' + self.rating_value + self.genre

def create_movie_dict():
    titles = []
    years =[]

    url = 'https://www.imdb.com/list/ls068082370/'
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    for movie in soup.find_all(class_ = 'lister-item-header'):
        title = movie.find('a').contents[0]
        titles.append(title)
        year = movie.find('span', class_ = 'lister-item-year text-muted unbold').text.strip()
        years.append(year)
        movies_data = dict(zip(titles, years))
    return(movies_data)

x = create_movie_dict()

def create_csv(movies_data):
    with open('dict.csv', 'w', newline="") as csv_file:
        writer = csv.writer(csv_file)
        for key, value in movies_data.items():
            writer.writerow([key, value])

create_csv(x)

def create_db():
    conn = sqlite3.connect('movies.sqlite')
    cur = conn.cursor()

    drop_imdb_sql = 'DROP TABLE IF EXISTS "IMDb"'
    drop_movies_sql = 'DROP TABLE IF EXISTS "Movies"'

    create_imdb_sql = '''
        CREATE TABLE IF NOT EXISTS "IMDb" (
            "Id" INTEGER PRIMARY KEY AUTOINCREMENT,
            "Title" TEXT NOT NULL,
            "Year"
        )
    '''
    create_movies_sql = '''
        CREATE TABLE IF NOT EXISTS 'Movies'(
            'Id' INTEGER PRIMARY KEY AUTOINCREMENT,
            'Title' TEXT NOT NULL,
            'Runtime' TEXT NOT NULL,
            'Rated' TEXT NOT NULL,
            'Country' TEXT NOT NULL
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
    base_url = client_key
    movies = requests.get(base_url).json()

    insert_movies_sql = '''
        INSERT INTO Movies
        VALUES (NULL, ?, ?, ?, ?)
    '''

    conn = sqlite3.connect('movies.sqlite')
    cur = conn.cursor()
    for m in movies:
        cur.execute(insert_movies_sql,
            [
                m[0:6],
                m[1],
                m[2],
                m[2]
            ]
        )
    conn.commit()
    conn.close()
load_movies()


def load_imdb():

    titles = []
    years =[]


    url = 'https://www.imdb.com/list/ls068082370/'
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    for movie in soup.find_all(class_ = 'lister-item-header'):
        title = movie.find('a').contents[0]
        titles.append(title)
        year = movie.find('span', class_ = 'lister-item-year text-muted unbold').text.strip()
        years.append(year)
        movie_data = dict(zip(titles, years))


    insert_imdb_sql = '''
        INSERT INTO IMDb
        VALUES (NULL, ?, NULL)
    '''

    conn = sqlite3.connect('movies.sqlite')
    cur = conn.cursor()
    for k in movie_data:
        cur.execute(insert_imdb_sql,
        [
            k[0:],
        ]
    )

    conn.commit()
    conn.close()
load_imdb()

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
    xvals = ['2001', '2003', '1994', '1995', '1999', '2000', '2008', '1980']
    yvals = [7, 5, 4, 4, 4, 4, 4, 3]

    bar_data = go.Bar(x=xvals, y=yvals)
    basic_layout = go.Layout(title="Most Common Years of Movies in the Top 100")
    fig = go.Figure(data=bar_data, layout=basic_layout)

    fig_ = fig.show()
    return fig_

if __name__ == "__main__":

    count  = 0
    while count >= 0:
        count += 1
        search_term = input("Enter a search term to get Movie Ratings, or 'quit' to exit, or 'graph' \n")
        search_term.lower()
        if search_term == 'graph':
            plot_year()
        if search_term == "exit":
            exit()
        if search_term.isalpha():
            try:
                info_from_OMDb_results(search_term)
            except KeyError:
                print('invalid movie')
        else:
            print('[Error] Enter a proper Movie name')