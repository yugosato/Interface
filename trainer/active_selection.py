# -*- coding: utf-8 -*-

import numpy as np
from libact.query_strategies import UncertaintySampling
from libact.base.dataset import Dataset
from scipy.spatial.distance import  cosine
import os
from mymodel import Chainer2Sklearn


home_dir = "/home/yugo/workspace/Interface/trainer"


class ActiveSelection(object):

    def __init__(self):
        pass

    def run_selection(self):
        self.load_classifier()
        _, trn_ds = self.split_train_test()

        if len(trn_ds) > 0:
            uncertain_index = self.getUncertaintyIndex(trn_ds, "sm", self.clf_)
        else:
            uncertain_index = self.getRandomIndex()
        random_index = self.getRandomIndex()

        self.write(os.path.join(home_dir, "result/uncertain_index.txt"), uncertain_index)
        self.write(os.path.join(home_dir, "result/random_index.txt"), random_index)

    def run_estimate_class(self):
        print "[Trainer-Selection] Start Estimating positive/negative."
        proba = self.clf_.predict_proba(self.train_.features_)
        positive_index = self.sort_positive(proba)
        negative_index = self.sort_negative(proba)
        self.write(os.path.join(home_dir, "result/positive_index.txt"), positive_index)
        self.write(os.path.join(home_dir, "result/negative_index.txt"), negative_index)

    def load_classifier(self):
        self.clf_ = Chainer2Sklearn(self.model_)

    def labeled_index(self):
        positives = self.train_.positives_
        negatives = self.train_.negatives_
        self.labeled_index_ = np.hstack((positives, negatives))
        self.len_labeled_index_ = len(self.labeled_index_)

    def unlabeled_index(self):
        self.unlabeled_index_ = []
        for index in self.train_.neighbors_:
            if not index in self.labeled_index_:
                self.unlabeled_index_.append(index)
        self.len_unlabeled_index_ = len(self.unlabeled_index_)

    def labeled_sample(self):
        pairs = self.train_.base_
        X = []
        y = []
        for pair in pairs:
            X.append(pair[0])
            y.append(pair[1])
        return X, y

    def unlabeled_sample(self):
        X = []
        y = [None] * len(self.unlabeled_index_)
        for index in self.unlabeled_index_:
            X.append(self.train_.features_[index])
        return X, y

    def split_train_test(self):
        self.labeled_index()
        self.unlabeled_index()
        X_test, y_test = self.labeled_sample()
        X_train, y_train = self.unlabeled_sample()
        tst_ds = Dataset(X_test, y_test)
        trn_ds = Dataset(X_train, y_train)
        return  tst_ds, trn_ds

    "Random selection for compasion."
    def getRandomIndex(self):
        print "[Trainer-Selection] Get random sampling index."
        database_size = len(self.train_.features_)
        neighbors_size = len(self.train_.neighbors_)
        database_index = [i for i in xrange(database_size)]
        return np.random.choice(database_index, neighbors_size, replace = False)

    "Traditional active learning method."
    def getUncertaintyIndex(self, trn_ds, method, clf):
        print "[Trainer-Selection] Get uncertainty sampling index."
        qs = UncertaintySampling(trn_ds, method=method, model=clf)
        _, score = qs.make_query(return_score=True)
        score_sorted = sorted(score, key=lambda x:x[1], reverse=True)
        result = []
        for index in score_sorted:
            result.append(self.unlabeled_index_[index[0]])
        return result

    "Active distance used in the CueFlik (Fogary+,2008)."
    def getCueFlikIndex(self):
        print "[Trainer-Selection] Get CueFlik sampling index."
        features = self.new_features_

        result = []
        for index in self.unlabeled_index_:
            mindist_p = 1.0
            for index_positive in self.train_.positives_:
                distance = cosine(features[index], features[index_positive])
                if distance < mindist_p:
                    mindist_p = distance

            mindist_n = 1.0
            for index_negative in self.train_.negatives_:
                distance = cosine(features[index], features[index_negative])
                if distance < mindist_p:
                    mindist_n = distance

            uncertain = abs(mindist_p - mindist_n)
            active_distance = (mindist_p + mindist_n) * uncertain
            result.append(active_distance)
        return np.argsort(result)

    @staticmethod
    def sort_positive(proba):
        positive_proba = []
        for prob in proba:
            positive_proba.append(prob[1])
        return np.argsort(positive_proba)[::-1]

    @staticmethod
    def sort_negative(proba):
        negative_proba = []
        for prob in proba:
            negative_proba.append(prob[0])
        return np.argsort(negative_proba)[::-1]

    @staticmethod
    def write(filename, index):
        if not os.path.exists(os.path.join(home_dir, "result")):
            os.makedirs(os.path.join(home_dir, "result"))
        np.savetxt(filename, np.array(index), fmt="%.0f")
        print "[Trainer-Selection] --> {}".format(filename)
