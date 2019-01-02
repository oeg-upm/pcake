import math
from SPARQLWrapper import SPARQLWrapper, JSON


from flask import Flask, render_template, request
app = Flask(__name__)


@app.route("/")
def serve():
    num_of_splits = 0
    if 'class' in request.args and 'property' in request.args:
        if 'num_of_splits' in request.args:
            num_of_splits = int(request.args['num_of_splits'])
        class_uri = request.args['class']
        property_uri = request.args['property']
        points = get_points(class_uri=class_uri, property_uri=property_uri)
        points = remove_outliers(points)
        points_counts, labels, num_of_splits = get_dist(points, num_of_splits=num_of_splits)
        label = class_uri.split('/')[-1].split('#')[-1] + " - " + property_uri.split('/')[-1].split('#')[-1]
        return render_template('distribution_view.html', points=points_counts, labels=labels, label=label,
                           class_uri=class_uri, property_uri=property_uri, splits=num_of_splits)
    return render_template('distribution_view.html', splits=num_of_splits)


def get_dist(points, num_of_splits=10):
    if len(points) < 1:
        return [], []
    num_of_bins = num_of_splits
    if num_of_splits == 0:
        num_of_bins = int(math.ceil(math.sqrt(len(points))))
        print("num of bins: "+str(num_of_bins))
	print("num of points: "+str(len(points)))
    counts = [0] * num_of_bins
    labels = []
    points.sort()
    min_val = min(points)
    max_val = max(points)
    bucket_size = (max_val - min_val + 1)/num_of_bins
    for split_id in range(num_of_bins):
        upper_bound = (split_id+1)*bucket_size + min_val
        labels.append("%.2f-%.2f" % (round(split_id*bucket_size + min_val, 2), round(upper_bound, 2)))
        while(len(points)>0 and points[0] < upper_bound):
            pt = points[0]
            counts[split_id] += 1
            points.remove(pt)
    return counts, labels, num_of_bins


def get_points(endpoint="http://dbpedia.org/sparql", class_uri="", property_uri=""):
    sparql = SPARQLWrapper(endpoint)
    query = """
        SELECT ?o
        WHERE {
            ?s a <%s>. ?s <%s> ?o
        } LIMIT 200""" % (class_uri, property_uri)
    print "query: "
    print query
    sparql.setQuery(query)
    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()
    print "results: "
    vals = [r['o']['value'] for r in results['results']['bindings']]
    return get_numericals(vals)


def get_numericals(column):
    """
    :param column:
    :return: list of numeric values
    """
    clean_column = []
    for c in column:
        if isinstance(c, (int, float)):
            clean_column.append(c)
        elif isinstance(c, basestring):
            if '.' in c or ',' in c or c.isdigit():
                try:
                    clean_column.append(float(c.replace(',', '')))
                except Exception as e:
                    pass
    return clean_column


def remove_outliers(column):
    """
    :param column: list of numbers
    :return:
    """
    if len(column) < 1:
        return []
    import numpy as np
    clean_column = []
    q1 = np.percentile(column, 25)
    q3 = np.percentile(column, 75)
    k = 1.5
    # [Q1 - k(Q3 - Q1), Q3 + k(Q3 - Q1)]
    lower_bound = q1 - k*(q3-q1)
    upper_bound = q3 + k*(q3-q1)
    for c in column:
        if c >= lower_bound and c <= upper_bound:
            clean_column.append(c)
    return clean_column


if __name__ == '__main__':
    app.run(debug=True)



