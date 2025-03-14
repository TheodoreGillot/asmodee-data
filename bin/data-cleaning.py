import configparser
import pandas as pd
import os

config = configparser.ConfigParser()
config.read('../cfg/config.ini')

data_dir = config['DEFAULT']['data_dir']
data_filename = config['DEFAULT']['data']

csv_file_path = os.path.join(data_dir, data_filename)

chunk_size = 1000000
pd.set_option('display.max_columns', None)

# Colonnes à conserver
columns_to_keep = ['player_id', 'start', 'game_name']

# Créer le fichier de sortie une seule fois
output_file = '/media/data/asmodee/cleaned_tablesPlayersList-2024.csv'

# Initialiser une variable pour gérer l'entête du CSV
first_chunk = True
chunk_state = 1

for chunk in pd.read_csv(csv_file_path, chunksize=chunk_size, usecols=columns_to_keep):
    print(f"Processing rows {chunk_state*chunk_size}")
    chunk_state += 1
    filtered_chunk = chunk
    # Filtrer les lignes sans valeurs nulles dans player_gender
    #filtered_chunk = chunk.dropna(subset=['player_gender'])

    # Supprimer la colonne player_gender après filtrage
    #filtered_chunk = filtered_chunk.drop(columns=['player_gender'])

    # Écrire chaque chunk filtré dans le fichier CSV sans charger tout en mémoire
    filtered_chunk.to_csv(output_file, mode='w' if first_chunk else 'a', index=False, header=first_chunk)
    first_chunk = False