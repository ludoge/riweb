from Collection import *
from collections import Counter
from math import log10, sqrt
import nltk

common_words = open("Data/CACM/common_words", mode='r').read().splitlines()
common_words += list(string.punctuation)


class VectorRequest:
    def __init__(self, Collection):
        self.collection = Collection
        self.allTerms = range(collection.termLen)
        self.allDocuments = range(collection.docLen)

        self.index_weights = {}

    def tf_idf_weights(self,termId):
        N = self.collection.docLen
        # for docId in range(N):
        #     self.index_weights[(docId, termId)] = 0
        postings = self.collection.invertedIndex[termId][1]
        df = len(postings)
        idf = log10(N/df)
        for posting in postings:
            docId = posting[0]
            tf = posting[1]
            self.index_weights[(termId, docId)] = (1+log10(tf))*idf

    def all_weights(self):
        for termId in self.allTerms:
            self.tf_idf_weights(termId)

    def request_weights(self, request):
        """
        :param request: string
        :return:
        """
        request_tokens = nltk.wordpunct_tokenize(request)
        request_terms = []

        for token in request_tokens:
            try:
                request_terms += [self.collection.termId[token.lower()]]
            except:
                pass

        request_terms = list(Counter(request_terms).items())

        weights = {}

        N = self.collection.docLen

        for term in request_terms:
            tf = term[1]
            df = len(self.collection.invertedIndex[term[0]][1])
            idf = log10(N/df)

            weights[term[0]] = (1+log10(tf))*idf

        return weights

    def cos_similarity(self, docId, request_weights):
        res = 0
        documents_norm = 0
        request_norm = 0

        for i in self.allTerms:
            try:
                res += self.index_weights[(i, docId)]*request_weights[i]
            except:
                pass
            try:
                documents_norm += self.index_weights[(i, docId)] ** 2
            except:
                pass
            try:
                request_norm += request_weights[i]**2
            except:
                pass

        try:
            res = res/(sqrt(documents_norm*request_norm))
        except ZeroDivisionError:
            res = 0
        return res

    def full_ranked_vector_request(self, request, measure = cos_similarity):
        weights = self.request_weights(request)
        res = [(x, measure(self, x, weights)) for x in self.allDocuments]
        res = [x for x in res if x[1] > 0]
        res = sorted(res, key=lambda x: x[1])[::-1]
        try:
            res = res[:10]
        except IndexError:
            pass
        return res


if __name__ == "__main__":
    collection = CACMCollection('test')
    collection.parseNextBlock()
    #print(collection.invertedIndex)
    request = VectorRequest(collection)

    request.all_weights()

    #print(request.index_weights)
    test_weights = request.request_weights("cat")

    #print(test_weights)

    print(request.cos_similarity(1170, test_weights))

    print(request.full_ranked_vector_request("A cat to doge the Pentomino zzz by the Recursive Use of Shibas"))



