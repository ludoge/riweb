import nltk
import string
import os
from itertools import groupby
from threading import Thread, RLock


def intToVBCode(number):
    """ Convertit un entier en un tableau d'octets correspondant à son variable byte code """
    if not isinstance(number, int):
        raise TypeError("number converted in VB code must be an integer")
    if number < 0:
        raise ValueError("number converted in VB code must be positive")
    b = number % 128
    a = number // 128
    result = [128 + b]
    while a > 0:
        b = a % 128
        a = a // 128
        result.insert(0, b)
    return bytearray(result)


def VBCodeToFirstInt(file):
    """ Pour un fichier binaire en lecture, récupère le premier nombre codé en VB code et renvoit l'entier
     correspondant """
    value = 0
    byte = file.read(1)
    if byte==b'':
        return None
    while int.from_bytes(byte, byteorder='big') < 128:
        value = 128 * value + int.from_bytes(byte, byteorder='big')
        byte = file.read(1)
    value = 128 * value + (int.from_bytes(byte, byteorder='big') - 128)
    return value


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

    def _indexToBinary(self, file):
        """ Convertit l'index inversé en variable byte code pour une enregistrement avec compression. """

        for indexTerm in self.invertedIndex:
            vbcode = bytearray([])
            term_code = intToVBCode(indexTerm[0])
            previous_posting_id = 0
            for posting in indexTerm[1]:
                posting_id_diff = posting[0] - previous_posting_id
                previous_posting_id = posting[0]
                term_code.extend(intToVBCode(posting_id_diff))
                term_code.extend(intToVBCode(posting[1]))
            # On ajoute au début de cette chaine d'octet le nombre de postings de ce terme, afin de savoir quand
            # commence la liste de postings du terme suivant
            vbcode.extend(intToVBCode(len(indexTerm[1])))
            vbcode.extend(term_code)
            file.write(vbcode)

    def _binaryToIndex(self, file):
        """ Lit un fichier encodé en variable byte code pour récupérer l'index inversé. """
        nbPostings = VBCodeToFirstInt(file)
        while nbPostings is not None:
            termId = VBCodeToFirstInt(file)
            postings = []
            previousPostingId = 0
            for i in range(nbPostings):
                postingId = VBCodeToFirstInt(file) + previousPostingId
                postingCount = VBCodeToFirstInt(file)
                postings.append((postingId, postingCount))
                previousPostingId = postingId
            self.invertedIndex.append((termId, postings))
            nbPostings = VBCodeToFirstInt(file)

    def saveIndex(self):
        """ Enregistre l'indexe inversé sur disque-dur. """
        if self.indexLocation is not None:
            # Save invertedIndex in variable byte code
            with open(self.indexLocation + "/invertedIndex", mode="wb") as file:
                self._indexToBinary(file)
            # Save termId
            _termById = {self.termId[term]: term for term in self.termId}
            _termLen = len(_termById)
            with open(self.indexLocation + "/termId", mode="w") as file:
                for termId in range(_termLen):
                    file.write(str(termId) + " " + str(_termById[termId]) + "\n")
            # Save docId
            _docById = {self.docId[doc]: doc for doc in self.docId}
            with open(self.indexLocation + "/docId", mode="w") as file:
                for docId in _docById:
                    file.write(str(docId) + " " + str(_docById[docId]) + "\n")
        else:
            print("No location specified to save inverted index.")

    def loadIndex(self):
        """ Récupère l'index inversé stocké sur disque-dur. """
        if self.indexLocation is not None:
            # Load invertedIndex
            self.invertedIndex = []
            with open(self.indexLocation + "/invertedIndex", mode="rb") as file:
                self._binaryToIndex(file)
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

        with open("Data/CACM/query.text", mode="r") as queryText:
            queries = []
            read_query = False

            for queryLine in queryText:
                if queryLine[:1] == ".":
                    read_query = False
                if read_query:
                    query.query = (query.query + " " + queryLine.lower()).replace("\n", "")
                    while query.query[0] == " ":
                        query.query = query.query[1:]
                if queryLine[:2] == ".I":
                    query = Query(int(queryLine.split(" ")[-1].replace("\n", "")))
                    with open("Data/CACM/qrels.text", mode="r") as qrelsText:
                        for qrelsLine in qrelsText:
                            if int(qrelsLine.split(" ")[0].replace("\n", "")) == query.id:
                                query.results.append(int(qrelsLine.split(" ")[1].replace("\n", "")))
                    queries.append(query)
                if queryLine[:2] == ".W":
                    read_query = True
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

        # Release memory
        del documentsNames
        self.list = []

    def saveBlockIndex(self, blockID):
        if self.indexLocation is not None:
            # Save invertedIndex in variable byte code
            with open(self.indexLocation + "/" + str(blockID), mode="wb") as file:
                self._indexToBinary(file)
        else:
            print("No location specified to save inverted index for block " + str(blockID) + ".")

        # Release memory
        self.invertedIndex = []

    def mergeBlockIndex(self, blockIndexFiles):

        # Reading the first element from each index
        currentTermId = {}
        currentPostings = {}
        for blockID in blockIndexFiles.keys():
            nbPostings = VBCodeToFirstInt(blockIndexFiles[blockID])
            if nbPostings is not None:
                currentTermId[blockID] = VBCodeToFirstInt(blockIndexFiles[blockID])
                currentPostings[blockID] = []
                previousPostingId = 0
                for i in range(nbPostings):
                    postingId = VBCodeToFirstInt(blockIndexFiles[blockID]) + previousPostingId
                    postingCount = VBCodeToFirstInt(blockIndexFiles[blockID])
                    currentPostings[blockID].append((postingId, postingCount))
                    previousPostingId = postingId
            else:
                # Closing the block if not any term id is found
                print("Block " + str(blockID) + " has been closed.")
                blockIndexFiles[blockID].close()
                del blockIndexFiles[blockID]
                del currentTermId[blockID]
                del currentPostings[blockID]

        # Merging all elements with the smallest term id and reading the next element of those blocks
        # (or close the file if it was the last element)
        termId = 0
        while termId < self.termLen:
            blocksToMerge = [blockID for blockID in currentTermId.keys() if currentTermId[blockID] == termId]
            self.invertedIndex.append([termId, []])
            for blockID in blocksToMerge:
                # Add postings from this block for this term id to the list
                self.invertedIndex[termId][1].extend(currentPostings[blockID])
                # Reading the next line or closing this block.
                nbPostings = VBCodeToFirstInt(blockIndexFiles[blockID])
                if nbPostings is not None:
                    currentTermId[blockID] = VBCodeToFirstInt(blockIndexFiles[blockID])
                    currentPostings[blockID] = []
                    previousPostingId = 0
                    for i in range(nbPostings):
                        postingId = VBCodeToFirstInt(blockIndexFiles[blockID]) + previousPostingId
                        postingCount = VBCodeToFirstInt(blockIndexFiles[blockID])
                        currentPostings[blockID].append((postingId, postingCount))
                        previousPostingId = postingId
                else:
                    # Closing the block
                    print("Block " + str(blockID) + " has been closed.")
                    blockIndexFiles[blockID].close()
                    del blockIndexFiles[blockID]
                    del currentTermId[blockID]
                    del currentPostings[blockID]
            termId += 1

    def constructIndex(self):

        # Write inverted index for each block
        for blockID in range(10):
            self.parseBlock(blockID)

            # Write index in Hard Drive
            self.saveBlockIndex(blockID)
            print("Index for block " + str(blockID) + " saved.")

        # Open files to merge all inverted index
        blockIndexFiles = {}
        for blockID in range(10):
            blockIndexFiles[blockID] = open(self.indexLocation + "/" + str(blockID), mode="rb")

        # Merging
        print("Merging index from all blocks...")
        self.mergeBlockIndex(blockIndexFiles)
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
        print("Start loading...")
        collection.loadIndex()
        print("Index loaded.")
    else:
        collection.constructIndex()
        print("Index constructed.")
        collection.saveIndex()
        print("Index saved.")
        collection.loadIndex()
        print("Index loaded.")

