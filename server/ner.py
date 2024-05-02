import spacy
import re
from grouping import *


def create_tags(text):
    # Load the spaCy English language model
    nlp = spacy.load("en_core_web_sm")
    # Process the text
    # Extract tags by topics
    # topics = []
    # text = text.replace("\n", " ")
    # text = re.sub('[^A-Za-z0-9]+', ' ', text)
    # text = text.lower()

    # # Remove punctuations using spaCy
    doc = nlp(text)
    # text = ' '.join(token.text for token in doc if not token.is_punct)
    doc = nlp(' '.join(token.text for token in doc if not token.is_punct))

    # # Remove stopwords using spaCy
    # doc = nlp(text)
    # text = ' '.join(token.text for token in doc if not token.is_stop)
    doc = nlp(' '.join(token.text for token in doc if not token.is_stop))
    # for token in doc:
    #     if token.pos_ == "NOUN" or token.pos_ == "PROPN":
    #         topics.append(token.text)
    # topics=topics[:5]
    # Extract named entities
    ner = {}
    for ent in doc.ents:
        if ent.label_ in ['CARDINAL', 'ORDINAL']:
            continue
        if ent.label_ == 'DATE' and not re.search(r"(?!\d)|(\d{1,4})", ent.text):
            continue
        if ent.label_ not in ner:
            ner[ent.label_] = []
        if ent.text not in ner[ent.label_]:
            ner[ent.label_].append(ent.text)
    # Prepare the result in the desired format
    ner_tags = []

    for label, entities in ner.items():
        ner_tags.append({
            "title": label.capitalize(),
            "tags": entities
        })

    return ner_tags
