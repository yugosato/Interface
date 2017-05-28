# -*- coding: utf-8 -*-

import chainer
import chainer.functions as F
import chainer.links as L
from chainer import Chain


class MyModel(Chain):
    def __init__(self):
        super(MyModel, self).__init__(
            fc1=L.Linear(None, 4096),
            fc2=L.Linear(None, 4096),
            fc3=L.Linear(None, 2)
        )
        self.train = True

        
    def __call__(self, x, t):
        h = F.dropout(F.relu(self.fc1(x)), train=self.train, ratio=0.5)
        h = F.dropout(F.relu(self.fc2(h)), train=self.train, ratio=0.5)
        h = self.fc3(h)

        loss = F.softmax_cross_entropy(h, t)
        chainer.report({'loss': loss, 'accuracy': F.accuracy(h, t)}, self)
        return loss