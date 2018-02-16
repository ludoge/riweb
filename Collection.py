import datetime
import nltk
import string
import os
import math
import matplotlib.pyplot as plt
from itertools import groupby
from threading import Thread, RLock
from queue import Queue


nbThreadMap = 2
nbThreadReduce = 2


def intToVBCode(number):
    """ Convert an integer into a byte array in Variable Byte Code (VBC) """
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
    """ Read an open file to get the first number in VB code into an integer """
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
    """ Main class to deal with collections """

    def __init__(self, indexLocation = None):
        self.indexLocation = indexLocation # Location on hard-drive to save the inverted index
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
        """ Get common words from a file in the CACM folder """
        with open("Data/CACM/common_words", mode='r') as file:
            self.commonWords = file.read().splitlines()
            self.commonWords += list(string.punctuation)

    def _indexToBinary(self, file):
        """ Convert the inverted index in VB Code to be saved in an open file """

        for indexTerm in self.invertedIndex:
            vbcode = bytearray([])
            term_code = intToVBCode(indexTerm[0])
            previous_posting_id = 0
            for posting in indexTerm[1]:
                posting_id_diff = posting[0] - previous_posting_id
                previous_posting_id = posting[0]
                term_code.extend(intToVBCode(posting_id_diff))
                term_code.extend(intToVBCode(posting[1]))
            # An integer is put at the beginning of this byte array for the current term in order to know how many
            # postings there are before the next term
            vbcode.extend(intToVBCode(len(indexTerm[1])))
            vbcode.extend(term_code)
            file.write(vbcode)

    def _binaryToIndex(self, file):
        """ Read an open file in VB Code to get the inverted index """
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
        """ Save the inverted index on hard-drive """
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
        """ Load inverted index from hard-drive """
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

    def answerQuestion(self):
        """ To answer the questions from the exercise about collections """

        common_words = self.commonWords
        nb_documents = 0
        tokens = []
        vocabulary_frequency = {}
        half_tokens = []
        half_vocabulary_frequency = {}

        with open("Data/CACM/cacm.all", mode="r") as all:
            readLine = False
            for line in all:
                if line[:1] == ".":
                    readLine = False
                if readLine:
                    new_tokens = [x for x in nltk.wordpunct_tokenize(line.lower()) if x not in common_words]
                    tokens += new_tokens
                    if nb_documents % 2 == 1:
                        half_tokens += new_tokens
                if line[:2] == ".I":
                    nb_documents += 1
                if line[:2] in [".T", ".W", ".K"]:
                    readLine = True

        for token in tokens:
            if token not in vocabulary_frequency:
                vocabulary_frequency[token] = 1
            else:
                vocabulary_frequency[token] += 1

        nb_tokens = len(tokens)
        size_vocabulary = len(vocabulary_frequency)

        for token in half_tokens:
            if token not in half_vocabulary_frequency:
                half_vocabulary_frequency[token] = 1
            else:
                half_vocabulary_frequency[token] += 1

        nb_half_tokens = len(half_tokens)
        size_half_vocabulary = len(half_vocabulary_frequency)

        b = math.log(size_vocabulary / size_half_vocabulary) / math.log(nb_tokens / nb_half_tokens)
        k = size_vocabulary/(math.pow(nb_tokens, b))

        token_estimation = 1000000
        estimated_size = int(k * math.pow(token_estimation, b))

        print('\nExercice 1')
        print(f'{nb_tokens} tokens found in this collection.')

        print('\nExercice 2')
        print(f'{size_vocabulary} words in the vocabulary.')

        print('\nExercice 3')
        print('For half of the collection, we get:')
        print(f'{nb_half_tokens} tokens')
        print(f'{size_half_vocabulary} words in the vocabulary.')
        print("Parameters for Heaps' law are therefore:")
        print(f"    k = {k}         b = {b}")

        print('\nExercice 4')
        print(f"With Heaps' law, vocabulary size for {token_estimation} tokens would be {estimated_size} words.")

        frequencies = list(vocabulary_frequency.values())
        frequencies.sort()
        frequencies = frequencies[::-1]
        ranks = range(1, len(frequencies) + 1)

        logfrequencies = [math.log(x) for x in frequencies]
        logranks = [math.log(x) for x in ranks]

        f, (ax1, ax2) = plt.subplots(2, 1)
        ax1.plot(ranks, frequencies)
        ax1.set_title('Frequencies in relation to Ranks')
        ax2.scatter(logranks, logfrequencies)
        ax2.set_title('log(Frequencies) in relation to log(Ranks)')

        plt.show()

    def constructIndex(self):
        """ Construct inverted index for CACM Collection (in memory) """

        # Class to describe a CACM document
        class _Document:
            def __init__(self, ID):
                self.ID = ID
                self.title = ""
                self.summary = ""
                self.keywords = ""

        # Common words
        common_words = self.commonWords

        # Reading all documents line by line
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

        # Token identification and list of term id / doc id
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

        # Inverted index creation
        self.invertedIndex = [(key, [x[1] for x in group]) for key, group in groupby(self.list, key=lambda x: x[0])]
        self.invertedIndex = [(y[0], sorted(set([(z, y[1].count(z)) for z in y[1]]))) for y in self.invertedIndex]

    def queryTest(self):
        """ To get queries and awaited responses for test """

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

    def answerQuestion(self):
        """ To answer the questions from the exercise about collections """

        common_words = self.commonWords
        nb_documents = 0
        tokens = []
        vocabulary_frequency = {}
        half_tokens = []
        half_vocabulary_frequency = {}

        for blockID in range(10):
            documentsNames = os.listdir("Data/CS276/pa1-data/" + str(blockID))
            for documentName in documentsNames:
                with open("Data/CS276/pa1-data/" + str(blockID) + "/" + documentName, mode="r") as documentFile:
                    nb_documents += 1
                    documentContent = documentFile.read().replace("\n", " ")
                    new_tokens = [x for x in nltk.wordpunct_tokenize(documentContent.lower()) if x not in common_words]
                    tokens += new_tokens
                    if nb_documents % 2 == 1:
                        half_tokens += new_tokens

        for token in tokens:
            if token not in vocabulary_frequency:
                vocabulary_frequency[token] = 1
            else:
                vocabulary_frequency[token] += 1

        nb_tokens = len(tokens)
        size_vocabulary = len(vocabulary_frequency)

        for token in half_tokens:
            if token not in half_vocabulary_frequency:
                half_vocabulary_frequency[token] = 1
            else:
                half_vocabulary_frequency[token] += 1

        nb_half_tokens = len(half_tokens)
        size_half_vocabulary = len(half_vocabulary_frequency)

        del half_tokens
        del half_vocabulary_frequency

        b = math.log(size_vocabulary / size_half_vocabulary) / math.log(nb_tokens / nb_half_tokens)
        k = size_vocabulary/(math.pow(nb_tokens, b))

        token_estimation = 1000000
        estimated_size = int(k * math.pow(token_estimation, b))

        print('\nExercice 1')
        print(f'{nb_tokens} tokens found in this collection.')

        print('\nExercice 2')
        print(f'{size_vocabulary} words in the vocabulary.')

        print('\nExercice 3')
        print('For half of the collection, we get:')
        print(f'{nb_half_tokens} tokens')
        print(f'{size_half_vocabulary} words in the vocabulary.')
        print("Parameters for Heaps' law are therefore:")
        print(f"    k = {k}         b = {b}")

        print('\nExercice 4')
        print(f"With Heaps' law, vocabulary size for {token_estimation} tokens would be {estimated_size} words.")

        frequencies = list(vocabulary_frequency.values())
        frequencies.sort()
        frequencies = frequencies[::-1]
        ranks = range(1, len(frequencies) + 1)

        logfrequencies = [math.log(x) for x in frequencies]
        logranks = [math.log(x) for x in ranks]

        f, (ax1, ax2) = plt.subplots(2, 1)
        ax1.plot(ranks, frequencies)
        ax1.set_title('Frequencies in relation to Ranks')
        ax2.scatter(logranks, logfrequencies)
        ax2.set_title('log(Frequencies) in relation to log(Ranks)')

        plt.show()

    def parseBlock(self, blockID):
        """ Create a partial inverted index (in memory) for one block """

        global nbThreadMap, nbThreadReduce

        self.invertedIndex = []

        # Common words list
        common_words = open("Data/CACM/common_words", mode='r').read().splitlines()
        common_words += list(string.punctuation)

        print("Generating index for block " + str(blockID) + "...")

        list_after_mapper = []
        docLen = self.docLen
        docId = self.docId
        termLen = self.termLen
        termId = self.termId

        locker_list = RLock()
        locker_doc = RLock()
        locker_term = RLock()
        locker_index = RLock()

        class Mapper(Thread):
            """ Mapper for the map reduce to get tokens in documents """

            def __init__(self, documentsNames):
                super().__init__()
                self.tasks = documentsNames
                self.daemon = True
                self.start()

            def run(self):
                nonlocal list_after_mapper, docLen, docId, termLen, termId, common_words
                while True:
                    documentName = self.tasks.get()
                    try:
                        # Open the document
                        documentFile = open("Data/CS276/pa1-data/" + str(blockID) + "/" + documentName, mode="r")
                        documentContent = documentFile.read().replace("\n", " ")
                        documentFile.close()
                        # Add this document's name to the list of doc id
                        with locker_doc:
                            doc_id = docLen
                            docId[str(blockID) + "/" + documentName] = doc_id
                            docLen += 1
                        # Tokenize document content
                        documentTokens = nltk.wordpunct_tokenize(documentContent)
                        documentTokens = [x for x in documentTokens if not x in common_words]
                        for token in documentTokens:
                            with locker_term:
                                if token in termId:
                                    term_id = termId[token]
                                else:
                                    term_id = termLen
                                    termLen += 1
                                    termId[token] = term_id
                            with locker_list:
                                list_after_mapper.append((term_id, doc_id))
                    finally:
                        # Mark this task as done, whether an exception happened or not
                        self.tasks.task_done()

        class MapperPool:
            """ Pool of mappers consuming tasks from a queue (of document names) """

            def __init__(self, num_threads):
                self.tasks = Queue(num_threads)
                for _ in range(num_threads):
                    Mapper(self.tasks)

            def add_task(self, documentName):
                """ Add a task to the queue """
                self.tasks.put(documentName)

            def wait_completion(self):
                """ Wait for completion of all the tasks in the queue """
                self.tasks.join()

        # Loading all documents of the current block in a mapper
        documentsNames = os.listdir("Data/CS276/pa1-data/" + str(blockID))
        mapper_pool = MapperPool(nbThreadMap)
        for name in documentsNames:
            mapper_pool.add_task(name)
        mapper_pool.wait_completion()

        self.docId = docId
        self.docLen = docLen
        self.termId = termId
        self.termLen = termLen

        list_after_mapper.sort()
        list_before_reducer = [(key, [x[1] for x in group]) for key, group in groupby(list_after_mapper, key=lambda x: x[0])]
        invertedIndex = []

        class Reducer(Thread):
            """ Reducer for the map reduce to get have a list of postings for each term """

            def __init__(self, postings):
                super().__init__()
                self.tasks = postings
                self.daemon = True
                self.start()

            def run(self):
                nonlocal invertedIndex
                while True:
                    postings_list = self.tasks.get()
                    try:
                        with locker_index:
                            invertedIndex.append(
                                (postings_list[0], sorted(set([(z, postings_list[1].count(z)) for z in postings_list[1]]))))
                    finally:
                        # Mark this task as done, whether an exception happened or not
                        self.tasks.task_done()

        class ReducerPool:
            """ Pool of reducers consuming tasks from a queue (of lists of postings) """

            def __init__(self, num_threads):
                self.tasks = Queue(num_threads)
                for _ in range(num_threads):
                    Reducer(self.tasks)

            def add_task(self, postings):
                """ Add a task to the queue """
                self.tasks.put(postings)

            def wait_completion(self):
                """ Wait for completion of all the tasks in the queue """
                self.tasks.join()

        reducer_pool = ReducerPool(nbThreadReduce)
        for postings in list_before_reducer:
            reducer_pool.add_task(postings)
        reducer_pool.wait_completion()

        # Creating inverted index
        invertedIndex.sort()
        self.invertedIndex = invertedIndex

        print("Index for block " + str(blockID) + " generated.")

        # Release memory
        del documentsNames
        del list_after_mapper
        del list_before_reducer

    def saveBlockIndex(self, blockID):
        """ Save the current partial inverted index for one block """

        if self.indexLocation is not None:
            # Save invertedIndex in variable byte code
            with open(self.indexLocation + "/" + str(blockID), mode="wb") as file:
                self._indexToBinary(file)
        else:
            print("No location specified to save inverted index for block " + str(blockID) + ".")

        # Release memory
        self.invertedIndex = []

    def mergeBlockIndex(self, blockIndexFiles):
        """ Merge all partial inverted index previously saved to get the whole inverted index """

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
                blockIndexFiles[blockID].close()
                print("Block " + str(blockID) + " has been closed.")
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
                    blockIndexFiles[blockID].close()
                    print("Block " + str(blockID) + " has been closed.")
                    del blockIndexFiles[blockID]
                    del currentTermId[blockID]
                    del currentPostings[blockID]
            termId += 1

    def constructIndex(self):
        """ Construct the inverted index block by block """

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

    answer_questions = ""
    while answer_questions not in ['Y', 'YES', 'N', 'NO']:
        answer_questions = input("Do you want to answer the questions about collections ? (YES or NO)\n> ").upper()

    if answer_questions in ['Y', 'YES']:
        collection.answerQuestion()
    elif os.path.isfile('index' + collection_name + '/docId') and os.path.isfile('index' + collection_name + '/termId') \
            and os.path.isfile('index' + collection_name + '/invertedIndex'):
        print("Start loading...")
        collection.loadIndex()
        print("Index loaded.")
    else:
        start_time = datetime.datetime.now()
        collection.constructIndex()
        print(f"Index constructed. Time elapsed: {(datetime.datetime.now()-start_time).seconds}s")
        collection.saveIndex()
        print(f"Index saved. Time elapsed: {(datetime.datetime.now()-start_time).seconds}s")
        collection.loadIndex()
        print(f"Index loaded.  Time elapsed: {(datetime.datetime.now()-start_time).seconds}s")
