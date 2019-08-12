import sys
import re
import string
import json
import time
from stop_words import get_stop_words
import operator
from bs4 import BeautifulSoup
from nltk.stem.snowball import SnowballStemmer

# global declarations for doclist, postings, vocabulary
docids = []
doclength = {}
cache = []
postings = {}
vocab = []

# main is used for offline testing only
def main():
    # code for testing offline

    # time start
    if len(sys.argv) != 2:
        print('usage: ./indexer.py file')
        sys.exit(1)
    filename = sys.argv[1]

    try:
        input_file = open(filename, 'r')
    except (IOError) as ex:
        print('Cannot open ', filename, '\n Error: ', ex)

    else:
        page_contents = input_file.read()  # read the input file
        url = 'http://www.' + filename + '/'
        print(url, page_contents)
        make_index(url, page_contents)

    finally:
        input_file.close()

#writes the indexs to the files
def write_index():
    # declare refs to global variables
    global docids
    global doclength
    global cache
    global postings
    global vocab

    # writes to index files: docids, vocab, postings
    outlist1 = open('docids.txt', 'w')
    outlist2 = open('vocab.txt', 'w')
    outlist3 = open('postings.txt', 'w')
    outlist4 = open('doclength.txt', 'w')
    outlist5 = open('cache.txt', 'w')

    json.dump(docids, outlist1)
    json.dump(vocab, outlist2)
    json.dump(postings, outlist3)
    json.dump(doclength, outlist4)
    json.dump(cache, outlist5)

    outlist1.close()
    outlist2.close()
    outlist3.close()
    outlist4.close()
    outlist5.close()

    return

#cleans HTML and tokenizes
def clean_html(page_contents):
    # function to clean html

    # removes tags that are not needed
    remove = r"(<script(\s|\S)*?<\/script>)|(<header(\s|\S)*?<\/header>)|(<nav(\s|\S)*?<\/nav>)|" \
             r"(<footer(\s|\S)*?<\/footer>)|(<style(\s|\S)*?<\/style>)|" \
             r"(<div(.+)?id=\"(.+)?menu\">(\s|\S)*?<\/div>)|(<div(.+)?class=\"(.+)?menu\">(\s|\S)*?<\/div>)" \
             r"(<!--(\s|\S)*?-->)|(<\/?(\s|\S)*?>)|\t|\b\\u....\b"
    regex = r"\w{3,}|\d"  # get words 3 chars or longer

    get_words = re.sub(remove, '\n', page_contents) #removes new lines
    get_words = get_words.lower() #oonverts to lower case

    get_words = re.findall(regex, get_words)  # puts words in list

    get_words = [get_words for get_words in get_words if get_words not in get_stop_words('english')]
    # uses get_stop_words to compare and remove stopwords

    #print(get_words)
    #print("------------------------------------")

    # STEM THE WORD, BASIC REMOVING ING, S AND IF ENDS WITH ED ONLY REMOVING THE D

    stemmer = SnowballStemmer("english") #stems terms with NLTK English stemmer

    page_contents = [stemmer.stem(plural) for plural in get_words]

    return page_contents

#finds keywrods in page and give them weight
def keywords(page_contents):
    soup = BeautifulSoup(page_contents, "html.parser")
    _title = [element.get_text() for element in soup.findAll('title')]#find terms in <title>
    _h1 = [element.get_text() for element in soup.findAll('h1')]#finds all header tags
    _h2 = [element.get_text() for element in soup.findAll('h2')]
    _h3 = [element.get_text() for element in soup.findAll('h3')]
    _h4 = [element.get_text() for element in soup.findAll('h4')]
    _h5 = [element.get_text() for element in soup.findAll('h5')]

    title = ' '.join(_title)
    h1 = ' '.join(_h1)
    h2 = ' '.join(_h2)
    h3 = ' '.join(_h3)
    h4 = ' '.join(_h4)
    h5 = ' '.join(_h5)

    page_contents = title + " " + h1 + " " + h2 + " " + h3 + " " + h4 + " " + h5 #puts all keywords in a list

    page_contents = page_contents.lower() #convert to lower case

    return page_contents

#gets page title and snippet
def get_title(page_contents):
    soup = BeautifulSoup(page_contents, "html.parser")
    title = soup.title.string

    _p = [element.get_text() for element in soup.findAll('p')] #find all P elements for snippit
    p = ' '.join(_p)
    p = p[0:295] + " ..." #get the first 295 chars and ad ... at the end

    page_contents = [title, p] #store title and snippet in a list

    return page_contents


def make_index(url, page_contents):
    # declare refs to global variables
    global docids
    global doclength
    global postings
    global vocab

    # first convert bytes to string if necessary
    if isinstance(page_contents, bytes):
        # page_contents = page_contents.decode('utf-8')
        page_contents = page_contents.decode('latin-1', 'ignore')
        # page_contents = page_contents.decode(encoding='utf-8', errors='ignore')
    print('===============================================')
    print('make_index: url = ', url)
    print('===============================================')

    #get all the data and store in lists
    title = get_title(page_contents)
    page_text = clean_html(page_contents)
    keywordss = keywords(page_contents)

    ##document Id to table
    docids.insert(len(docids), url)

    cache.append(title)

    docid = docids.index(url)
    docwordcount = 0

    # loop though page_text, and check if that is in vocab list
    # if it is, get vocab ID , if not Add to the list and vocab ID
    for words in page_text:
        docwordcount += 1

        # Adds to vocab
        if words in vocab:
            wordid = int(vocab.index(words))
        else:
            vocab.append(words)
            wordid = int(vocab.index(words))

        # check if word is in keywords
        if words in keywordss:
            # print(words, "is in keywords")
            if wordid not in postings:
                postings[wordid] = [[docid, 1, 1]]
            else:
                # if word is found, check if docId is in dict
                if docid in postings[wordid][-1]:  # using -1 as this is this doc would be
                    # if id is found, add 1
                    postings[wordid][-1][1] += 1
                    postings[wordid][-1][2] += 1
                else:
                    # if not found add docid and freq
                    postings[wordid].append([docid, 1, 1])
        #if word not in keyword add but dont increment weight.
        else:
            if wordid not in postings:
                postings[wordid] = [[docid, 1, 0]]
            else:
                # if word is found, check if docId is in dict
                if docid in postings[wordid][-1]:  # using -1 as this is this doc would be
                    # if id is found, add 1
                    postings[wordid][-1][1] += 1
                else:
                    # if not found add docid and freq
                    postings[wordid].append([docid, 1, 0])

    doclength[docid] = docwordcount

    return

# Standard boilerplate to call the main() function to begin
# the program.
if __name__ == '__main__':
    main()
