import math
from SPARQLWrapper import SPARQLWrapper, JSON
import six
import random
import os
import string
from flask import Flask, render_template, request, send_from_directory, session
from pcake.pcake import human_format, remove_outliers, get_dist, get_points, get_numericals

app = Flask(__name__)
app.secret_key = ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))
default_endpoint = 'http://dbpedia.org/sparql'

if 'endpoint' in os.environ:
    default_endpoint = os.environ['endpoint']


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
        points1 = get_points(endpoint=endpoint, class_uri=class_uri, property_uri=property_uri1)
        # points1 = get_points(class_uri=class_uri, property_uri=property_uri1)
        points1 = remove_outliers(points1)
        points2 = get_points(endpoint=endpoint, class_uri=class_uri, property_uri=property_uri2)
        # points2 = get_points(class_uri=class_uri, property_uri=property_uri2)
        print("points2: "+str(len(points2)))
        points2 = remove_outliers(points2)
        print("points2 - after outlier removal: "+str(len(points2)))
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
        session['points1'] = points1
        session['points2'] = points2
        session['points3'] = []
        label1 = class_uri.split('/')[-1].split('#')[-1] + " - " + property_uri1.split('/')[-1].split('#')[-1]
        label2 = class_uri.split('/')[-1].split('#')[-1] + " - " + property_uri2.split('/')[-1].split('#')[-1]
        if 'data' in request.args:
            data = request.args['data'].strip()
            data = data.split('\n')
            data = [d.strip() for d in data]
            data = get_numericals(data)
            print("numericals: "+str(data))
            num_of_points3 = len(data)
            points_counts3, _ = get_dist(data, num_of_bins=num_of_bins, prob=prob)
            session['points3'] = data
            label3 = "data"
            # print("data to be sent: "+str(data))
            print("labels: ")
            print(labels)
            print("label1: ")
            print(label1)
            print("points1: ")
            print(points1)
            return render_template('compare_view.html', points=points_counts1, labels=labels, label=label1,
                                   label2=label2,
                                   class_uri=class_uri, property_uri1=property_uri1, property_uri2=property_uri2,
                                   splits=num_of_bins, num_of_points2=num_of_points2, num_of_points1=num_of_points1,
                                   points1=points_counts1, points2=points_counts2, endpoint=endpoint,
                                   label3=label3, num_of_points3=num_of_points3, points3=points_counts3, data=data
                                   )
        return render_template('compare_view.html', points=points_counts1, labels=labels, label=label1, label2=label2,
                           class_uri=class_uri, property_uri1=property_uri1, property_uri2=property_uri2,
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
        fname = fname.replace('http://', '').replace('https://', '').replace('/', '-')
        outf_path = os.path.join(fdir, fname)
        txt = "\n".join([str(p) for p in points])
        print("out path: <"+outf_path+">")
        f = open(outf_path, 'w')
        f.write(txt)
        f.close()
        return send_from_directory(directory=fdir, filename=fname, as_attachment=True)
    else:
        return "class and/or property are not passed"


if __name__ == '__main__':
    app.run(debug=True)



