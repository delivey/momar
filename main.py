import os
import os.path
import requests
from bs4 import BeautifulSoup
import json

DATA_FILENAME = "data.json"
datafile = open(DATA_FILENAME)
directory = "D:\Torrents"
extensions = [".mp4", ".mkv"]
movies = []
data = json.load(datafile)

def is_integer(str):
    try:
        int(str)
        return True
    except ValueError:
        return False

def cap_sentence(s):
  return ' '.join(w[:1].upper() + w[1:] for w in s.split(' ')) 

# TODO: make more complete
def is_show(name):
    name = name.upper()
    for idx, letter in enumerate(name):
        if letter == "S":
            season_string = name[idx:idx+6]
            digits = len([ch for ch in season_string if ch.isdigit()])
            if "E" in season_string and digits == 4:
                return True
    return False

def save_data():
    with open(DATA_FILENAME, 'w') as json_file:
        json.dump(data, json_file, indent=4)

for dirpath, dirnames, filenames in os.walk(directory):
    for filename in [f for f in filenames]:
        if filename[-4:] in extensions and not is_show(filename):
            filename = filename.replace(" ", ".")
            movie_name_parts = filename.split(".")
            movie_name = ""
            for idx, i in enumerate(movie_name_parts):
                if i.isdigit() and len(i) == 4:
                    movie_name = cap_sentence(" ".join(movie_name_parts[:idx])) + f" {i}"
                    break
            if movie_name:
                movies.append(movie_name)

def get_imdb_data(id, name):
    try:
        return data[name]["data"]
    except KeyError:
        url = f"https://www.imdb.com/title/{id}/"
        r = requests.get(url)
        soup = BeautifulSoup(r.text, "html.parser")
        djson = json.loads(soup.find('script', type='application/json', id='__NEXT_DATA__').string)

        length = djson["props"]["pageProps"]["aboveTheFoldData"]["runtime"]["seconds"]
        rating = djson["props"]["pageProps"]["aboveTheFoldData"]["ratingsSummary"]["aggregateRating"]
        genres = djson["props"]["pageProps"]["aboveTheFoldData"]["genres"]["genres"]
        genres = [genre["text"] for genre in genres]

        simplified = {
            "length": length,
            "rating": rating,
            "genres": genres
        }

        data[name]["data"] = simplified 

        return simplified


def get_imdb_id(name):
    try:
        return data[name]["id"]
    except KeyError:
        params = {
            'q': name,
            's': 'tt',
            'ttype': 'ft',
            'ref_': 'fn_ft',
        }
        r = requests.get("https://www.imdb.com/find", params=params)
        soup = BeautifulSoup(r.text, "html.parser")
        result = str(soup.select_one('td.result_text'))
        id = result[result.index('href="/title/')+len('href="/title/'):result.index('/"')]

        data[name] = {"id": id}

        return id

for idx, movie in enumerate(movies):
    try:
        imdb = get_imdb_id(movie) 
        movie_data = get_imdb_data(imdb, movie)
        print(f"{idx}. {movie}: {', '.join(movie_data['genres'])}. ")
    except:
        save_data()

save_data()