from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import KMeans
from sklearn.cluster import DBSCAN
from sklearn.cluster import OPTICS

import numpy as np


def kmeans(documents, k):
    clusters = {}
    vectorizer = TfidfVectorizer()
    tfidf_matrix = vectorizer.fit_transform(documents)

    kmeans = KMeans(n_clusters=k, random_state=42)
    kmeans.fit(tfidf_matrix)

    # Get the cluster labels for each document
    cluster_labels = kmeans.labels_

    # Assign each document to its corresponding cluster
    for i, label in enumerate(cluster_labels):
        if label not in clusters:
            clusters[label] = {"keywords": [], "docs_n": []}
        clusters[label]["docs_n"].append(i)

    # Get keywords for each cluster
    vectorizer = TfidfVectorizer()
    tfidf_matrix = vectorizer.fit_transform(documents)
    feature_names = vectorizer.get_feature_names_out()
    res = []
    for cluster, cluster_data in clusters.items():
        cluster_docs = [documents[i] for i in cluster_data["docs_n"]]
        tfidf_scores = tfidf_matrix[cluster_data["docs_n"], :]
        sorted_indices = np.argsort(-tfidf_scores.sum(axis=0))
        top_keywords = [feature_names[idx] for idx in sorted_indices[:, 0][:5]]
        cluster_data["keywords"] = top_keywords[0].tolist()[0]
        res.append(cluster_data)
    return res


def dbscan(documents):
    clusters = {}
    vectorizer = TfidfVectorizer()
    tfidf_matrix = vectorizer.fit_transform(documents)

    db = DBSCAN()
    db.fit(tfidf_matrix)

    # Get the cluster labels for each document
    cluster_labels = db.labels_

    # Assign each document to its corresponding cluster
    for i, label in enumerate(cluster_labels):
        if label not in clusters:
            clusters[label] = {"keywords": [], "docs_n": []}
        clusters[label]["docs_n"].append(i)

    # Get keywords for each cluster
    vectorizer = TfidfVectorizer()
    tfidf_matrix = vectorizer.fit_transform(documents)
    feature_names = vectorizer.get_feature_names_out()
    res = []
    for cluster, cluster_data in clusters.items():
        cluster_docs = [documents[i] for i in cluster_data["docs_n"]]
        tfidf_scores = tfidf_matrix[cluster_data["docs_n"], :]
        sorted_indices = np.argsort(-tfidf_scores.sum(axis=0))
        top_keywords = [feature_names[idx] for idx in sorted_indices[:, 0][:5]]
        cluster_data["keywords"] = top_keywords[0].tolist()[0]
        res.append(cluster_data)
    return res


def optics(documents):
    clusters = {}
    vectorizer = TfidfVectorizer()
    tfidf_matrix = vectorizer.fit_transform(documents)

    db = OPTICS(min_cluster_size=2)
    db.fit(tfidf_matrix.todense())

    # Get the cluster labels for each document
    cluster_labels = db.labels_
    labels = db.labels_
    n_clusters_ = len(set(labels)) - (1 if -1 in labels else 0)
    n_noise_ = list(labels).count(-1)
    print(labels)
    print('Estimated number of clusters: %d' % n_clusters_)
    print('Estimated number of noise points: %d' % n_noise_)

    # Assign each document to its corresponding cluster
    for i, label in enumerate(cluster_labels):
        if label not in clusters:
            clusters[label] = {"keywords": [], "docs_n": []}
        clusters[label]["docs_n"].append(i)

    # Get keywords for each cluster
    vectorizer = TfidfVectorizer()
    tfidf_matrix = vectorizer.fit_transform(documents)
    feature_names = vectorizer.get_feature_names_out()
    res = []
    for cluster, cluster_data in clusters.items():
        cluster_docs = [documents[i] for i in cluster_data["docs_n"]]
        tfidf_scores = tfidf_matrix[cluster_data["docs_n"], :]
        sorted_indices = np.argsort(-tfidf_scores.sum(axis=0))
        top_keywords = [feature_names[idx] for idx in sorted_indices[:, 0][:5]]
        cluster_data["keywords"] = top_keywords[0].tolist()[0]
        res.append(cluster_data)
    return res
