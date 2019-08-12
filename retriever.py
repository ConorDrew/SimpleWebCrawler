#!/usr/bin/python3
# needs improving to remove forced type conversions

import sys
import re
import json
import math
from nltk.stem.snowball import SnowballStemmer
import string
import csv

# global declarations for doclist, postings, vocabulary
docids = []
postings = {}
cache = []
doclength = {}
vocab = []

def main():
    # code for testing offline
    if len(sys.argv) < 2:
        print('usage: ./retriever.py term [term ...]')
        sys.exit(1)
    query = sys.argv[1:]
    query_terms = []
    answer = []

    read_index_files()

    print('Query: ', query) #shows terms that were input

    for i in query: #stores terms in a list
        stripped = "".join(l for l in i if l not in string.punctuation)
        query_terms.append(stripped)


    #Stem the input to find stemmmed words in vocab
    stemmer = SnowballStemmer("english")
    query_terms = [stemmer.stem(plural) for plural in query_terms]

    answer = retrieve_bool(query_terms)

    #prints results
    print()
    i = 0
    with open('output.csv', 'w', newline='\n') as file:#store output to file for data collection
        for docid in answer:
            # only print top 10 results (un-nest for all results)
            if i < 10:
                i += 1

                print(i, cache[docid][0]) #Title
                print(docids[int(docid)]) #URL
                print(cache[docid][1]) #Snippit
                print()#space

                #stores data to CSV for collection(got top line from stackoverflow)
                spamwriter = csv.writer(file, delimiter=' ',
                                        quotechar='|', quoting=csv.QUOTE_MINIMAL)
                spamwriter.writerow(docids[int(docid)])

def read_index_files():
    ## reads existing data from index files: docids, vocab, postings
    # uses JSON to preserve list/dictionary data structures
    # declare refs to global variables
    global docids
    global postings
    global cache
    global doclength
    global vocab
    # open the files
    in_d = open('docids.txt', 'r')
    in_v = open('vocab.txt', 'r')
    in_c = open('cache.txt', 'r')
    in_l = open('doclength.txt', 'r')
    in_p = open('postings.txt', 'r')
    # load the data
    docids = json.load(in_d)
    vocab = json.load(in_v)
    cache = json.load(in_c)
    doclength = json.load(in_l)
    postings = json.load(in_p)
    # close the files
    in_d.close()
    in_v.close()
    in_c.close()
    in_l.close()
    in_p.close()

    return

def retrieve_bool(query_terms):

    global docids
    global doclength
    global cache
    global vocab
    global postings

    answer = []
    merge_list = []
    idf = {}
    scores = {}
    query_vector = []

    query_set = set(query_terms)

    for term in query_set:
        weight = 0 #set weight to 0 each term
        try:
            termid = str(vocab.index(term.lower()))#check if term is in vocab

        except:  # the term is not in the vocab
            print('Not found: ', term, ' is not in vocabulary')
            continue

        #gets the words weight

        for i in postings.get(termid):
            weight = weight + i[2] #get weight location from postings
            if weight > 0:
                #if it has a weight, give weight
                weight = weight + i[2]

        #get idf weight
        idf[termid] = (1 + math.log(len(postings.get(termid)))) / (len(doclength))

    i = -1
    ## now calculate tf*idf and score for each doc and the query
    for termid in sorted(idf, key=idf.get, reverse=True):

        i += 1
        #get vector
        query_vector.append(idf[termid] / len(query_set) + weight)

        #give post thr score for results
        for post in postings.get(termid):
            if post[0] in scores:
                scores[post[0]] += (idf.get(termid) * post[1]) / doclength[str(post[0])] * query_vector[i]
            else:
                scores[post[0]] = (idf.get(termid) * post[1]) / doclength[str(post[0])] * query_vector[i]

    # rank the list
    for docid in sorted(scores, key=scores.get, reverse=True):
        answer.append(docid)

    return answer


# Standard boilerplate to call the main() function
if __name__ == '__main__':
    main()
