import nltk
import string
from itertools import groupby


class Collection:
    """Classe pour manipuler des collections (on pourra faire hériter d'autres classes de celle-ci pour s'adapter au format propre à chaque collection)."""

    def __init__(self,indexLocation):
        self.indexLocation = indexLocation # Emplacement où on stocke l'index inversé
        self.termId = {}
        self.termLen = 0
        self.docId = {}
        self.docLen = 0
        self.list = []
        self.invertedIndex = []

    def getTermId(self, term):
        return self.termId[term]

class CACMCollection(Collection):

    def __init__(self,indexLocation):
        Collection.__init__(self,indexLocation)

    def parseNextBlock(self):  # TODO: make sure term IDs are unique across multiple blocks !!!!

        class Document:
            def __init__(self, ID):
                self.ID = ID
                self.title = ""
                self.summary = ""
                self.keywords = ""

        common_words = open("Data/CACM/common_words", mode='r').read().splitlines()

        common_words += list(string.punctuation)

        all = open("Data/CACM/cacm.all", mode="r")

        documents = []
        readTitle = False
        readSummary = False
        readKeywords = False

        for line in all:
            if line[:1] == ".":
                readTitle = False
                readSummary = False
                readKeywords = False
            if readTitle:
                document.title = document.title + "\n" + line.lower()
            if readSummary:
                document.summary = document.summary + "\n" + line.lower()
            if readKeywords:
                document.keywords = document.keywords + "\n" + line.lower()
            if line[:2] == ".I":
                document = Document(int(line.split(" ")[-1].replace("\n","")))
                documents.append(document)
            if line[:2] == ".T":
                readTitle = True
                readSummary = False
                readKeywords = False
            if line[:2] == ".W":
                readTitle = False
                readSummary = True
                readKeywords = False
            if line[:2] == ".K":
                readTitle = False
                readSummary = False
                readKeywords = True

        for document in documents:
            self.docId[document.ID] = document.ID
            documentTokens = []
            documentTokens += nltk.wordpunct_tokenize(document.title)
            documentTokens += nltk.wordpunct_tokenize(document.summary)
            documentTokens += nltk.wordpunct_tokenize(document.keywords)
            documentTokens = [x for x in documentTokens if not x in common_words]
            for token in documentTokens:
                if token in self.termId:
                    termId = self.termId[token]
                else:
                    termId = self.termLen
                    self.termLen += 1
                    self.termId[token] = termId
                self.list.append((termId,document.ID))
        self.list.sort()
        #print(self.list[:10])
        self.invertedIndex = [(key, [x[1] for x in group]) for key, group in groupby(self.list, key=lambda x: x[0])]
        self.invertedIndex = [(y[0], sorted(set([(z, y[1].count(z)) for z in y[1]]))) for y in self.invertedIndex]
        print (self.invertedIndex[:2])

    def writeIndex(self):
        with open(self.indexLocation, mode="w+") as file:
            for indexTerm in self.invertedIndex:
                file.write(str(indexTerm[0]) + " ")
                for posting in indexTerm[1]:
                    file.write(str(posting) + " ")
                file.write("\n")

if __name__ == "__main__":

    collection = CACMCollection('test')
    collection.parseNextBlock()
    #print(collection.invertedIndex)
    print(collection.getTermId("test"))
    collection.writeIndex()
