import os
import os.path
from re import M
from typing import Type
import requests
from bs4 import BeautifulSoup
import json
from colorama import init, Fore, Back, Style
init(autoreset=True)

DISCARD_PARTIAL_DATA = True
YELLOW_RATING_THRESHOLD = 6
GREEN_RATING_THRESHOLD = 8

DATA_FILENAME = "data.json"
DIRECTORY = "D:\Torrents"

class MovieManager:
    def __init__(self, directory, data_filename):
        self.directory = directory
        self.extensions = [".mp4", ".mkv"]
        self.movies = []
        self.discarded = []
        self.first_time = True

        datafile = open(data_filename)
        self.data = json.load(datafile)

    def is_integer(self, str):
        try:
            int(str)
            return True
        except ValueError:
            return False

    def cap_sentence(self, s):
        return ' '.join(w[:1].upper() + w[1:] for w in s.split(' '))

    # TODO: make more complete
    def is_show(self, name):
        name = name.upper()
        for idx, letter in enumerate(name):
            if letter == "S":
                season_string = name[idx:idx+6]
                digits = len([ch for ch in season_string if ch.isdigit()])
                if "E" in season_string and digits == 4:
                    return True
        return False

    def save_data(self):
        with open(DATA_FILENAME, 'w') as json_file:
            json.dump(self.data, json_file, indent=4)

    def get_movie_names(self):
        for dirpath, dirnames, filenames in os.walk(self.directory):
            for filename in [f for f in filenames]:
                if filename[-4:] in self.extensions and not self.is_show(filename):
                    filename = filename.replace(" ", ".")
                    movie_name_parts = filename.split(".")
                    movie_name = ""
                    for idx, i in enumerate(movie_name_parts):
                        if i.isdigit() and len(i) == 4:
                            movie_name = self.cap_sentence(
                                " ".join(movie_name_parts[:idx])) + f" {i}"
                            break
                    if movie_name:
                        self.movies.append(movie_name)

    def get_movie_data(self):
        for movie in self.movies:
            imdb = self.get_imdb_id(movie)
            self.get_imdb_data(imdb, movie)
        return self.data

    def get_movies(self):
        self.get_movie_names()
        self.get_movie_data()
        self.save_data()
        if self.first_time: self.first_time = False
        return self.data, self.discarded

    def get_imdb_data(self, id, name):
        try:
            return self.data[name]["data"]
        except KeyError:
            url = f"https://www.imdb.com/title/{id}/"
            r = requests.get(url)
            soup = BeautifulSoup(r.text, "html.parser")
            djson = json.loads(soup.find('script', type='application/json', id='__NEXT_DATA__').string)

            try:
                length = djson["props"]["pageProps"]["aboveTheFoldData"]["runtime"]["seconds"]
            except TypeError:
                if DISCARD_PARTIAL_DATA:
                    del self.data[name]
                    self.discarded.append(name)
                    return False
                length = 0

            rating = djson["props"]["pageProps"]["aboveTheFoldData"]["ratingsSummary"]["aggregateRating"]
            genres = djson["props"]["pageProps"]["aboveTheFoldData"]["genres"]["genres"]
            genres = [genre["text"] for genre in genres]

            if rating == None:
                self.discarded.append(name)
                del self.data[name]
                return False

            simplified = {
                "length": length,
                "rating": rating,
                "genres": genres
            }

            self.data[name]["data"] = simplified
            return simplified

    def get_imdb_id(self, name):
        try:
            return self.data[name]["id"]
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
            id = result[result.index('href="/title/') + len('href="/title/'):result.index('/"')]

            self.data[name] = {"id": id}

            return id

    def show_movies(self):
        if self.first_time:
            movies, discarded = self.get_movies()
        else:
            movies, discarded = self.data, self.discarded
        sorted_movies = dict(sorted(movies.items(), key=lambda item: item[1]['data']["rating"], reverse=True))

        idx = 0
        for name, mdata in sorted_movies.items():
            mdata = mdata["data"]
            idx+=1

            if mdata["rating"] >= GREEN_RATING_THRESHOLD: color = Fore.GREEN
            elif mdata["rating"] >= YELLOW_RATING_THRESHOLD: color = Fore.YELLOW
            else: color = Fore.RED

            print(color + f"{idx}. ({mdata['rating']}) {name}: {', '.join(mdata['genres'])}. ")



class CommandManager:
    def __init__(self, manager):
        self.validCommands = ["discarded", "movies"]

    def validCommand(self, command):
        return command in self.validCommands

    def showDiscarded(self):
        print(Fore.GREEN + ", ".join(manager.discarded))

    def doCommand(self, com):
        comdict = {
            "discarded": self.showDiscarded(),
            "movies": manager.show_movies()
        }
        comdict[com]
        return True

    def askCommand(self):
        com = input()
        valid = self.validCommand(com)
        if valid:
            self.doCommand(com)
            return True
        else:
            return False


manager = MovieManager(DIRECTORY, DATA_FILENAME)
manager.show_movies()

command = CommandManager(manager)
while True:
    try:
        command.askCommand()
    except KeyboardInterrupt:
        break