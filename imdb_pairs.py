import os
import sys
import time
import pandas as pd
from itertools import combinations
from collections import OrderedDict

SCRIPT_PATH = os.path.dirname(__file__)

MOVIES_RATINGS_PATH = 'data/movies.ratings.tsv'
NAMES_SHORT_PATH = 'data/names.short.tsv'
MOVIES_PRINCIPALS_PATH = 'data/movies.principals.tsv'

MOVIES_PATH = '{}/{}'.format(SCRIPT_PATH, MOVIES_RATINGS_PATH)
PERSONS_PATH = '{}/{}'.format(SCRIPT_PATH, NAMES_SHORT_PATH)
PRINCIPAL_PATH = '{}/{}'.format(SCRIPT_PATH, MOVIES_PRINCIPALS_PATH)

PAIR_CHOICES = {
    1: {'actor', 'actress'},
    2: {'actor', 'actor'},
    3: {'actress', 'actress'},
    4: {'actor', 'director'},
    5: {'actress', 'director'},
    6: {'producer', 'director'},
    7: {'producer', 'actor'},
    8: {'producer', 'actress'},
}


def process_film_principals(principals, pairs_choice):
    """
    (list, int) -> generator
    Receives list of person and film category, returns combinations of two
    principals: [('nm0151653', 'director'), ('nm0156955', 'actor'), ('nm0423663', 'actor'), ('nm0593014', 'actress')]

    >>> p = [('nm0151653', 'director'), ('nm0156955', 'actor'), ('nm0423663', 'actor'), ('nm0593014', 'actress')]
    >>> list(process_film_principals(p, 4))
    [(('nm0151653', 'director'), ('nm0156955', 'actor')), (('nm0151653', 'director'), ('nm0423663', 'actor'))]
    """
    # Sort on principal id
    p_sorted = sorted(principals, key=lambda x: x[0])

    # Return combinations as pairs
    pairs = combinations(p_sorted, 2)
    return filter(lambda x: set((x[0][1], x[1][1])) == PAIR_CHOICES[pairs_choice], pairs)


def enrich_movies_titles(tconst_set):
    """
    set -> dict

    This function works with external files, so there is no doctests
    Function finds names of films, year and rating due to their code number

    >>> sorted(enrich_movies_titles({'tt0000574', 'tt0000615'}).items(), key=lambda x: x[0])
    [('tt0000574', 'The Story of the Kelly Gang (1906) with rating 6.2'), ('tt0000615', 'Robbery Under Arms (1907) with rating 5.1')]
    """
    movies = pd.read_csv(
        MOVIES_PATH,
        delimiter='\t',
        header=0,
        low_memory=False
    )

    result = {}
    for tconst in tconst_set:
        movie = movies[movies['tconst'] == tconst]
        movie_title = '{} ({}) with rating {}'.format(
            movie['primaryTitle'].values[0],
            movie['startYear'].values[0],
            movie['averageRating'].values[0],
        )
        result[tconst] = movie_title

    return result


def enrich_persons_names(nconst_set):
    """
    set -> dict
    This function works with external files, so there is no doctests
    Function finds real names of principals due to their code number

    >>> sorted(enrich_persons_names({'nm0000007', 'nm0000008'}).items(), key=lambda x: x[0])
    [('nm0000007', 'Humphrey Bogart'), ('nm0000008', 'Marlon Brando')]

    """
    persons = pd.read_csv(
        PERSONS_PATH,
        delimiter='\t',
        header=0,
        low_memory=False,
    )

    result = {}
    for nconst in nconst_set:
        person = persons[persons['nconst'] == nconst]
        person_name = person['primaryName'].values[0]
        result[nconst] = person_name

    return result


def print_result(win_pairs):
    """
    Prints result in human readable format

    :param win_pairs:
    e.g. [((('nm0151653', 'director'), ('nm0156955', 'actor')), ['tt0065450', 'tt0066587', 'tt0067026']),
     ((('nm0423663', 'actor'), ('nm0593014', 'director')), ['tt0068815', 'tt0068816'])]

    :return: nothing

    Prints this win_pairs structure like

    Cheh Chang involved as director and David Chiang involved as actor in 3 films:
    Vengeance (1970) with rating 7.2
    Xiao sha xing (1970) with rating 7.2
    Duel of the Iron Fist (1971) with rating 7.1

    Tomisaburô Wakayama involved as actor and Kenji Misumi involved as director in 2 films:
    Lone Wolf and Cub: Sword of Vengeance (1972) with rating 7.9
    Lone Wolf and Cub: Baby Cart at the River Styx (1972) with rating 8.0
    """
    all_tconst = set([tconst for entry in win_pairs for tconst in entry[1]])
    all_nconst = set([person[0] for entry in win_pairs for person in entry[0]])

    movies_dict = enrich_movies_titles(all_tconst)
    names_dict = enrich_persons_names(all_nconst)

    for win_pair in win_pairs:
        pair = win_pair[0]
        films_tconst = win_pair[1]
        print('{} involved as {} and {} involved as {} in {} films:'.format(
            names_dict[pair[0][0]],
            pair[0][1],
            names_dict[pair[1][0]],
            pair[1][1],
            len(films_tconst)
        ))
        for film_tconst in films_tconst:
            print(movies_dict[film_tconst])
        print('\n')


