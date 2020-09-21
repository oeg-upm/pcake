import math
from SPARQLWrapper import SPARQLWrapper, JSON

from flask import Flask, render_template, request, send_from_directory
app = Flask(__name__)

default_endpoint = 'http://dbpedia.org/sparql'


@app.route("/")
def serve():
    num_of_bins = 0
    if 'class' in request.args and 'property' in request.args and 'endpoint' in request.args:
        endpoint = request.args['endpoint'].strip()
        class_uri = request.args['class']
        property_uri = request.args['property']
        points = get_points(endpoint=endpoint, class_uri=class_uri, property_uri=property_uri)
        remove_out = False
        if 'outliers' in request.args:
            print("outlier is here")
            print(request.args)
            if request.args['outliers'] == 'on':
                remove_out = True
            else:
                remove_out = False
        if remove_out:
            print("Will remove outliers")
            points = remove_outliers(points)
        else:
            print("Won't remove the outliers")
        num_of_points = len(points)
        if 'num_of_bins' in request.args and request.args['num_of_bins'].strip() != '0' and request.args['num_of_bins'].isdigit():
            num_of_bins = int(request.args['num_of_bins'])
        else:
            print("will compute the number of bins")
            num_of_bins = int(math.ceil(math.sqrt(len(points))))
        points_counts, labels = get_dist(points, num_of_bins=num_of_bins)
        label = class_uri.split('/')[-1].split('#')[-1] + " - " + property_uri.split('/')[-1].split('#')[-1]
        return render_template('distribution_view.html', points=points_counts, labels=labels, label=label,
                           class_uri=class_uri, property_uri=property_uri, splits=num_of_bins,
                        num_of_points=num_of_points, remove_outliers=remove_out)
    return render_template('distribution_view.html', splits=num_of_bins, num_of_points=0, remove_outliers=False, endpoint=default_endpoint)


@app.route("/reexpression")
def reexpression():
    num_of_bins = 0
    if 'class' in request.args and 'property' in request.args and 'endpoint' in request.args:
        endpoint = request.args['endpoint'].strip()
        class_uri = request.args['class']
        property_uri = request.args['property']
        points = get_points(endpoint=endpoint, class_uri=class_uri, property_uri=property_uri)
        points = remove_outliers(points)
        reexpressed = [math.sqrt(x) for x in points if x >= 0]
        num_of_points = len(points)
        if 'num_of_bins' in request.args and request.args['num_of_bins'].strip() != '0' and request.args['num_of_bins'].isdigit():
            num_of_bins = int(request.args['num_of_bins'])
        else:
            print("will compute the number of bins")
            num_of_bins = int(math.ceil(math.sqrt(len(points))))
        points_counts, labels = get_dist(points, num_of_bins=num_of_bins)
        reexpressed_counts, _ = get_dist(reexpressed, num_of_bins=num_of_bins)
        label = class_uri.split('/')[-1].split('#')[-1] + " - " + property_uri.split('/')[-1].split('#')[-1]
        return render_template('reexpression_view.html', points=points_counts, labels=labels, label=label, label2="rexpressed",
                           class_uri=class_uri, property_uri=property_uri, splits=num_of_bins,
                               num_of_points=num_of_points, reexpressed=reexpressed_counts)
    return render_template('reexpression_view.html', splits=num_of_bins, num_of_points=0, endpoint=default_endpoint)


@app.route("/compare")
def compare():
    num_of_bins = 0
    prob = True
    if 'class' in request.args and 'property1' in request.args and 'property2' in request.args and 'endpoint' in request.args:
        class_uri = request.args['class'].strip()
        property_uri1 = request.args['property1'].strip()
        property_uri2 = request.args['property2'].strip()
        endpoint = request.args['endpoint'].strip()
        print("***********\n\n\nThe end points: "+endpoint)
        # points1 = get_points(endpoint=endpoint, class_uri=class_uri, property_uri=property_uri1)
        points1 = get_points(class_uri=class_uri, property_uri=property_uri1)
        points1 = remove_outliers(points1)
        # points2 = get_points(endpoint=endpoint, class_uri=class_uri, property_uri=property_uri2)
        points2 = get_points(class_uri=class_uri, property_uri=property_uri2)
        points2 = remove_outliers(points2)
        num_of_points1 = len(points1)
        num_of_points2 = len(points2)
        if 'num_of_bins' in request.args and request.args['num_of_bins'].strip() != '0' and request.args['num_of_bins'].isdigit():
            num_of_bins = int(request.args['num_of_bins'])
        else:
            print("will compute the number of bins")
            num_of_points = min(num_of_points1, num_of_points2)
            num_of_bins = int(math.ceil(math.sqrt(num_of_points)))
        points_counts1, labels = get_dist(points1, num_of_bins=num_of_bins, prob=prob)
        points_counts2, _ = get_dist(points2, num_of_bins=num_of_bins, prob=prob)
        label1 = class_uri.split('/')[-1].split('#')[-1] + " - " + property_uri1.split('/')[-1].split('#')[-1]
        label2 = class_uri.split('/')[-1].split('#')[-1] + " - " + property_uri2.split('/')[-1].split('#')[-1]
        return render_template('compare_view.html', points=points_counts1, labels=labels, label=label1, label2=label2,
                           class_uri=class_uri, property_uri1=property_uri1,property_uri2=property_uri2,
                            splits=num_of_bins, num_of_points2=num_of_points2, num_of_points1=num_of_points1,
                               points1=points_counts1, points2=points_counts2, endpoint=endpoint)
    return render_template('compare_view.html', splits=num_of_bins, num_of_points1=0, num_of_points2=0, endpoint=default_endpoint)


