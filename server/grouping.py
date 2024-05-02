import nltk
from nltk.tokenize import RegexpTokenizer
from nltk.stem import WordNetLemmatizer, PorterStemmer
from nltk.corpus import stopwords
import string
import re
import nltk
from gensim.models import LdaModel
from gensim.corpora.dictionary import Dictionary
from sklearn.feature_extraction.text import TfidfVectorizer
import summa.keywords as textrank_keywords

lemmatizer = WordNetLemmatizer()
stemmer = PorterStemmer()

from nltk.corpus import stopwords

nltk.download('stopwords')
nltk.download('wordnet')
stop_words = stopwords.words('english')
stop_words.extend(['button', 'submit', 'menu', 'login'])


def preprocess(sentence):
    sentence = str(sentence)
    sentence = sentence.lower()
    sentence = sentence.replace('{html}', "")
    cleanr = re.compile('<.*?>')
    cleantext = re.sub(cleanr, ' ', sentence)
    rem_url = re.sub(r'http\S+', '', cleantext)
    rem_url = re.sub(r'\n', ' ', rem_url)
    rem_num = re.sub('[0-9]+', '', rem_url)
    rem_punct = rem_num.translate(str.maketrans('', '', string.punctuation))
    rem_lb = rem_punct.replace('\n', ' ').replace('\r', ' ')
    tokenizer = RegexpTokenizer(r'\w+')
    tokens = tokenizer.tokenize(rem_lb)
    filtered_words = [w for w in tokens if len(w) > 2 if not w in stop_words]
    lemmatized_words = [lemmatizer.lemmatize(w) for w in filtered_words]
    # stemmed_words = [stemmer.stem(w) for w in lemmatized_words]
    return " ".join(lemmatized_words)


def tagify(data, threshold=0.2, txt=''):
    styles = {"headers": [], "styledTexts": []}
    if 'headers' in data:
        headersToStr = '. '.join([str(elem) for elem in data['headers']])
        styles["headers"] = headersToStr
    if 'styledTexts' in data:
        headersToStr = '. '.join([str(elem) for elem in data['styledTexts']])
        styles["styledTexts"] = headersToStr
    if len(txt) == 0:
        txt = [preprocess(data['texts'])]

    # Preprocess documents
    processed_docs = [doc.lower().split() for doc in txt]
    doc_strings = [' '.join(doc) for doc in processed_docs]

    # TD-IDF
    tfidf_vectorizer = TfidfVectorizer()
    tfidf_matrix = tfidf_vectorizer.fit_transform(doc_strings)
    tfidf_keywords = tfidf_vectorizer.get_feature_names_out()

    filtered_tfidf_keywords = [keyword for keyword, score in zip(tfidf_keywords, tfidf_matrix.toarray()[0]) if
                               score > threshold]

    # LDA
    dictionary = Dictionary(processed_docs)
    corpus = [dictionary.doc2bow(doc) for doc in processed_docs]
    lda_model = LdaModel(corpus=corpus, id2word=dictionary, num_topics=1)
    lda_keywords = lda_model.show_topic(0)
    keywords = [keyword for keyword, _ in lda_keywords]

    alls = set(filtered_tfidf_keywords + keywords)  # + textrank_keywords_)

    multipliers = {
        keyword: 1.5 if keyword in styles['headers'] else 1.2 if keyword in styles['styledTexts'] else 1.0
        for keyword in list(alls)
    }
    # TD-IDF
    tfidf_scores = {keyword: score for keyword, score in zip(tfidf_keywords, tfidf_matrix.toarray()[0])}
    tfidf_scores = [(keyword, score * multipliers[keyword]) for keyword, score in tfidf_scores.items() if
                    keyword in alls]

    # LDA
    lda_scores = {keyword: score for keyword, score in lda_model.show_topic(0)}
    lda_scores = [(keyword, score * multipliers[keyword]) for keyword, score in lda_scores.items() if keyword in alls]

    sorted_list = sorted(list(tfidf_scores + lda_scores), key=lambda x: x[1])

    for item in sorted_list:
        if item[1] > threshold:
            # print(item[0])
            continue
    return {keyword: score for keyword, score in sorted_list if score > threshold}
