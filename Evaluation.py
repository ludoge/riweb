import Collection
import VectorRequest
import matplotlib.pyplot as plt

class Evaluation():
    def __init__(self, coll, req):
        self.collection = coll
        self.collection.loadIndex()
        self.vectorRequest = req

    def precision_measure(self, results, expected_results):
        pertinent_results = [x for x in set(expected_results) if x in set(results)]
        try:
            return len(pertinent_results)/len(results)
        except ZeroDivisionError:
            return 0

    def recall_measure(self, results, expected_results):
        pertinent_results = [x for x in set(expected_results) if x in set(results)]
        try:
            return len(pertinent_results)/len(expected_results)
        except ZeroDivisionError:
            return 0

    def prec_rec_measure(self, results, expected_results):
        return self.precision_measure(results, expected_results), self.recall_measure(results, expected_results)

    def precision_recall_points(self, results, expected_results, docLen):
        """
        Results parameter should be a list of all documents sorted from most to least relevant
        :param results:
        :param expected_results:
        :return:
        """
        recall_points = []
        precision_points = []
        curr_recall = 0
        n = len(results)
        i = 0
        while curr_recall < 1 and i < n:
            new_recall = self.recall_measure(results[:i], expected_results)
            if new_recall > curr_recall:
                curr_recall = new_recall
                recall_points.append(curr_recall)
                precision_points.append(self.precision_measure(results[:i], expected_results))
            i += 1
        while len(recall_points) < 1/recall_points[0]:
            recall_points.append(recall_points[-1] + recall_points[0])
            precision_points.append(1/docLen)

        # Interpolation
        for i in range(len(precision_points)):
            for j in range(i, len(precision_points)):
                if precision_points[i] < precision_points[j]:
                    precision_points[i] = precision_points[j]

        return recall_points, precision_points

    def plot_precision_recall(self, precision_recall_points):
        plt.plot(precision_recall_points[0], precision_recall_points[1])

    def E_measure(self, results, expected_results, alpha):
        try:
            return 1 - (1/(alpha/self.precision_measure(results, expected_results) + (1-alpha)/self.recall_measure(results, expected_results)))
        except ZeroDivisionError:
            return 0

    def F_measure(self, results, expected_results, alpha):
        return 1-self.E_measure(results, expected_results, alpha)

    def F1_measure(self, results, expected_results):
        return self.F_measure(results, expected_results, 1/2)

if __name__ == '__main__':
    collection = Collection.CACMCollection()
    collection.loadIndex()
    v = VectorRequest.VectorRequest(collection)
    v.all_weights()
    e = Evaluation(collection, v)
    #
    #e.parse_requests()
    #for r in e.requests.values():
    #    print(v.full_ranked_vector_request(r))
    #print([[r[0] for r in v.full_ranked_vector_request(q.query)] for q in collection.queryTest()[:2]])
    #print([q.id for q in collection.queryTest()])
    """
    recall_points, precision_points = [], []
    num_queries = len(collection.queryTest())
    for number in range (3,16):
        print(f"Evaluating precision and recall for k={number}")
        avg_rec, avg_prec = 0, 0
        for i in range(num_queries):
            q = collection.queryTest()[i]
            prec, rec = e.prec_rec_measure([r[0] for r in v.full_ranked_vector_request(q.query, number)], q.results)
            print(prec, rec)
            #recall_points.append(rec)
            #precision_points.append(prec)
            avg_rec += rec
            avg_prec += prec
        avg_rec /= num_queries
        avg_prec /= num_queries
        recall_points.append(avg_rec)
        precision_points.append(avg_prec)

    plt.plot(recall_points, precision_points, 'ro')
    plt.show()
    """
    query1 = collection.queryTest()[44]

    all_results = [r[0] for r in v.full_ranked_vector_request(query1.query, collection.docLen)]
    e.plot_precision_recall(e.precision_recall_points(all_results, query1.results, collection.docLen))
    plt.show()
