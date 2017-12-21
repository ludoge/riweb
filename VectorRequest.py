from Collection import *
from math import log10



class VectorRequest:
    def __init__(self, Collection):
        self.collection = Collection
        self.allTerms = range(collection.termLen)

        self.weights = {}

    def tf_idf_weights(self,termId):
        N = self.collection.docLen
        for docId in range(N):
            self.weights[(docId, termId)] = 0
        postings = self.collection.invertedIndex[termId][1]
        df = len(postings)
        idf = log10(N/df)
        for posting in postings:
            docId = posting[0]
            tf = posting[1]
            self.weights[(termId, docId)] = (1+log10(tf))*idf

    def all_weights(self):
        for termId in self.allTerms:
            self.tf_idf_weights(termId)

if __name__ == "__main__":
    collection = CACMCollection('test')
    collection.parseNextBlock()
    #print(collection.invertedIndex)
    request = VectorRequest(collection)

    request.all_weights()

    print(request.weights[(0, 0)])


