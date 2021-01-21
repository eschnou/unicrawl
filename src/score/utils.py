# -*- coding: utf-8 -*-
from typing import List, Dict

from unidecode import unidecode
from sklearn.feature_extraction.text import TfidfVectorizer
# spaCy is a free, open-source library for advanced Natural Language Processing (NLP) in Python.
import spacy
from functools import partial

from collections import Counter
import re

import logging
logger = logging.Logger(name='Utils Logger')


def load_models(corpus: List[str], language: str):
    """
    Build TF-IDF vectorize and features from a given corpus.

    :param corpus: List of strings from which we want to extract features.
    :param language: Language of the corpus.
    :return:
    TODO complete
    """

    # We replace the default tokenizer from sklearn by one using spaCy # TODO: why are we doing that?
    def tokenize(nlp, text):
        # Cut the text into individual tokens removing stop words, punctuations, numbers, symbols and spaces
        return [unidecode(w.text.lower()) for w in nlp(text)
                if w.pos_ not in ["PUNCT", "SYM", "SPACE"] and w.is_stop is False]
    # Load spacy language model
    nlp = spacy.load(language)
    # Allows to send the nlp argument in the callback function passed to TfidfVectorizer
    t = partial(tokenize, nlp)

    # Create and train a vectorizer with a spacy tokenizer, with features
    # being word n-grams (and not letter n-grams)
    logger.info("Training vectorizer")
    vectorizer = TfidfVectorizer(tokenizer=t, analyzer="word", ngram_range=(1, 3))
    vectorizer.fit(corpus)
    # pickle.dump(vectorizer, open(cfg.vectorizer.format(language), "wb"))
    features = vectorizer.get_feature_names()
    logger.info("Vectorizer trained")

    return vectorizer, features

def compute_score(text,pattern_mapping):
    #TODO : insert language detection
    language="fr"
    for p in pattern_mapping[language]:
        if re.search(p,text) is not None: return 1
    return 0


def compute_climate_score(ngram_score_dict: Dict[str, float], pattern) -> (float, Counter):
    """
    # TODO: complete

    :param ngram_score_dict: Dictionary associating ngrams to a score.
    :param pattern:
    :return:
    """
    matching = Counter()
    total_score = 0
    for ngram, score in ngram_score_dict.items():
        if re.match(pattern, ngram) is not None:
            total_score += (len(ngram.split(" ")) * score)
            matching[ngram] += 1
    return total_score, matching


def compute_shift_score(ngram_score_dict: Dict[str, float], pattern_weights_dict: Dict[str, float]) -> (float, Counter):
    """
    Computes the Shift score.

    # TODO: complete

    :param ngram_score_dict: Dictionary associating ngrams to a score.
    :param pattern_weights_dict: Dictionary associating patterns to weights.
    :return:
    - float giving the score associated to the input ngrams
    - dictionary counting the number of times ngrams have been matched
    """
    total_score = 0.0
    matching = Counter()
    # Compare each ngram to shift score patterns and increase the total score each time there is a match
    for ngram, score in ngram_score_dict.items():
        for pattern, weight in pattern_weights_dict.items():
            if re.match(pattern, ngram) is not None:
                # TODO: is this computation documented somewhere? where does it come from?
                total_score += (len(ngram.split(" ")) * score) ** weight
                matching[ngram] += 1
    return total_score, matching


def compute_sdg_scores(ngram_score_dict: Dict[str, float], patterns_dict: Dict[str, List[str]]):
    """
    Compute the SDG (Sustainable Development Goals) scores.

    :param ngram_score_dict: Dictionary associating ngrams to a score.
    :param patterns_dict: Dictionary associating a list of patterns to each SDG.
    :return:
    """
    scores = {}
    for sdg, patterns in patterns_dict.items():
        if sum([re.match(pattern, ngram) is not None for ngram, score in
                ngram_score_dict.items() for pattern in patterns]) > 2:
            scores[sdg] = 1
        else:
            scores[sdg] = 0
    return scores
