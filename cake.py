from SPARQLWrapper import SPARQLWrapper, JSON


from flask import Flask, render_template, request
app = Flask(__name__)


@app.route("/")
def serve():
    if 'class' in request.args and 'property' in request.args:
        class_uri = request.args['class']
        property_uri = request.args['property']
        points = get_points(class_uri=class_uri, property_uri=property_uri)
        points = remove_outliers(points)
        print "points"
        print points
        #return render_template('distribution_view.html', class_uri=class_uri, property_uri=property_uri)
    return render_template('distribution_view.html')


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



