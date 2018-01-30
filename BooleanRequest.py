from collections import deque
from Collection import *
import datetime
from functools import reduce
import logging

class BooleanRequest:
    def __init__(self, Collection):
        self.collection = Collection
        self.allTerms = range(collection.termLen)

    def simpleRequest(self, termId):
        try:
            return [x[0] for x in self.collection.invertedIndex[int(termId)][1]]
        except TypeError:
            return self.orRequest([termId])

    def polishNotationRequest(self, tokens):
        token = tokens.popleft().lower()
        if token == 'or':
            return list(set(self.polishNotationRequest(tokens) + self.polishNotationRequest(tokens)))
        if token == 'and':
            a, b = self.polishNotationRequest(tokens), self.polishNotationRequest(tokens)
            return list(set([x for x in a if x in b]))
        if token == 'not':
            a = self.polishNotationRequest(tokens)
            return [x for x in range(1, self.collection.docLen) if x not in a]
        else:
            try:
                return self.simpleRequest(self.collection.termId[token.lower()])
            except KeyError:
                return []


if __name__ == "__main__":

    # Collection choice
    collection_name = ""
    while collection_name not in ['CACM', 'CS276']:
        collection_name = input("Choose a collection among 'CACM' and 'CS276'\n> ").upper()

    if collection_name == 'CS276':
        collection = CS276Collection()
    else:
        collection = CACMCollection()

    if os.path.isfile('index' + collection_name + '/docId') and os.path.isfile('index' + collection_name + '/termId') \
            and os.path.isfile('index' + collection_name + '/invertedIndex'):
        collection.loadIndex()
    else:
        collection.constructIndex()
        collection.saveIndex()

    doc_by_id = {}
    for doc_name in collection.docId:
        doc_by_id[collection.docId[doc_name]] = doc_name

    # Initiate boolean request
    request = BooleanRequest(collection)
    #print(request.simpleRequest(0))
    #print(request.simpleRequest(1))
    #print(request.simpleRequest(2))
    #print(request.parseRequest(["NOT",["AND",[[0], [1], [2]]]]))
    #print(request.parseRequest(request.parseInput("NOT AND 0 OR 1 2")))
    while True:
        query = input("Please enter your query in Polish notation:\n> ")
        start_time = datetime.datetime.now()
        if '!' in query:
            print("Exiting...")
            break
        try:
            response = request.polishNotationRequest(deque(query.split(" ")))
            # response = request.parseRequest(request.parseInput(query))
        except(IndentationError):
            response = None
            print("Invalid request. Valid operations are 'or', 'and' and 'not'. Enter '!' to quit.")

        if response == []:
            print("No results found. Try being less specific. Some of the terms you looked for might not exist.")
        elif response is not None:
            print(f"Request found in {len(response)} documents in {(datetime.datetime.now()-start_time).seconds}s:")
            for doc_and_measure in response:
                print(doc_by_id[doc_and_measure])

