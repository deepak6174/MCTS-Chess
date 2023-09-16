import pandas as pd
import pickle

class TrieNode:
     
    # Trie node class
    def __init__(self, depth=0, isLast=False):
        self.children = {}
 
        # isEndOfWord is True if node represent the end of the word
        self.OpeningDepth = depth
        self.isEndOfOpening = isLast 
    
    def insert(self, move):
        ro = self
        for i in move:
            if i not in ro.children:
                ro.children[i] = TrieNode(len(move))
            elif len(move) > ro.children[i].OpeningDepth:
                ro.children[i].OpeningDepth = len(move)
            ro = ro.children[i]



df_1 = pd.read_csv("a.tsv", sep='\t')
df_1 = df_1.reset_index()

df_2 = pd.read_csv("b.tsv", sep='\t')
df_2 = df_2.reset_index()

df_3 = pd.read_csv("c.tsv", sep='\t')
df_3 = df_3.reset_index()

df_4 = pd.read_csv("d.tsv", sep='\t')
df_4 = df_4.reset_index()

df_5 = pd.read_csv("e.tsv", sep='\t')
df_5 = df_5.reset_index()

df = pd.concat([df_1, df_2, df_3, df_4, df_5])
df = df.reset_index()

root = TrieNode()
for x, row in df.iterrows():
    s = row[4].split(". ")
    k = []
    for y in s[1:]:
        y = y.split(" ")
        k.append(y[0])
        if len(y) > 1:
            k.append(y[1])

    root.insert(k)


# def dfs(root):
    
#     queue = []
 
#     # Enqueue Root and initialize height
#     queue.append(root)
#     t = []
#     t.append(0)
#     k=1
#     c=0
#     while(len(queue) > 0):
 
#         # Print front of queue and
#         # remove it from queue

#         print(t[0], end=" ")
#         node = queue.pop(0)
#         t.pop(0)
        
#         k = k-1
#         # Enqueue left child
#         for x, y in node.children.items():
#             queue.append(y)
#             t.append(x)
#             c = c+1
#         if(k==0):
#             print()
#             print()
#             k=c
#             c=0


# # dfs(root)

pickle.dump(root, open('opening.pkl', 'wb'))

# r = pickle.load(open('./opening.pkl', 'rb'))
# dfs(r)