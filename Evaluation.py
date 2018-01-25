import Collection
import VectorRequest

class Evaluation():
    def __init__(self, coll, req):
        self.collection = coll
        self.collection.parseNextBlock()
        self.vectorRequest = req
        self.requests = {}
        self.expected_results = {}

    def parse_requests(self, location="Data/CACM/query.text"):
        with open(location, 'r') as f:
            i = 0
            read = False
            for line in f:
                if line[:2] == ".I":
                    i += 1
                    self.requests[i] = ""
                if read and not line[0] == ".":
                    self.requests[i] = self.requests[i] + " " + line
                if line[:1] == ".":
                    read = False
                if line[:2] == ".W":
                    read = True


if __name__ == '__main__':
    collection = Collection.CACMCollection('test')
    collection.parseNextBlock()
    v = VectorRequest.VectorRequest(collection)
    v.normalized_tf_weights()
    e = Evaluation(collection, v)

    e.parse_requests()
    for r in e.requests.values():
        print(v.full_ranked_vector_request(r))