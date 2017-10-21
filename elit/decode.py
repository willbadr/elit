# ========================================================================
# Copyright 2017 Emory University
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
# ========================================================================
import abc
import json
import os

from elit.component.sentiment import TwitterSentimentAnalyzer, MovieSentimentAnalyzer
from elit.component.tokenizer import SpaceTokenizer, EnglishTokenizer
from elit.configure import *
from elit.lexicon import Word2Vec
from elit.string_util import is_right_bracket, is_final_mark

__author__ = 'Jinho D. Choi'


DOC_MAX_SIZE = 10485760
DOC_DELIM = '@#DOC$%'

KEY_TOKENS = 'tokens'
KEY_OFFSETS = 'offsets'
KEY_SENTIMENT = 'sentiment'


class Decoder:
    def decode(self, config, istream, ostream=None):
        """
        :param config: elit.configuration.Configuration
        :param istream: either StringIO or File
        :param ostream: either StringIO or File
        :return:
        """
        if ostream is not None: ostream.write('[')
        decode = self.decode_raw if config.input_format == INPUT_FORMAT_RAW else self.decode_line
        d = decode(config, istream, ostream)
        if ostream is not None: ostream.write(']')
        return d

    def decode_raw(self, config, istream, ostream=None):
        def decode():
            d = self.text_to_sentences(config, ''.join(lines))
            if ostream is None:
                documents.append(d)
            else:
                ostream.write(str(json.dumps(d)) + ',')

        documents = []
        offset = 0
        lines = []

        for line in istream:
            if line.strip() == DOC_DELIM:
                decode()
                offset = 0
                lines.clear()
            elif offset + len(line) <= DOC_MAX_SIZE:
                offset += len(line)
                lines.append(line)

        if lines: decode()
        return documents

    def decode_line(self, config, istream, ostream=None):
        def decode():
            if ostream is None:
                documents.append(sentences)
            else:
                ostream.write(str(json.dumps(sentences)) + ',')

        documents = []
        sentences = []
        offset = 0

        for line in istream:
            if line.strip() == DOC_DELIM:
                decode()
                offset = 0
                sentences = []
            elif offset + len(line) <= DOC_MAX_SIZE:
                d = self.text_to_sentences(config, line, offset)
                offset += len(line)
                sentences.extend(d)

        if sentences: decode()
        return documents

    ############################## CONVERSION ##############################

    @abc.abstractmethod
    def text_to_sentences(self, config, text, offset=0):
        return


class EnglishDecoder(Decoder):
    def __init__(self, resource_dir, config):
        # init tokenizer
        self.tokenizer_space = SpaceTokenizer()

        if config.tokenize == FLAG_TRUE:
            self.tokenizer = EnglishTokenizer(os.path.join(resource_dir, 'tokenizer'))

        # init sentiment analyzer: twitter
        if SENTIMENT_TWITTER in config.sentiment:
            emb_model = Word2Vec(os.path.join(resource_dir, 'embedding/w2v-400-twitter.gnsm'))
            model_file = os.path.join(resource_dir, 'sentiment/sentiment-semeval17-400-v2')
            self.sentiment_twit = TwitterSentimentAnalyzer(emb_model, model_file)

        # init sentiment analyzer: movie review
        if SENTIMENT_MOVIE in config.sentiment:
            emb_model = Word2Vec(os.path.join(resource_dir, 'embedding/w2v-400-amazon-review.gnsm'))
            model_file = os.path.join(resource_dir, 'sentiment/sentiment-sst-400-v2')
            self.sentiment_mov = MovieSentimentAnalyzer(emb_model, model_file)

    ############################## CONVERSION ##############################

    def text_to_sentences(self, config, text, offset=0):
        # tokenization
        tokenizer = self.tokenizer if config.tokenize == FLAG_TRUE else self.tokenizer_space
        tokens, offsets = tokenizer.tokenize(text, offset)

        # segmentation
        sentences = segment(tokens, offsets) if config.segment == FLAG_TRUE \
                    else [{KEY_TOKENS: tokens, KEY_OFFSETS: offsets}]

        # sentiment analysis
        if config.sentiment:
            self.sentiment_analyze(config, sentences)

        return sentences

    ############################## COMPONENTS ##############################

    def sentiment_analyze(self, config, sentences):
        def get_analyzer(s):
            if s.startswith(SENTIMENT_TWITTER):
                an = self.sentiment_twit
                key = SENTIMENT_TWITTER
            else:  # elif s.startswith(SENTIMENT_MOVIE):
                an = self.sentiment_mov
                key = SENTIMENT_MOVIE

            return an, s.endswith('att'), key

        for s in config.sentiment:
            analyzer, att, key = get_analyzer(s)
            sens = [d[KEY_TOKENS] for d in sentences]
            y, att = analyzer.decode(sens, att=att)

            for i, sentence in enumerate(sentences):
                sentence[KEY_SENTIMENT+'-'+key] = y[i].tolist()
                if att: sentence[KEY_SENTIMENT+'-'+key+'-att'] = att[i].tolist()


def segment(tokens, offsets):
    """
    :param tokens: the input tokens.
    :type tokens: list of str
    :return: the list of sentences, where each sentence is a dictionary containing tokens and offsets as keys.
        the sentence boundaries with respect to the tokens.
        e.g., tokens = ['1st', 'sentence', '.', '2nd', 'sentence', '?', '3rd', 'sentence', '!'] -> [0, 3, 6, 9],
              where each pair (0, 3), (3, 6), (6, 9) represents the corresponding sentence.
    """
    def sentence(begin, end):
        return {KEY_TOKENS: tokens[begin:end], KEY_OFFSETS: offsets[begin:end]}

    sentences = []
    begin = 0
    right_quote = True

    for i, token in enumerate(tokens):
        t = token[0]
        if t == '"': right_quote = not right_quote

        if begin == i:
            if sentences and (is_right_bracket(t) or t == u'\u201D' or t == '"' and right_quote):
                d = sentences[-1]
                d[KEY_TOKENS].append(token)
                d[KEY_OFFSETS].append(offsets[i])
                begin = i + 1
        elif all(is_final_mark(c) for c in token):
            sentences.append(sentence(begin, i+1))
            begin = i + 1

    if begin < len(tokens):
        sentences.append(sentence(begin, len(tokens)))

    return sentences