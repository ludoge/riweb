from Collection import *
from functools import reduce

class BooleanRequest:
    def __init__(self, Collection):
        self.collection = Collection
        self.allTerms = range(collection.termLen)

    def simpleRequest(self, termId):
        return self.collection.invertedIndex[int(termId)][1]

    def notRequest(self, terms):
        posting = self.parseRequest(terms)
        return [x for x in self.allTerms if x not in posting]

    def andRequest(self, terms):
        postings = [self.parseRequest(term) for term in terms]
        return sorted(reduce(set.intersection, [set(item) for item in postings]))

    def orRequest(self, terms):
        postings = [self.parseRequest(term) for term in terms]
        return sorted(reduce(set.union, [set(item) for item in postings]))

    def parseRequest(self, request):
        #print(request)
        if request == []:
            return []
        elif len(request)==1:
            return self.simpleRequest(request[0])
        elif request[0] == "NOT":
            return self.notRequest(request[1])
        elif request[0] == "AND":
            return self.andRequest(request[1])
        elif request[0] == "OR":
            return self.orRequest(request[1])
        else:
            return self.simpleRequest(request[0])

    def parseInput(self, userInput):
        n = len(userInput)
        if userInput[:2].lower() == "or":
            return ["OR", self.parseInput(userInput[2:])]
        elif userInput[:3].lower() == "and":
            return ["AND", self.parseInput(userInput[3:])]
        elif userInput[:3].lower() == "not":
            return ["NOT", self.parseInput(userInput[3:])]
        elif userInput[0] == " ":
            return self.parseInput(userInput[1:])
        else:
            split = userInput.split(" ")
            try:
                first = [self.collection.termId[split[0].lower()]]
            except KeyError:
                first = []
            if len(split) == 1:
                return first
            else:
                return [first] + [self.parseInput(userInput[len(split[0]):])]


if __name__ == "__main__":
    collection = CACMCollection('test')
    collection.parseNextBlock()
    #print(collection.invertedIndex)
    request = BooleanRequest(collection)
    #print(request.simpleRequest(0))
    #print(request.simpleRequest(1))
    #print(request.simpleRequest(2))
    #print(request.parseRequest(["NOT",["AND",[[0], [1], [2]]]]))
    #print(request.parseRequest(request.parseInput("NOT AND 0 OR 1 2")))
    while True:
        query = input("Please enter your query in Polish notation:\n")
        print(request.parseRequest(request.parseInput(query)))
