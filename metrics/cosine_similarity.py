from sklearn.datasets import fetch_20newsgroups
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.decomposition import LatentDirichletAllocation
import spacy
import networkx as nx
import numpy as np

# Завантаження даних
data = fetch_20newsgroups(subset='all')['data']

# Підготовка тексту
nlp = spacy.load('en_core_web_sm')
processed_docs = [' '.join([token.lemma_ for token in nlp(doc) if token.is_alpha and not token.is_stop]) for doc in data]

# TF-IDF
tfidf_vectorizer = TfidfVectorizer(max_df=0.95, min_df=2)
tfidf_matrix = tfidf_vectorizer.fit_transform(processed_docs)
feature_names = tfidf_vectorizer.get_feature_names_out()
top_n = 10
tfidf_keywords_matrix = np.zeros_like(tfidf_matrix.toarray())
for i, row in enumerate(tfidf_matrix.toarray()):
    top_indices = np.argsort(row)[-top_n:]
    for idx in top_indices:
        tfidf_keywords_matrix[i][idx] = row[idx]

# LDA
lda = LatentDirichletAllocation(n_components=5, random_state=0)
lda_matrix = lda.fit_transform(tfidf_matrix)
top_n = 10
lda_keywords_matrix = np.zeros((len(data), len(feature_names)))
for topic_idx, topic in enumerate(lda.components_):
    for i in lda_matrix[:, topic_idx].argsort()[::-1]:
        top_features_ind = topic.argsort()[:-top_n - 1:-1]
        lda_keywords_matrix[i, top_features_ind] += lda_matrix[i, topic_idx]

# TextRank
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
textrank_matrix = tfidf_vectorizer.transform([' '.join(words) for words in textrank_keywords])

# Вимірювання косинусної подібності
cosine_similarities_tfidf_textrank = cosine_similarity(tfidf_keywords_matrix, textrank_matrix)
mean_cosine_similarity_tfidf_textrank = np.mean(cosine_similarities_tfidf_textrank)

print(f"Середня косинусна подібність між TF-IDF і TextRank: {mean_cosine_similarity_tfidf_textrank:.3f}")

cosine_similarities_lda_textrank = cosine_similarity(lda_keywords_matrix, textrank_matrix)
mean_cosine_similarity_lda_textrank = np.mean(cosine_similarities_lda_textrank)

print(f"Середня косинусна подібність між LDA і TextRank: {mean_cosine_similarity_lda_textrank:.3f}")

cosine_similarities_lda_tfidf = cosine_similarity(lda_keywords_matrix, tfidf_keywords_matrix)
mean_cosine_similarity_lda_tfidf = np.mean(cosine_similarities_lda_tfidf)

print(f"Середня косинусна подібність між LDA і TF-IDF: {mean_cosine_similarity_lda_tfidf:.3f}")