def ask_pair_choice():
    """
    Function asks a user to enter pairs he wants to investigate
    """
    print('Please, choose which pairs you want to compare\n')
    print(
        '1 - If you want to compare top films by actor and actress\n'
        '2 - If you want to compare by actor and actor\n'
        '3 - If you want to compare by actress and actress\n'
        '4 - If you want to compare by actor and director\n'
        '5 - If you want to compare by actress and director\n'
        '6 - If you want to compare by producer and director\n'
        '7 - If you want to compare by producer and actor\n'
        '8 - If you want to compare by producer and actress\n'
    )

    for _ in range(4):
        user_choice = int(input('Your choice: '))
        if 1 <= user_choice <= 8:
            return user_choice
        else:
            print('Please, try again. Read information carefully to enter correct numbers')


def ask_rating():
    """
    Function asks a user to enter minimum and maximum rating he wants to compare in
    """
    for _ in range(4):
        try:
            min_rating = float(input('Please, enter the minimum rating from 0.0 to 10.0\n '
                                     '(Consider the fact, that minimum and maximum cannot be the same): '))
            max_rating = float(input('Now, please, enter the maximum rating from 0.0 to 10.0: '))

            if 0.0 > min_rating or min_rating > 10.0 or 0.0 > max_rating or max_rating > 10.0 \
                    or min_rating >= max_rating:
                print('Sorry, you entered the wrong data. Please, try again...')
            else:
                return min_rating, max_rating

        except ValueError:
            print('You did not input a number')


def ask_year():
    """
    Function asks user to enter minimum and maximum year to filter info by this criteria
    """
    floor = 1900
    ceil = 2018
    for _ in range(4):
        try:
            min_year = float(input('Please, enter the minimum year from 1900 to 2018\n'
                                   '(Consider the fact that minimum year cannot be the same as maximum): '))
            max_year = float(input('Please, enter the maximum year from 1900 to 2018: '))

            if floor > min_year or min_year > ceil \
                    or floor > max_year or max_year > ceil \
                    or min_year >= max_year:
                print('Sorry, you entered the wrong data. Please, try again...')
            else:
                return min_year, max_year

        except ValueError:
            print('You did not input a number')


def ask_result_length():
    """
    Function asks a user to enter number of pairs he wants to get
    """
    floor = 1
    ceil = 10
    for _ in range(4):
        try:
            number_of_pairs = int(input('Please, enter a number of pairs you want to get after analyzing: '))

            if floor > number_of_pairs or ceil < number_of_pairs:
                print('Sorry, you entered the wrong data. Please, try again...')
            else:
                return number_of_pairs

        except ValueError:
            print('You did not input a number')


def draw_rotating_bar(iteration):
    bars = list('/-\|')
    sys.stdout.write('\r')
    next_symbol = bars[iteration % len(bars)]
    sys.stdout.write(next_symbol)
    sys.stdout.flush()


if __name__ == '__main__':
    pairs_choice = ask_pair_choice()
    min_year, max_year = ask_year()
    min_rating, max_rating = ask_rating()
    number_of_pairs = ask_result_length()

    # open file with movie title and rating info
    movies = pd.read_csv(
        MOVIES_PATH,
        delimiter='\t',
        header=0,
        low_memory=False
    )

    # Filter movies regarding user choice
    filtered_movies = movies[
        (movies['startYear'] >= str(min_year)) & (movies['startYear'] <= str(max_year)) &
        (movies['averageRating'] >= min_rating) & (movies['averageRating'] <= max_rating)
    ]

    # Select movies ids' based on filtered result
    movies_ids_set = set(filtered_movies['tconst'])

    # Just to clean memory
    del filtered_movies
    del movies

    # Open file with movies principals as iterator to save memory
    principals_iter = pd.read_csv(
        PRINCIPAL_PATH,
        delimiter='\t',
        header=0,
        iterator=True,
        chunksize=1000,
    )

    print('\nWe are trying to get some results for you. This may take a couple of minutes. Please relax.')

    start_time = time.time()

    pair_success = dict()
    film_id = 0
    print('\nIt can take from 3 to 5 minutes. Do not worry, it is working!')

    # Started iterating over principals_iter chunks
    chunk_number = 0
    for chunk in principals_iter:
        draw_rotating_bar(chunk_number)
        chunk_number += 1
        for index, row in chunk.iterrows():
            # If tconst in movies filter
            if row['tconst'] in movies_ids_set:
                if film_id != row['tconst']:
                    if film_id != 0:
                        # here we should process prev film principals
                        principals_pairs = process_film_principals(film_principals, pairs_choice)

                        for pair in principals_pairs:
                            if pair in pair_success:
                                pair_success[pair].add(film_id)
                            else:
                                pair_success[pair] = set([film_id])

                    # New film founded. Start working with a new film data
                    film_id = row['tconst']
                    film_principals = []
                    if row['category'] in PAIR_CHOICES[pairs_choice]:
                        film_principals.append((row['nconst'], row['category']))
                else:
                    if row['category'] in PAIR_CHOICES[pairs_choice]:
                        film_principals.append((row['nconst'], row['category']))

    pair_success_items = pair_success.items()

    if len(pair_success_items) == 0:
        print('\nWe are sorry, we could not find any results matching your request')
    else:
        print('\nWow! We have found some interesting results for you. Now we are printing it. \n\n')

        od = OrderedDict(sorted(pair_success.items(), key= lambda x: len(x[1])))

        first_five_candidates = [od.popitem() for _ in range(number_of_pairs)]

        print_result(first_five_candidates)

        end_time = time.time()

        print('It took - {} seconds'.format(round(end_time-start_time, 2)))
