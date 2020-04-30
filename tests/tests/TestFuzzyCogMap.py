import csv
import os
import random
from unittest import TestCase

from src.fuzzyCogMap import FuzzyCogMap
from src.synonymList import SynonymList
from tests.tests.SimpleUserQuery import SimpleUserQuery
from tests.tests.TempFileManager import TempFileManager


class TestFuzzyCogMap(TestCase):
    SYN_PATH = ".." + os.path.sep + "resources" + os.path.sep + "syn_files" + os.path.sep
    FCM_PATH = ".." + os.path.sep + "resources" + os.path.sep + "fcm_files" + os.path.sep
    SYN_FILE = "syn.csv"

    def setUp(self):
        self.syn_file = TempFileManager(self.SYN_PATH, self.SYN_FILE)

    def tearDown(self):
        self.syn_file.close()

    # creates an fcm with the given length, filename, using synonyms, and appends append
    # returns the anchors of the headers
    def create_random_fcm(self, synonyms: SynonymList, n: int, filename: str, append=None):
        if append is None:
            append = []
        head_inds = []
        for i in range(n):
            r = random.randrange(len(synonyms))
            while r in head_inds:
                r = random.randrange(len(synonyms))
            head_inds.append(r)

        headers = [""]
        anchors = [""]
        for i in head_inds:
            if len(synonyms[i].syns) == 0:
                headers.append(synonyms[i].anchor)
                anchors.append(synonyms[i].anchor)
            else:
                if len(synonyms[i].syns) == 1:
                    r = 0
                else:
                    r = random.randrange(len(synonyms[i].syns))
                headers.append(synonyms[i].syns[r])
                anchors.append(synonyms[i].anchor)

        headers += append
        self.fill_random_headers(headers, filename)

        return anchors

    # choose synonyms randomly, and positions randomly
    # dist is a list of conflicts, i.e how many overlapping
    # filename is a full path
    def create_conflicted_fcm(self, synonyms: SynonymList, dist: list, m: int, filename: str):
        head_inds = []
        headers = [""]
        # make a list containing the required number of unique indexes
        for i in range(m + len(dist)):
            r = random.randrange(len(synonyms))
            while r in head_inds:
                r = random.randrange(len(synonyms))
            head_inds.append(r)
            headers.append(synonyms[r].anchor)

        # now randomly pick an index to duplicate, and duplicate it as many times as dist tells us
        unique_length = len(head_inds)  # because we will append to headers and we don't want to pick the ones we append
        for i in dist:
            r = random.randrange(unique_length)
            unique = []
            for j in range(i):
                r2 = random.randrange(len(synonyms[r].syns))
                while r2 not in unique:
                    r2 = random.randrange(len(synonyms[r].syns))
                headers.append(synonyms[r].syns[r2])
                unique.append(r2)

        random.shuffle(headers)
        # at this point we should have a list with headers
        self.fill_random_headers(headers, filename)

    @staticmethod
    def fill_random_headers(headers: list, filename: str):
        with open(filename, 'w', encoding="utf-8-sig", newline='') as csv_file:
            writer = csv.writer(csv_file)
            writer.writerow(headers)

            row = []
            for i in range(1, len(headers)):
                row.append(headers[i])
                for j in range(len(headers) - 1):
                    row.append(random.random())

                writer.writerow(row)
                row.clear()

    def test_normal_fcm(self):
        for i in range(10, 100, 10):
            for j in range(20):
                filename = self.FCM_PATH + "normal_fcm_temp.csv"
                synonyms = SynonymList(self.syn_file.path)
                anchors = self.create_random_fcm(synonyms, 20, filename)
                fcm = FuzzyCogMap(filename, SimpleUserQuery(), synonyms, 0.86, 0.1, 0.86)
                fcm.get_codes()
                fcm.file.close()  # fcm leaves the file open until it is done storing its contents
                self.assertListEqual(list(fcm.anchors.values()), anchors)
                os.remove(filename)

    def test_new_synonym(self):
        for i in range(10, 100, 10):
            for j in range(20):
                filename = self.FCM_PATH + "normal_fcm_temp.csv"
                random_name = "asdlfkjsdfsdafalskjfasdf"
                synonyms = SynonymList(self.syn_file.path)
                anchors = self.create_random_fcm(synonyms, 20, filename, [random_name])
                r = random.randrange(len(synonyms))
                anchor = synonyms[r].anchor
                anchors.append(anchor)
                fcm = FuzzyCogMap(filename, SimpleUserQuery(gct_result=anchor, gct_exists=1), synonyms, 0.86, 0.1, 0.86)
                fcm.get_codes()
                self.assertListEqual(fcm.anchors.values(), anchors)
                self.assertTrue(synonyms.changed)
                self.assertTrue(random_name in synonyms[r].syns)
                os.remove(filename)

    def test_new_anchor(self):
        pass

    def test_combine(self):
        pass

    def test_remap(self):
        pass

    def test_split(self):
        pass
