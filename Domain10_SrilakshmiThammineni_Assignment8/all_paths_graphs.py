from collections import defaultdict

class Graph:
    def __init__(self):
        self.graph = defaultdict(list)

    def add_edge(self, u, v):
        self.graph[u].append(v)

    def find_all_paths(self, start, end):
        result = []
        path = []

        def dfs(current):
            path.append(current)
            if current == end:
                result.append(path[:])
            else:
                for neighbor in self.graph[current]:
                    dfs(neighbor)
            path.pop()

        dfs(start)
        return result

g = Graph()
g.add_edge(0, 1)
g.add_edge(0, 2)
g.add_edge(1, 2)
g.add_edge(2, 0)
g.add_edge(2, 3)
g.add_edge(3, 3)

start, end = 2, 3
print("All Paths:", g.find_all_paths(start, end))
