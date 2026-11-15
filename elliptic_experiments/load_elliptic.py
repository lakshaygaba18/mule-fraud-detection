from torch_geometric.datasets import EllipticBitcoinDataset

dataset = EllipticBitcoinDataset(root="data/elliptic")
data = dataset[0]

print(data)
print("Nodes:", data.num_nodes, "| Edges:", data.num_edges)
print("Features:", data.x.shape[1])
print("Train nodes:", int(data.train_mask.sum()), "| Test nodes:", int(data.test_mask.sum()))
print("Illicit in train:", int(((data.y == 1) & data.train_mask).sum()))
print("Illicit in test:", int(((data.y == 1) & data.test_mask).sum()))