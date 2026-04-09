
#lst = ['a', 'b', 'c','d','e']

#languages = lst 


#id(lst), id(languages)

#lst.append('c')

#lst 

#languages

a = [1, 2, 3]
b=a
b.append(4)
print(a)
print(a is b)

a = [1, 2, 3]
b= a[:]
b.append(4)
print(a)
print(a is b)

#Chapeter 10 

names = ['Cam', 'Wah', 'Billy']
scores = [50, 97, 85]

names_scores = list(zip(names, scores))
print(names_scores)

eng2sp = {'one':'uno', 'two':'dos', 'three':'tres'}

eng2sp['one'] #uno
eng2sp['four'] #KeyError, no four in the dictionary
'two' in eng2sp #True
len(eng2sp) #3

for k in eng2sp:
    print(k)

for k in eng2sp:
    sp = eng2sp[eng]
    if sp == 'dos':
        print(eng)


    




