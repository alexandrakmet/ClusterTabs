import requests
from bs4 import BeautifulSoup
import re

import time
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.decomposition import LatentDirichletAllocation
from summa import keywords
from nltk.tokenize import sent_tokenize, word_tokenize
import nltk

from collections import Counter
from itertools import combinations

nltk.download('punkt')
nltk.download('wordnet')
nltk.download('stopwords')

from nltk.stem import WordNetLemmatizer
from nltk.corpus import stopwords


def lemmatize_text(text):
    lemmatizer = WordNetLemmatizer()
    lemmatized_text = ' '.join([lemmatizer.lemmatize(word) for word in text.split()])
    return lemmatized_text


def remove_stopwords(text):
    stop_words = set(stopwords.words('english'))
    filtered_text = ' '.join([word for word in text.split() if word.lower() not in stop_words])
    return filtered_text


def get_tfidf_features(documents, num_features, ngram_range=(1, 1)):
    vectorizer = TfidfVectorizer(max_features=num_features, ngram_range=ngram_range)
    tfidf_matrix = vectorizer.fit_transform(documents)
    feature_names = vectorizer.get_feature_names_out()
    return tfidf_matrix, feature_names


def get_lda_features(documents, num_topics, num_features, ngram_range=(1, 1)):
    vectorizer = TfidfVectorizer(max_features=num_features, ngram_range=ngram_range)
    tfidf_matrix = vectorizer.fit_transform(documents)

    lda = LatentDirichletAllocation(n_components=num_topics)
    lda.fit(tfidf_matrix)

    feature_names = vectorizer.get_feature_names_out()
    lda_matrix = lda.components_
    return lda_matrix, feature_names


def get_textrank_features(text, num_keywords, ngram_range=(1, 1)):
    sentences = sent_tokenize(text)
    joined_text = ' '.join(sentences)
    tokens = word_tokenize(joined_text)

    ngrams = []
    for n in range(ngram_range[0], ngram_range[1] + 1):
        ngrams.extend(list(combinations(tokens, n)))
    ngram_counter = Counter(ngrams)
    top_ngrams = ngram_counter.most_common(num_keywords)
    keywords_list = [' '.join(ngram) for ngram, count in top_ngrams]
    return keywords_list


def get_textrank(text):
    soup = BeautifulSoup(text, 'html.parser')
    text = soup.get_text()

    text = text.lower()
    text = re.sub(r'\d+', '', text)
    text = re.sub(r'[\n]|\\', '', text)
    text = re.sub(r'[^\w\s]', '', text)
    text = ' '.join([word for word in text.split() if word not in stopwords.words('english')])

    text = ' '.join(text)
    lemmatized_text = lemmatize_text(text)
    filtered_text = remove_stopwords(lemmatized_text)
    documents = filtered_text
    textrank_keywords = get_textrank_features(documents, num_keywords=5, ngram_range=(1, 2))
    return text


def metrics(texts):
    ngram_range = (1, 2)
    for i, tt in enumerate(texts):
        text = ' '.join(tt)
        lemmatized_text = lemmatize_text(text)
        filtered_text = remove_stopwords(lemmatized_text)
        documents = [filtered_text]
        if len(documents) > 0:
            start_time = time.time()
            tfidf_matrix, tfidf_feature_names = get_tfidf_features(documents, num_features=5, ngram_range=ngram_range)
            tfidf_time = time.time() - start_time

            start_time = time.time()
            lda_matrix, lda_feature_names = get_lda_features(documents, num_topics=2, num_features=5,
                                                             ngram_range=ngram_range)
            lda_time = time.time() - start_time

            start_time = time.time()
            text = ' '.join(documents)
            textrank_keywords = get_textrank_features(text, num_keywords=5, ngram_range=ngram_range)
            textrank_time = time.time() - start_time

            true_keywords = ['python', 'data science', 'machine learning', 'skills', 'algorithms']

            tfidf_precision = len(set(tfidf_feature_names).intersection(true_keywords)) / len(tfidf_feature_names)
            tfidf_recall = len(set(tfidf_feature_names).intersection(true_keywords)) / len(true_keywords)

            lda_topic_keywords = [lda_feature_names[np.argsort(topic)[-1]] for topic in lda_matrix]
            lda_precision = len(set(lda_topic_keywords).intersection(true_keywords)) / len(lda_topic_keywords)
            lda_recall = len(set(lda_topic_keywords).intersection(true_keywords)) / len(true_keywords)

            textrank_precision = len(set(textrank_keywords).intersection(true_keywords)) / len(textrank_keywords)
            textrank_recall = len(set(textrank_keywords).intersection(true_keywords)) / len(true_keywords)

            print("TF-IDF Features:")
            print(tfidf_feature_names)
            print("TF-IDF Precision:", tfidf_precision)
            print("TF-IDF Recall:", tfidf_recall)
            print("Time taken:", tfidf_time, "seconds")
            print()

            print("LDA Features:")
            print(lda_topic_keywords)
            print("LDA Precision:", lda_precision)
            print("LDA Recall:", lda_recall)
            print("Time taken:", lda_time, "seconds")
            print()

            print("TextRank Features:")
            print(textrank_keywords)
            print("TextRank Precision:", textrank_precision)
            print("TextRank Recall:", textrank_recall)
            print("Time taken:", textrank_time, "seconds")
