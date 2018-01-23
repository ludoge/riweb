import nltk
import string
import os
from itertools import groupby


class Collection:
    """Classe pour manipuler des collections (on pourra faire hériter d'autres classes de celle-ci pour s'adapter au format propre à chaque collection)."""

    def __init__(self, indexLocation = None):
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

    def __init__(self, indexLocation = None):
        Collection.__init__(self, indexLocation)

    def parseNextBlock(self):  # TODO: make sure term IDs are unique across multiple blocks !!!!

        class Document:
            def __init__(self, ID):
                self.ID = ID
                self.title = ""
                self.summary = ""
                self.keywords = ""

        # Common words list
        common_words = open("Data/CACM/common_words", mode='r').read().splitlines()
        common_words += list(string.punctuation)

        # Reading all documents to get their content
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
        self.docLen = len(documents)

        # Tokenizing and creating inverted index
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
        #print (self.invertedIndex[:2])

    def writeIndex(self):
        with open(self.indexLocation, mode="w+") as file:
            for indexTerm in self.invertedIndex:
                file.write(str(indexTerm[0]) + " ")
                for posting in indexTerm[1]:
                    file.write(str(posting) + " ")
                file.write("\n")

    def queryTest(self):

        class Query:
            def __init__(self, id):
                self.id = id
                self.query = ""
                self.results = []

        queryText = open("Data/CACM/query.text", mode="r")
        qrelsText = open("Data/CACM/qrels.text", mode="r")

        queries = []
        readQuery = False

        for queryLine in queryText:
            if queryLine[:1] == ".":
                readQuery = False
            if readQuery:
                query.query = (query.query + " " + queryLine.lower()).replace("\n", "")
                while query.query[0] == " ":
                    query.query = query.query[1:]
            if queryLine[:2] == ".I":
                query = Query(int(queryLine.split(" ")[-1].replace("\n", "")))
                for qrelsLine in qrelsText:
                    if int(qrelsLine.split(" ")[0].replace("\n", "")) == query.id:
                        query.results.append(int(qrelsLine.split(" ")[1].replace("\n", "")))
                queries.append(query)
            if queryLine[:2] == ".W":
                readQuery = True
        queryText.close()
        qrelsText.close()

        return queries

class CS276Collection(Collection):

    def __init__(self, indexLocation = "indexCS276"):
        Collection.__init__(self, indexLocation)

    def parseBlock(self, blockID):

        # Common words list
        common_words = open("Data/CACM/common_words", mode='r').read().splitlines()
        common_words += list(string.punctuation)

        # Loading all documents of the current block in memory
        documentsNames = os.listdir("Data/CS276/pa1-data/" + str(blockID))
        for name in documentsNames:
            documentFile = open("Data/CS276/pa1-data/" + str(blockID) + "/" + name, mode="r")
            documentContent = documentFile.read().replace("\n"," ")
            documentFile.close()
            # Add this document's name to the list of doc id
            docId = self.docLen
            self.docId[str(blockID) + "/" + name] = docId
            self.docLen += 1
            # Tokenize document content
            documentTokens = nltk.wordpunct_tokenize(documentContent)
            documentTokens = [x for x in documentTokens if not x in common_words]
            for token in documentTokens:
                if token in self.termId:
                    termId = self.termId[token]
                else:
                    termId = self.termLen
                    self.termLen += 1
                    self.termId[token] = termId
                self.list.append((termId, docId))
        self.list.sort()

        # Creating inverted index
        self.invertedIndex = [(key, [x[1] for x in group]) for key, group in groupby(self.list, key=lambda x: x[0])]
        self.invertedIndex = [(y[0], sorted(set([(z, y[1].count(z)) for z in y[1]]))) for y in self.invertedIndex]

        # Write index in Hard Drive
        self.writeIndex(blockID)

        # Release memory
        del documentsNames
        self.list = []
        self.invertedIndex = []

    def writeIndex(self, blockID):
        with open(self.indexLocation + "/" + str(blockID), mode="w+") as file:
            for indexTerm in self.invertedIndex:
                file.write(str(indexTerm[0]) + " ")
                for posting in indexTerm[1]:
                    file.write(str(posting) + " ")
                file.write("\n")

    def constructIndex(self):

        # Write inverted index for each block
        for blockID in range(10):
            self.parseBlock(blockID)

        # Open file to write the final inverted index and each partial reverted index
        # indexFile = open(self.indexLocation + "/invertedIndex", mode="w+") /!\
        blockIndexFile = {}
        for blockID in range(10):
            blockIndexFile[blockID] = open(self.indexLocation + "/" + str(blockID), mode="r")

        # Reading line by line each partial reverted index and merging all lines with the smallest term id
        # blockIndexFileOpen = range(10)

        # Reading the first line from each index
        currentLine = {}
        currentTermId = {}
        currentString = {}
        for blockID in range(10):
            currentLine[blockID] = blockIndexFile[blockID].readline()
            firstSpace = currentLine[blockID].index(" ")
            currentTermId[blockID] = int(currentLine[blockID][0:firstSpace])
            currentString[blockID] = currentLine[blockID][firstSpace + 1:].replace("\n", "")

        # Merging all lines with the smallest term id and reading the next line of those lines
        # (or close the file if it was the last line)
        termId = 0
        while termId < self.termLen:
            blocksToMerge = [blockID for blockID in currentTermId.keys() if currentTermId[blockID] == termId]
            self.invertedIndex.append("")
            for blockID in blocksToMerge:
                # Adding the invert index of this block for this term id to elements the string of doc id already found
                # for this term id.
                self.invertedIndex[termId] += currentString[blockID]
                # Reading the next line or closing this block.
                currentLine[blockID] = blockIndexFile[blockID].readline()
                if currentLine[blockID] == "":
                    # Closing the block
                    blockIndexFile[blockID].close()
                    del blockIndexFile[blockID]
                    del currentTermId[blockID]
                    del currentString[blockID]
                    del currentLine[blockID]
                else:
                    # Reading next line
                    firstSpace = currentLine[blockID].index(" ")
                    currentTermId[blockID] = int(currentLine[blockID][0:firstSpace])
                    currentString[blockID] = currentLine[blockID][firstSpace + 1:].replace("\n", "")
            termId += 1





if __name__ == "__main__":

    collection = CS276Collection()
    collection.constructIndex()
    print(collection.invertedIndex)
    #print(collection.getTermId("test"))
    #collection.writeIndex()
