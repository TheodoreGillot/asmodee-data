import configparser
import pandas as pd
import os
import networkx as nx
import matplotlib.pyplot as plt

config = configparser.ConfigParser()
config.read('../cfg/config.ini')

data_dir = config['DEFAULT']['data_dir']
data_filename = config['DEFAULT']['data_filename']

csv_file_path = os.path.join(data_dir, data_filename)

graph_threshold = 5  
chunk_size = 1000000  

G = nx.Graph()
previous_game_by_player = {}

for chunk in pd.read_csv(csv_file_path, chunksize=chunk_size):
    chunk['start'] = pd.to_datetime(chunk['start'], format='%Y-%m-%d %H:%M:%S', errors='coerce')
    chunk.sort_values(['player_id', 'start'], inplace=True)

    for player_id, group in chunk.groupby('player_id'):
        previous_game = previous_game_by_player.get(player_id)
        for game in group['game_name']:
            if previous_game and previous_game != game:
                if G.has_edge(previous_game, game):
                    G[previous_game][game]['weight'] += 1
                else:
                    G.add_edge(previous_game, game, weight=1)
            previous_game = game

        previous_game_by_player[player_id] = previous_game

weak_edges = [(u, v) for u, v, w in G.edges(data='weight') if w < graph_threshold]
G.remove_edges_from(weak_edges)

isolated_nodes = list(nx.isolates(G))
G.remove_nodes_from(isolated_nodes)

clusters = nx.community.louvain_communities(G, weight='weight')
graph_threshold = 20  # augmenter selon le besoin

def plot_graph(G, clusters, top_n_labels=50):
    plt.figure(figsize=(20, 15))
    pos = nx.spring_layout(G, k=0.3, seed=42)

    colors = plt.cm.tab20(range(len(clusters)))
    node_colors = {}
    for idx, cluster in enumerate(clusters):
        for node in cluster:
            node_colors[node] = colors[idx]

    node_sizes = [G.degree(node) * 30 for node in G.nodes()]

    nx.draw_networkx_nodes(G, pos,
                           node_color=[node_colors[node] for node in G.nodes()],
                           node_size=node_sizes,
                           alpha=0.8)

    nx.draw_networkx_edges(G, pos, alpha=0.2)

    top_nodes = sorted(G.degree, key=lambda x: x[1], reverse=True)[:top_n_labels]
    labels = {node: node for node, degree in top_nodes}
    nx.draw_networkx_labels(G, pos, labels=labels, font_size=10, font_weight='bold')

    plt.title('Graph amélioré des connexions entre Jeux BGA', fontsize=15)
    plt.axis('off')
    plt.show()

plot_graph(G, clusters)

cluster_output = {f'Cluster {i+1}': list(cluster) for i, cluster in enumerate(clusters)}
cluster_df = pd.DataFrame(dict([(k, pd.Series(v)) for k,v in cluster_output.items()]))
cluster_df.to_csv('game_clusters.csv', index=False)

nx.write_gexf(G, '../bga_games_graph.gexf')