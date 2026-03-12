d = {'cam': 1, 'wah': 2, 'chloe':3}

len(d) 

for name in d:
    print(name)

for name in d.keys():
    print(name) #traversal

for grade in d.values():
    print(grade) 

for name, grade in d.items():
    print(name, grade) 

names = lisyt(d.keys())

names
for i  in range(len(names)):
    print(names[i])

for name in names:
    print(name)

for i, name in enumerate(names):
    print(i, name)

for name, grade in d.items():
    print(name, grade)  

######################################3

def histogram(s):
    """return a dictionary mapping each character in s to the number of times it appears in s"""
    d = {}
    for c in s:
        d[c] = d.get(c, 0) + 1
    return d

result = histogram('bookkeeper')
print(result['o'])
print(result.get('o', 0))
print(result.get('z', 0))

