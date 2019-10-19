import csv
import os
import pandas as pd

SCRIPT_PATH = os.path.dirname(__file__)

TITLE_BASICS_PATH = 'data/title.basics.tsv'
NAME_BASICS_PATH = 'data/name.basics.tsv'
TITLE_RATINGS_PATH = 'data/title.ratings.tsv'
TITLE_PRINCIPALS_PATH = 'data/title.principals.tsv'

MOVIES_RATINGS_PATH = 'data/movies.ratings.tsv'
NAMES_SHORT_PATH = 'data/names.short.tsv'
MOVIES_PRINCIPALS_PATH = 'data/movies.principals.tsv'

IMDB_TITLE_BASICS_PATH = '{}/{}'.format(SCRIPT_PATH, TITLE_BASICS_PATH)
IMDB_NAME_BASICS_PATH = '{}/{}'.format(SCRIPT_PATH, NAME_BASICS_PATH)
IMDB_TITLE_RATINGS_PATH = '{}/{}'.format(SCRIPT_PATH, TITLE_RATINGS_PATH)
IMDB_TITLE_PRINCIPALS_PATH = '{}/{}'.format(SCRIPT_PATH, TITLE_PRINCIPALS_PATH)

MOVIES_PATH = '{}/{}'.format(SCRIPT_PATH, MOVIES_RATINGS_PATH)
PERSONS_PATH = '{}/{}'.format(SCRIPT_PATH, NAMES_SHORT_PATH)
PRINCIPALS_PATH = '{}/{}'.format(SCRIPT_PATH, MOVIES_PRINCIPALS_PATH)

print('Start selecting movies only and merge with ratings data')

titles = pd.read_csv(
    IMDB_TITLE_BASICS_PATH,
    delimiter='\t',
    header=0,
    usecols=['tconst', 'startYear', 'titleType', 'primaryTitle'],
    low_memory=False
)

movies = titles[(titles['titleType'] == 'movie') & (titles['startYear'] >= '1800')]

ratings = pd.read_csv(
    IMDB_TITLE_RATINGS_PATH,
    delimiter='\t',
    header=0,
    low_memory=False
)

movies_with_rates = pd.merge(movies, ratings, on='tconst')

# Keep set of movies ids for further purposes
movies_tconst_set = set(movies_with_rates['tconst'])

# Save movies only
movies_with_rates.to_csv(
    MOVIES_PATH,
    sep='\t',
    columns=['tconst', 'startYear', 'primaryTitle', 'averageRating', 'numVotes'],
    index=False
)

del movies_with_rates
del movies
print('Successfully saved movies.ratings.tsv.')

print('Start selecting principals data for movies only.')

# Reduce principals size by selecting movies related info filtering by movies_tconst_set plus filtering by subset of
# principal category
principals_iter = pd.read_csv(
    IMDB_TITLE_PRINCIPALS_PATH,
    delimiter='\t',
    header=0,
    usecols=['tconst', 'nconst', 'category'],
    iterator=True,
    chunksize=1000,
)

category_filter = ['director', 'writer', 'producer', 'actor', 'actress']

# Keep persons ids for further filtering to reduce persons names file size.
person_nconst_set = set()

with open(PRINCIPALS_PATH, 'w', newline='') as csvfile:
    f_writer = csv.writer(csvfile, delimiter='\t')
    f_writer.writerow(['tconst', 'nconst', 'category'])
    for chunk in principals_iter:
        for index, row in chunk.iterrows():
            # Check whether the row relates to movies
            if row['tconst'] in movies_tconst_set and row['category'] in category_filter:
                f_writer.writerow([row['tconst'], row['nconst'], row['category']])
                person_nconst_set.add(row['nconst'])

print('Successfully saved movies.principals.tsv .')

print('Start selecting persons data for movies only.')

names = pd.read_csv(
    IMDB_NAME_BASICS_PATH,
    delimiter='\t',
    header=0,
    usecols=['nconst', 'primaryName'],
    low_memory=False
)

# Filter persons name by person_nconst_set
filtered_names = names[names['nconst'].isin(person_nconst_set)]

filtered_names.to_csv(
    PERSONS_PATH,
    sep='\t',
    index=False
)

print('Successfully created names.short.tsv')
