import nltk
import string
import os
from itertools import groupby


class Collection:
    """Classe pour manipuler des collections (on pourra faire hériter d'autres classes de celle-ci pour s'adapter au
    format propre à chaque collection)."""

    def __init__(self, indexLocation = None):
        self.indexLocation = indexLocation # Emplacement où on stocke l'index inversé
        self.termId = {}
        self.termLen = 0
        self.docId = {}
        self.docLen = 0
        self.list = []
        self.invertedIndex = []
        self.commonWords = []
        self._getCommonWords()
        if self.indexLocation is not None and not os.path.exists(self.indexLocation):
            os.makedirs(self.indexLocation)

    def _getCommonWords(self):
        """Récupère la liste des mots courants."""
        with open("Data/CACM/common_words", mode='r') as file:
            self.commonWords = file.read().splitlines()
            self.commonWords += list(string.punctuation)

    def saveIndex(self):
        """ Enregistre l'indexe inversé sur disque-dur. """
        if self.indexLocation is not None:
            # Save invertedIndex
            with open(self.indexLocation + "/invertedIndex", mode="w+") as file:
                for indexTerm in self.invertedIndex:
                    file.write(str(indexTerm[0]) + " ")
                    for posting in indexTerm[1]:
                        file.write(str(posting[0]) + "-" + str(posting[1]) + " ")
                    file.write("\n")
            # Save termId
            _termById = {self.termId[term]: term for term in self.termId}
            _termLen = len(_termById)
            with open(self.indexLocation + "/termId", mode="w+") as file:
                for termId in range(_termLen):
                    file.write(str(termId) + " " + str(_termById[termId]) + "\n")
            # Save docId
            _docById = {self.docId[doc]: doc for doc in self.docId}
            with open(self.indexLocation + "/docId", mode="w+") as file:
                for docId in _docById:
                    file.write(str(docId) + " " + str(_docById[docId]) + "\n")
        else:
            print("No location specified to save inverted index.")

    def loadIndex(self):
        """ Récupère l'index inversé stocké sur disque-dur. """
        if self.indexLocation is not None:
            # Load invertedIndex
            self.invertedIndex = []
            with open(self.indexLocation + "/invertedIndex", mode="r") as file:
                line = file.readline()
                while line != "":
                    lineContent = line.replace("\n", "").split(" ")
                    self.invertedIndex.append(
                        (int(lineContent[0]), [(int(docOccurrence.split("-")[0]), int(docOccurrence.split("-")[1]))
                                           for docOccurrence in lineContent[1:] if docOccurrence != ""])
                    )
                    line = file.readline()
            # Load termId
            self.termId = {}
            with open(self.indexLocation + "/termId", mode="r") as file:
                line = file.readline().replace("\n", "")
                while line != "":
                    termId = line.split(" ")[0]
                    term = line.split(" ")[1]
                    self.termId[term] = int(termId)
                    line = file.readline().replace("\n", "")
                self.termLen = len(self.termId)
            # Load docId
            self.docId = {}
            with open(self.indexLocation + "/docId", mode="r") as file:
                line = file.readline().replace("\n", "")
                while line != "":
                    docId = line.split(" ")[0]
                    doc = line.split(" ")[1]
                    self.docId[doc] = int(docId)
                    line = file.readline().replace("\n", "")
                self.docLen = len(self.docId)
        else:
            print("No location specified to load inverted index.")

    def getTermId(self, term):
        return self.termId[term]


class CACMCollection(Collection):

    def __init__(self, indexLocation = "indexCACM"):
        Collection.__init__(self, indexLocation)

    def constructIndex(self):
        """Constuit l'indexe inversé de la collection CACM."""

        # Définition locale du format des documents de la collection CACM.
        class _Document:
            def __init__(self, ID):
                self.ID = ID
                self.title = ""
                self.summary = ""
                self.keywords = ""

        # Liste des mots courants
        common_words = self.commonWords

        # Lecture de tous les documents et récupération de leur contenu
        # Il s'agit d'une lecture ligne par ligne en repérant les marqueurs.
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
                document = _Document(int(line.split(" ")[-1].replace("\n","")))
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

        # Identification des tokens de chaque document et ajout à la liste des correspondances termId / documentId
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

        # Création de l'index inversé
        self.invertedIndex = [(key, [x[1] for x in group]) for key, group in groupby(self.list, key=lambda x: x[0])]
        self.invertedIndex = [(y[0], sorted(set([(z, y[1].count(z)) for z in y[1]]))) for y in self.invertedIndex]

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

        print("Generating index for block " + str(blockID) + "...")

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
        print("Index for block " + str(blockID) + " generated.")

        # Write index in Hard Drive
        self.writeIndex(blockID)
        print("Index for block " + str(blockID) + " saved.")


        # Release memory
        del documentsNames
        self.list = []
        self.invertedIndex = []

    def writeIndex(self, blockID):
        with open(self.indexLocation + "/" + str(blockID), mode="w+") as file:
            for indexTerm in self.invertedIndex:
                file.write(str(indexTerm[0]) + " ")
                for posting in indexTerm[1]:
                    file.write(str(posting[0]) + "-" + str(posting[1]) + " ")
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
        print("Merging index from all blocks...")

        # Reading the first line from each index
        currentLine = {}
        currentTermId = {}
        currentPostings = {}
        for blockID in range(10):
            currentLine[blockID] = blockIndexFile[blockID].readline().replace("\n", "").split(" ")
            currentTermId[blockID] = int(currentLine[blockID][0])
            currentPostings[blockID] = [(int(posting.split("-")[0]), int(posting.split("-")[1]))
                                        for posting in currentLine[blockID][1:] if posting != '']

        # Merging all lines with the smallest term id and reading the next line of those lines
        # (or close the file if it was the last line)
        termId = 0
        while termId < self.termLen:
            blocksToMerge = [blockID for blockID in currentTermId.keys() if currentTermId[blockID] == termId]
            self.invertedIndex.append([termId, []])
            for blockID in blocksToMerge:
                # Adding the invert index of this block for this term id to elements the string of doc id already found
                # for this term id.
                self.invertedIndex[termId][1] += currentPostings[blockID]
                # Reading the next line or closing this block.
                currentLine[blockID] = blockIndexFile[blockID].readline().replace("\n", "").split(" ")
                if currentLine[blockID] == [""]:
                    # Closing the block
                    print("Block " + str(blockID) + " has been closed.")
                    blockIndexFile[blockID].close()
                    del blockIndexFile[blockID]
                    del currentTermId[blockID]
                    del currentPostings[blockID]
                    del currentLine[blockID]
                else:
                    # Reading next line
                    currentTermId[blockID] = int(currentLine[blockID][0])
                    currentPostings[blockID] = [(int(posting.split("-")[0]), int(posting.split("-")[1]))
                                                for posting in currentLine[blockID][1:] if posting != '']
            termId += 1

        print("Index merged.")


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
        collection.loadIndex()

