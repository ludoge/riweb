from Collection import *
from collections import Counter
import datetime
from math import log10, sqrt
import nltk

common_words = open("Data/CACM/common_words", mode='r').read().splitlines()
common_words += list(string.punctuation)


class VectorRequest:
    def __init__(self, Collection, weight_type='tf_idf'):
        self.collection = Collection
        self.allTerms = range(self.collection.termLen)
        self.allDocuments = range(self.collection.docLen)
        self.index_weights = {}
        self.weight_type = 'tf_idf'

    def tf_idf_weights(self, termId):
        N = self.collection.docLen
        # for docId in range(N):
        #     self.index_weights[(docId, termId)] = 0
        postings = self.collection.invertedIndex[termId][1]
        df = len(postings)
        idf = log10(N/df)
        for posting in postings:
            docId = posting[0]
            tf = posting[1]
            self.index_weights[(termId, docId)] = tf*idf

    def normalized_tf_idf_weights(self, termId):
        N = self.collection.docLen
        postings = self.collection.invertedIndex[termId][1]
        df = len(postings)
        idf = log10(N/df)
        for posting in postings:
            docId = posting[0]
            tf = posting[1]
            self.index_weights[(termId, docId)] = (1+log10(tf))*idf


    def normalized_tf_weights(self):
        for termId in self.allTerms:
            postings = self.collection.invertedIndex[termId][1]
            max_tf = max([x[1] for x in postings])
            for posting in postings:
                docId = posting[0]
                tf = posting[1]
                self.index_weights[(termId, docId)] = tf/max_tf

    def index_request(self, request):
        request_tokens = nltk.wordpunct_tokenize(request)
        request_terms = []

        for token in request_tokens:
            try:
                request_terms += [self.collection.termId[token.lower()]]
            except:
                pass

        request_terms = list(Counter(request_terms).items())
        return request_terms

    def request_normalized_tf_idf_weights(self, request_terms):
        weights = {}

        N = self.collection.docLen

        for term in request_terms:
            tf = term[1]
            df = len(self.collection.invertedIndex[term[0]][1])
            idf = log10(N/df)

            weights[term[0]] = (1+log10(tf))*idf

        return weights

    def request_tf_idf_weights(self, request_terms):
        weights = {}

        N = self.collection.docLen

        for term in request_terms:
            tf = term[1]
            df = len(self.collection.invertedIndex[term[0]][1])
            idf = log10(N/df)

            weights[term[0]] = tf*idf

        return weights

    def request_normalized_tf_weights(self, request_terms):
        weights = {}

        max_tf = max([x[1] for x in request_terms])

        for term in request_terms:
            tf = term[1]

            weights[term[0]] = tf/max_tf

        return weights

    weight_types = {'tf_idf': (tf_idf_weights, request_tf_idf_weights),
                    'normalized_tf': (normalized_tf_weights, request_normalized_tf_weights),
                    'normalized_tf_idf': (normalized_tf_idf_weights, request_normalized_tf_idf_weights)}

    def all_weights(self):
        start_time = datetime.datetime.now()
        if self.weight_type == 'normalized_tf':
            self.normalized_tf_weights()
        else:
            for termId in self.allTerms:
                self.weight_types[self.weight_type][0](self, termId)
        print(f"{self.weight_type} scores computed in {(datetime.datetime.now() - start_time).microseconds/1000000}s")

    def cos_similarity(self, docId, request, request_weights):

        request_index = self.index_request(request)

        terms = [x[0] for x in request_index]
        docs = [x[0] for x in sum([self.collection.invertedIndex[x][1] for x in terms], [])]
        if docId not in docs:
            return 0

        #request_weights = self.request_tf_idf_weights(request_index)
        #request_weights = self.request_normalized_tf_weights(request_index)

        res = 0
        documents_norm = 0
        request_norm = 0

        for i in range(self.collection.termLen):
            try:
                documents_norm += self.index_weights[(i, docId)]
            except KeyError:
                pass

        for i in terms:
            try:
                res += self.index_weights[(i, docId)]*request_weights[i]
            except KeyError:
                pass
            request_norm += request_weights[i]**2


        try:
            res = res/(sqrt(documents_norm*request_norm))
        except ZeroDivisionError:
            res = 0
        return round(res, 6)

    def full_ranked_vector_request(self, request, number=10, measure=cos_similarity):
        weights = self.weight_types[self.weight_type][1](self, self.index_request(request))
        res = [(x, measure(self, x, request, weights)) for x in self.allDocuments]
        res = [x for x in res if x[1] > 0]
        res = sorted(res, key=lambda x: x[1])[::-1]
        try:
            res = res[:number]
        except IndexError:
            pass
        return res

    def save_weights(self):
        """Enregistre les pondérations au même endroit que l'index inversé"""
        if self.collection.indexLocation is not None:
            with open(f"{self.collection.indexLocation}/{self.weight_type}", mode="w+") as f:
                for (_termId, _docId) in self.index_weights:
                    f.write(f"{_termId} {_docId} {self.index_weights[(_termId, _docId)]}\n")

    def load_weights(self):
        if self.collection.indexLocation is not None:
            self.index_weights = {}
            with open(f"{self.collection.indexLocation}/{self.weight_type}", mode="r+") as f:
                for line in f.read().splitlines():
                    _termId, _docId, _score = int(line.split(" ")[0]), int(line.split(" ")[1]), float(
                        line.split(" ")[2])
                    self.index_weights[(_termId, _docId)] = _score



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

    # Initiate vector request
    request = VectorRequest(collection)

    # Scoring method choice
    weight_type = ""
    while weight_type not in request.weight_types:
        weight_type = input(
            f"Select a scoring method among {', '.join([str(k) for k, _ in request.weight_types.items()])}\n>")
    request.weight_type = weight_type

    #request.all_weights()

    if os.path.isfile(f"{request.collection.indexLocation}/{request.weight_type}"):
        request.load_weights()
    else:
        request.all_weights()
        request.save_weights()

    while True:
        query = input("Please enter your query:\n> ")
        start_time = datetime.datetime.now()
        if 'quit' in query:
            print("Exiting...")
            break
        response = request.full_ranked_vector_request(query)

        if response == []:
            print("No results found. Try being less specific. Some of the terms you looked for might not exist.")
        elif response is not None:
            print(f"Request found in {len(response)} documents in {(datetime.datetime.now()-start_time).seconds}s:")
            for doc_and_measure in response:
                print(f"{doc_by_id[doc_and_measure[0]]} with measure {doc_and_measure[1]}")