@app.route("/download")
def download_values():
    fdir = 'downloads'
    if 'class' in request.args and 'property' in request.args:
        class_uri = request.args['class']
        property_uri = request.args['property']
        points = get_points(class_uri=class_uri, property_uri=property_uri)
        import os
        if not os.path.exists(fdir):
            os.makedirs(fdir)
        fname = property_uri+" - "+class_uri+".txt"
        fname = fname.replace('http://','').replace('https://','').replace('/','-')
        outf_path = os.path.join(fdir, fname)
        txt = "\n".join([str(p) for p in points])
        print("out path: <"+outf_path+">")
        f = open(outf_path, 'w')
        f.write(txt)
        f.close()
        return send_from_directory(directory=fdir, filename=fname, as_attachment=True)
    else:
        return "class and/or property are not passed"


def get_dist(points, num_of_bins, prob=False):
    """
    :param points:
    :param num_of_bins:
    :param prob: whether to have the counts or the probability of items
    :return:
    """
    if len(points) < 1:
        return [], []
	print("num of points: "+str(len(points)))
    tot = len(points) * 1.0
    counts = [0] * num_of_bins
    labels = []
    points.sort()
    min_val = min(points)
    max_val = max(points)
    bucket_size = (max_val - min_val)/num_of_bins
    for split_id in range(num_of_bins):
        upper_bound = (split_id+1)*bucket_size + min_val
        labels.append("%.2f-%.2f" % (round(split_id*bucket_size + min_val, 2), round(upper_bound, 2)))
        while(len(points)>0 and points[0] < upper_bound):
            pt = points[0]
            counts[split_id] += 1
            points.remove(pt)
        if prob:
            counts[split_id] = counts[split_id] / tot
    return counts, labels

# def get_dist(points, num_of_bins):
#     if len(points) < 1:
#         return [], []
# 	print("num of points: "+str(len(points)))
#     counts = [0] * num_of_bins
#     labels = []
#     points.sort()
#     min_val = min(points)
#     max_val = max(points)
#     bucket_size = (max_val - min_val + 1)/num_of_bins
#     for split_id in range(num_of_bins):
#         upper_bound = (split_id+1)*bucket_size + min_val
#         labels.append("%.2f-%.2f" % (round(split_id*bucket_size + min_val, 2), round(upper_bound, 2)))
#         while(len(points)>0 and points[0] < upper_bound):
#             pt = points[0]
#             counts[split_id] += 1
#             points.remove(pt)
#     return counts, labels


def get_points(endpoint="http://dbpedia.org/sparql", class_uri="", property_uri=""):
    sparql = SPARQLWrapper(endpoint)
    query = """
        SELECT ?o
        WHERE {
            ?s a <%s>. ?s <%s> ?o.
        }""" % (class_uri, property_uri)
    # query = """
    #     SELECT ?o
    #     WHERE {
    #         ?s a <%s>. ?s <%s> ?o
    #     } LIMIT 200""" % (class_uri, property_uri)
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
    #k = 1.5
    k = 2
    # [Q1 - k(Q3 - Q1), Q3 + k(Q3 - Q1)]
    lower_bound = q1 - k*(q3-q1)
    upper_bound = q3 + k*(q3-q1)
    for c in column:
        if c >= lower_bound and c <= upper_bound:
            clean_column.append(c)
    return clean_column


if __name__ == '__main__':
    app.run(debug=True)



