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
import re
from typing import Union
from elit.structure import *

__author__ = 'Jinho D. Choi'

_TAB      = re.compile('\t')
_FEATS    = re.compile('\\|')
_FEATS_KV = re.compile(DELIM_FEAT_KV)
_ARC      = re.compile(DELIM_ARC)
_ARC_KV   = re.compile(DELIM_ARC_KV)


class TSVReader:
    """
    :param word_index: the column index of word forms.
    :param lemma_index: the column index of lemma.
    :param pos_index: the column index of part-of-speech tags.
    :param feats_index: the column index of extra features.
    :param head_index: the column index of primary head IDs.
    :param deprel_index: the column index of primary dependency labels.
    :param sheads_index: the column index of secondary dependency heads.
    :param nament_index: the column index of of named entity tags.
    :param filename: the nament of a TSV file.
    """
    def __init__(self, word_index: int=-1, lemma_index: int=-1, pos_index: int=-1, feats_index: int=-1,
                 head_index: int=-1, deprel_index: int=-1, sheads_index: int=-1, nament_index: int=-1,
                 filename: str=None):
        self.word_index: int   = word_index
        self.lemma_index: int  = lemma_index
        self.pos_index: int    = pos_index
        self.feats_index: int  = feats_index
        self.head_index: int   = head_index
        self.deprel_index: int = deprel_index
        self.sheads_index: int = sheads_index
        self.nament_index: int = nament_index

        if filename:
            self.fin = self.open(filename)

    def __next__(self):
        graph = self.next()
        if graph: return graph
        else: raise StopIteration

    def __iter__(self):
        return self

    def open(self, filename):
        """
        :param filename: the nament of a TSV file.
        :type  filename: str
        """
        self.fin = open(filename)
        return self.fin

    def close(self):
        self.fin.close()

    def next(self):
        tsv = []

        for line in self.fin:
            line = line.strip()
            if line:  tsv.append(_TAB.split(line))
            elif tsv: break

        return self.tsv_to_graph(tsv) if tsv else None

    def next_all(self):
        return [graph for graph in self]

    def tsv_to_graph(self, tsv: List[List[str]]):
        """
        :param tsv: each row represents a token, each column represents a field.
        """
        def get_field(row: List[str], index: int) -> str:
            return ROOT_TAG if row is None else row[index] if index >= 0 else None

        def get_feats(row: List[str]) -> Union[Dict[str, str], None]:
            if self.feats_index >= 0:
                f = row[self.feats_index]
                if f == BLANK:
                    return None
                return {feat[0]: feat[1] for feat in map(_FEATS_KV.split, _FEATS.split(f))}
            return None

        def init_node(i: int) -> NLPNode:
            row = tsv[i]
            node: NLPNode = NLPNode()
            node.node_id = i + 1
            node.word    = get_field(row, self.word_index)
            node.lemma   = get_field(row, self.lemma_index)
            node.pos     = get_field(row, self.pos_index)
            node.nament  = get_field(row, self.nament_index)
            node.feats   = get_feats(row) if row else {}
            return node

        g = NLPGraph([init_node(i) for i in range(len(tsv))])

        if self.head_index >= 0:
            for i, n in enumerate(g):
                t = tsv[i]
                n.set_parent(g.nodes[int(t[self.head_index])], t[self.deprel_index])

                if self.sheads_index >= 0 and t[self.sheads_index] != BLANK:
                    for arc in map(_ARC_KV.split, _ARC.split(t[self.sheads_index])):
                        n.add_secondary_parent(g.nodes[int(arc[0])], arc[1])

        return g

reader = TSVReader(word_index=1, lemma_index=2, pos_index=3, feats_index=4, head_index=5, deprel_index=6, sheads_index=7, nament_index=8)
reader.open('/Users/jdchoi/Documents/Software/elit/resources/sample/sample.tsv')

for graph in reader:
    print(str(graph))