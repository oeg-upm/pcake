import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
import pandas as pd
import os
from SPARQLWrapper import SPARQLWrapper, JSON

import six
import random
import string
import math


def compare(class_uri, property_uri1, property_uri2, label1a="", label2a="", data=None, data_label="data", num_of_bins=0, endpoint=None,
            outfile=None):
    prob = True
    if endpoint is None:
        if 'endpoint' not in os.environ:
            raise Exception("Either pass the endpoint url or set the environment variable 'endpoint'")
        else:
            endpoint = os.environ['endpoint']

    points1 = get_points(endpoint=endpoint, class_uri=class_uri, property_uri=property_uri1)
    points1 = remove_outliers(points1)
    points2 = get_points(endpoint=endpoint, class_uri=class_uri, property_uri=property_uri2)
    points2 = remove_outliers(points2)
    num_of_points1 = len(points1)
    num_of_points2 = len(points2)
    if num_of_bins == 0:
        num_of_points = min(num_of_points1, num_of_points2)
        num_of_bins = int(math.ceil(math.sqrt(num_of_points)))

    points_counts1, labels = get_dist(points1, num_of_bins=num_of_bins, prob=prob)
    points_counts2, _ = get_dist(points2, num_of_bins=num_of_bins, prob=prob)
    label1 = class_uri.split('/')[-1].split('#')[-1] + " - " + property_uri1.split('/')[-1].split('#')[-1]
    label2 = class_uri.split('/')[-1].split('#')[-1] + " - " + property_uri2.split('/')[-1].split('#')[-1]
    label3 = data_label

    label1 += label1a
    label2 += label2a

    df1 = pd.DataFrame(zip(points_counts1, labels, [label1]*len(points_counts1)), columns=["frequency", "value", "source"])
    df2 = pd.DataFrame(zip(points_counts2, labels, [label2]*len(points_counts2)), columns=["frequency", "value", "source"])
    df = df1.append(df2, ignore_index=True)
    # print(df)
    if data:
        if type(data) == str:
            data = data.split('\n')
            data = [d.strip() for d in data]

        data = get_numericals(data)
        points_counts3, _ = get_dist(data, num_of_bins=num_of_bins, prob=prob)
        df3 = pd.DataFrame(zip(points_counts3, labels, [label3] * len(points_counts3)), columns=["frequency", "value", "source"])
        df = df.append(df3, ignore_index=True)
        ax = sns.lineplot(x="value", y="frequency", hue="source", data=df)
    else:
        ax = sns.lineplot(x="value", y="frequency", hue="source", data=df)
    ax.set(xlabel=None)
    ax.set(xticklabels=[])
    if outfile:
        ax.figure.savefig("%s.svg" % outfile)
        ax.figure.clf()
    else:
        plt.show()


def get_numericals(column):
    """
    :param column:
    :return: list of numeric values
    """
    clean_column = []
    for cc in column:
        c = cc
        if isinstance(c, (int, float)):
            clean_column.append(c)
        elif isinstance(c, six.string_types):
            c = c.strip()
            if '.' in c or ',' in c or c.isdigit():
                try:
                    clean_column.append(float(c.replace(',', '')))
                except Exception as e:
                    pass
    return clean_column


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
    # print("endpoint: "+endpoint)
    # print("query: ")
    # print(query)
    sparql.setQuery(query)
    sparql.setReturnFormat(JSON)
    results = sparql.query().convert()
    # print("results: "+str(results))
    # print "results: "+str(len(results['results']['bindings']))
    vals = [r['o']['value'] for r in results['results']['bindings']]
    nums = get_numericals(vals)
    # print("len of results: "+str(len(vals)))
    # print("len of nums: "+str(len(nums)))
    return nums


def get_dist(points, num_of_bins, prob=False):
    """
    :param points:
    :param num_of_bins:
    :param prob: whether to have the counts or the probability of items
    :return:
    """
    if len(points) < 1:
        return [], []

    # print("num of points: "+str(len(points)))
    tot = len(points) * 1.0
    counts = [0] * num_of_bins
    labels = []
    points = sorted(points)
    # points.sort()
    min_val = min(points)
    max_val = max(points)
    bucket_size = (max_val - min_val)/num_of_bins
    for split_id in range(num_of_bins):
        upper_bound = (split_id+1)*bucket_size + min_val
        first_num_str = human_format(split_id*bucket_size + min_val)
        second_num_str = human_format(upper_bound)
        labels.append("%s - %s" % (first_num_str, second_num_str))
        # labels.append("%.2f-%.2f" % (round(split_id*bucket_size + min_val, 2), round(upper_bound, 2)))
        while(len(points)>0 and points[0] < upper_bound):
            pt = points[0]
            counts[split_id] += 1
            points.remove(pt)
        if prob:
            counts[split_id] = counts[split_id] / tot
    return counts, labels


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


# source: https://stackoverflow.com/questions/579310/formatting-long-numbers-as-strings-in-python/45846841
def human_format(number):
    units = ['', 'K', 'M', 'G', 'T', 'P']
    k = 1000.0
    # print("\n\n\n*****************\nnumber: ")
    # print(number)
    try:
        if number == 0:
            magnitude = 0
        else:
            magnitude = int(math.floor(math.log(number, k)))
        return '%.2f%s' % (number / k**magnitude, units[magnitude])
    except:
        return '%.2f' % number


if __name__ == "__main__":
    class_uri = "http://dbpedia.org/ontology/Country"
    property_uri1 = "http://dbpedia.org/property/pop"
    property_uri2 = "http://dbpedia.org/property/statArea"
    # endpoint = 'http://dbpedia.org/sparql'
    endpoint = None
    compare(class_uri, property_uri1, property_uri2, data=[1, 2, 3, 4, 5, 6, 7], data_label="data", num_of_bins=0,
            endpoint=endpoint)
