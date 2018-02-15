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

    def precision_recall_points_20(self, results, expected_results, docLen):
        recall_points = []
        precision_points = []
        curr_recall = 0
        n = len(results)
        i = 0
        while curr_recall < 1 and i < n:
            new_recall = self.recall_measure(results[:i], expected_results)
            if new_recall >= curr_recall + 1/20:
                curr_recall += 1/20
                recall_points.append(curr_recall)
                precision_points.append(self.precision_measure(results[:i], expected_results))
            i += 1
        while len(recall_points) < 21:
            recall_points.append((len(recall_points)+1)/20)
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

    def global_prec_rec(self, vector_request):
        prec, rec = [0] * 21, [0] * 21
        for query in self.collection.queryTest():
            all_results = [r[0] for r in vector_request.full_ranked_vector_request(query.query, collection.docLen)]
            new_rec, new_prec = self.precision_recall_points_20(all_results, query.results, collection.docLen)
            for i in range(len(prec)):
                prec[i] += new_prec[i]
                rec[i] += new_rec[i]
        n = len(self.collection.queryTest())
        prec = [x / n for x in prec]
        rec = [x / n for x in rec]
        return prec, rec

    def average_precision(self, results, expected_results, docLen):
        precision_points = []
        curr_recall = 0
        n = len(results)
        i = 0
        while curr_recall < 1 and i < n:
            new_recall = self.recall_measure(results[:i], expected_results)
            if new_recall >= curr_recall + 1 / 20:
                curr_recall += 1 / 20
                precision_points.append(self.precision_measure(results[:i], expected_results))
            i += 1
        while len(precision_points) < 21:
            precision_points.append(1 / docLen)

        # now the actual computation
        result = 0
        for precision in precision_points:
            result += precision

        result /= len(precision_points)
        return result

    def mean_average_precision(self, vector_request):
        result = 0
        for query in self.collection.queryTest():
            all_results = [r[0] for r in vector_request.full_ranked_vector_request(query.query, collection.docLen)]
            result += self.average_precision(all_results, query.results, collection.docLen)
        result /= len(self.collection.queryTest())
        return result


if __name__ == '__main__':
    collection = Collection.CACMCollection()
    try:
        collection.loadIndex()
    except:
        collection.constructIndex()
        collection.saveIndex()
    v = VectorRequest.VectorRequest(collection)
    try:
        v.load_weights()
    except:
        v.all_weights()
    e = Evaluation(collection, v)

    # precision-recall
    points = e.global_prec_rec(v)
    e.plot_precision_recall(points)

    plt.show()

    # Mean Average Precision

    print(f"Mean Average Precision: {e.mean_average_precision(v)}")
