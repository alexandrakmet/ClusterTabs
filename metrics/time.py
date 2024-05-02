import time
from sklearn.datasets import fetch_20newsgroups
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.decomposition import LatentDirichletAllocation
import spacy
import numpy as np

# Завантаження даних
data = fetch_20newsgroups(subset='all')['data']
data = data[:100]  # Обмеження датасету для швидкості обробки

# Підготовка тексту
nlp = spacy.load('en_core_web_sm')
processed_docs = [' '.join([token.lemma_ for token in nlp(doc) if token.is_alpha and not token.is_stop]) for doc in data]

# Запуск TF-IDF
start_time = time.time()
tfidf_vectorizer = TfidfVectorizer(max_df=0.95, min_df=2)
tfidf_matrix = tfidf_vectorizer.fit_transform(processed_docs)
tfidf_time = time.time() - start_time

# Запуск LDA
start_time = time.time()
lda = LatentDirichletAllocation(n_components=5, random_state=0)
lda_matrix = lda.fit_transform(tfidf_matrix)
lda_time = time.time() - start_time

# Запуск TextRank
start_time = time.time()
def text_rank_keywords(doc, nlp):
    doc_nlp = nlp(doc)
    graph = nx.Graph()
    for token in doc_nlp:
        if token.is_alpha and not token.is_stop:
            for neighbor in token.neighbors:
                if neighbor.is_alpha and not neighbor.is_stop:
                    graph.add_edge(token.text, neighbor.text)
    pagerank = nx.pagerank(graph)
    return sorted(pagerank, key=pagerank.get, reverse=True)[:10]

textrank_keywords = [text_rank_keywords(doc, nlp) for doc in data]
textrank_time = time.time() - start_time

# Виведення часу виконання для кожного методу
print(f"Час виконання TF-IDF: {tfidf_time:.2f} секунд")
print(f"Час виконання LDA: {lda_time:.2f} секунд")
print(f"Час виконання TextRank: {textrank_time:.2f} секунд")