from SPARQLWrapper import SPARQLWrapper, JSON


from flask import Flask, render_template, request, jsonify
app = Flask(__name__)


@app.route("/")
def serve():
    if 'class' in request.args and 'property' in request.args:
        class_uri = request.args['class']
        property_uri = request.args['property']
        points = get_points(class_uri=class_uri, property_uri=property_uri)
        points = remove_outliers(points)
        # # print "points"
        # # print points
        points_counts, labels = get_dist(points, num_of_splits=10)
        # print "x y: "
        # print points_x_y
        #points_x_y = {'points': [{'y': 97, 'x': 709.65}, {'y': 2, 'x': 709.65}, {'y': 35, 'x': 709.65}, {'y': 3, 'x': 709.65}, {'y': 25, 'x': 709.65}, {'y': 1, 'x': 709.65}, {'y': 4, 'x': 709.65}, {'y': 1, 'x': 709.65}, {'y': 2, 'x': 709.65}, {'y': 1, 'x': 709.65}]}

        #return render_template('distribution_view.html', points=str(points_x_y["points"]))
        #return render_template('distribution_view.html', class_uri=class_uri, property_uri=property_uri)
        #return render_template('distribution_view.html', points=[20,50,100])
        label = class_uri.split('/')[-1].split('#')[-1] + " - " + property_uri.split('/')[-1].split('#')[-1]
        return render_template('distribution_view.html', points=points_counts, labels=labels, label=label)
    return render_template('distribution_view.html')


def get_dist(points, num_of_splits=10):
    counts = [0] * num_of_splits
    labels = []
    points.sort()
    min_val = min(points)
    max_val = max(points)
    bucket_size = (max_val - min_val + 1)/num_of_splits
    for split_id in range(num_of_splits):
        upper_bound = (split_id+1)*bucket_size + min_val
        # for i in range(len(points)):
        #     print "i: "
        #     print i
        #     if points[i] < upper_bound:
        #         counts[split_id] += 1
        #         points.remove(points[i])
        #     else:
        #         break
        labels.append("%.2f-%.2f" % (round(split_id*bucket_size + min_val, 2), round(upper_bound, 2)))
        while(len(points)>0 and points[0] < upper_bound):
            pt = points[0]
            counts[split_id] += 1
            points.remove(pt)

    return counts, labels
    # d = {"points": []}
    # for i in range(num_of_splits):
    #     d["points"].append({"y": counts[i], "x": (split_id+0.5)*bucket_size + min_val})
    # return d


def get_points(endpoint="http://dbpedia.org/sparql", class_uri="", property_uri=""):
    sparql = SPARQLWrapper(endpoint)
    # query = """
    #     SELECT ?o
    #     WHERE {
    #         ?s a <%s>. ?s <%s> ?o FILTER ( isNumeric(?o))
    #     }""" % (class_uri, property_uri)
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
    #print results['results']
    # nums = [float(r['o']) for r in results['results']]
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



