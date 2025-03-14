import configparser
import pandas as pd #type: ignore
import os
import networkx as nx #type: ignore
import matplotlib.pyplot as plt #type: ignore

config = configparser.ConfigParser()
config.read('../cfg/config.ini')

data_dir = config['DEFAULT']['data_dir']
data_filename = config['DEFAULT']['cleaned_data']

csv_file_path = os.path.join(data_dir, data_filename)

chunk_size = 1000000  # Ajuster selon la mémoire disponible
chunk_state = 1
pd.set_option('display.max_columns', None)

# Déterminer les jeux les plus fréquents
print("Détermination des jeux les plus populaires...")
game_counts = pd.Series(dtype=int)
for chunk in pd.read_csv(csv_file_path, chunksize=chunk_size, usecols=['game_name']):
    print(f"Processing rows {chunk_state*chunk_size}")
    chunk_state += 1
    game_counts = game_counts.add(chunk['game_name'].value_counts(), fill_value=0)

top_games = set(game_counts.nlargest(15).index)
print(f"Top jeux : {top_games}")

# Initialiser le graphe de connexion entre jeux
G = nx.Graph()
previous_game_by_player = {}
chunk_state = 1

# Parcours par chunk
for chunk in pd.read_csv(csv_file_path, chunksize=chunk_size):
    print(f"Processing rows {chunk_state*chunk_size}")
    chunk_state += 1
    chunk['start'] = pd.to_datetime(chunk['start'], format='%Y-%m-%d %H:%M:%S', errors='coerce')
    chunk.sort_values(['player_id', 'start'], inplace=True)

    # Construire les connexions entre jeux
    for player_id, group in chunk.groupby('player_id'):
        previous_game = previous_game_by_player.get(player_id)
        for game in group['game_name']:
            if game not in top_games:
                continue
            if previous_game and previous_game in top_games and previous_game != game:
                if G.has_edge(previous_game, game):
                    G[previous_game][game]['weight'] += 1
                else:
                    G.add_edge(previous_game, game, weight=1)
            previous_game = game if game in top_games else previous_game
        previous_game_by_player[player_id] = previous_game

# Identification des clusters
clusters = [{game} for game in G.nodes()]

# Fonction pour visualiser le graphe clairement
def plot_graph(G):
    plt.figure(figsize=(15, 10))
    pos = nx.circular_layout(G)

    node_sizes = [G.degree(node) * 500 for node in G.nodes()]

    nx.draw_networkx_nodes(G, pos,
                           node_color='skyblue',
                           node_size=node_sizes,
                           alpha=0.9)

    for u,v in G.edges():
        G[u][v]['weight'] = 0 if G[u][v]['weight'] < 30000 else G[u][v]['weight']

    edge_widths = [G[u][v]['weight'] * 0.00002 for u, v in G.edges()]


    nx.draw_networkx_edges(G, pos, width=edge_widths, alpha=0.5)

    nx.draw_networkx_labels(G, pos, font_size=12, font_weight='bold')

    plt.title('Connexions entre les Top Jeux BGA', fontsize=16)
    plt.axis('off')
    plt.tight_layout()
    output_dir = '../out'
    os.makedirs(output_dir, exist_ok=True)
    plt.savefig(os.path.join(output_dir, 'bga_top_games_graph.png'))

# Générer et sauvegarder le graphe
plot_graph(G)

# Sauvegarder le graphe
nx.write_gexf(G, '../out/bga_top_games_graph.gexf')
