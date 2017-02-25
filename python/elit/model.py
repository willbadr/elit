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
from abc import ABCMeta
from abc import abstractmethod
from typing import List
from typing import Dict
import numpy as np
__author__ = 'Jinho D. Choi'


class LabelMap:
    def __init__(self):
        self.index_map: Dict[str, int] = {}
        self.labels: List[str] = []

    def __len__(self):
        return len(self.labels)

    def __str__(self):
        return str(self.labels)

    def index(self, label: str) -> int:
        """
        :return: the index of the label.
        """
        return self.index_map.get(label, -1)

    def add(self, label: str) -> int:
        """
        :return: the index of the label.
          Add a label to this map if not exist already.
        """
        idx = self.index(label)
        if idx < 0:
            idx = len(self.labels)
            self.index_map[label] = idx
            self.labels.append(label)
        return idx


class NLPModel(metaclass=ABCMeta):
    def __init__(self):
        self.index_map: Dict[str, int] = {}
        self.labels: List[str] = []

    # ============================== Label ==============================

    def get_label_index(self, label: str) -> int:
        """
        :return: the index of the label.
        """
        return self.index_map.get(label, -1)

    def get_label(self, index: int) -> str:
        """
        :param index: the index of the label to be returned.
        :return: the index'th label.
        """
        return self.labels[index]

    def add_label(self, label: str) -> int:
        """
        :return: the index of the label.
          Add a label to this map if not exist already.
        """
        idx = self.index(label)
        if idx < 0:
            idx = len(self.labels)
            self.index_map[label] = idx
            self.labels.append(label)
        return idx

    # ============================== Predict ==============================

    @abstractmethod
    def predict(self, x: np.array) -> int:
        """
        :param x: the feature vector.
        :return: the ID of the best predicted label.
        """