import os
from unittest import TestCase

from src.synonymList import SynonymList

from tests.tests.TempFileManager import TempFileManager


class TestSynonymList(TestCase):
    PATH = ".." + os.path.sep + "resources" + os.path.sep + "syn_files" + os.path.sep

    NOT_FOUND_SYN = "not_found_syn.csv"
    IMPROPER_FORMATS = ["empty_syn.csv",
                        "no_freqs.csv",
                        "improper_columns.csv",
                        "improper_columns2.csv"
                        ]
    PROPER_FORMATS = ["syn.csv",
                      "basic_syn_1.csv",
                      "basic_syn_2.csv"]

    def pathname(self, name):
        return self.PATH + name

    def setUp(self):
        # create temporary files to test io
        self.files = []
        for file in self.PROPER_FORMATS:
            self.files.append(TempFileManager(self.PATH, file))

    def tearDown(self):
        for file in self.files:
            file.close()

    def test_init_not_found(self):
        syn_list = SynonymList.__new__(SynonymList)
        self.assertRaises(FileNotFoundError, SynonymList.__init__, syn_list, self.pathname(self.NOT_FOUND_SYN))

    def test_improper_format(self):
        for file in self.IMPROPER_FORMATS:
            syn_list = SynonymList.__new__(SynonymList)
            self.assertRaises(ValueError,
                              SynonymList.__init__,
                              syn_list,
                              self.pathname(file))

    def test_proper_format(self):
        for file in self.PROPER_FORMATS:
            try:
                syn_list = SynonymList(self.pathname(file))
                self.assertFalse(syn_list.changed)
            except ValueError:
                self.fail("Proper file, raised formatting error!")

    def test_append(self):
        file = self.pathname(self.PROPER_FORMATS[0])
        syn_list = SynonymList(file)
        syn_list.append("test")
        syn = syn_list[len(syn_list)-1]
        self.assertIn(syn, syn_list)
        self.assertTrue(syn_list.changed)

    def test_add_syn(self):
        file = self.pathname(self.PROPER_FORMATS[0])
        syn_list = SynonymList(file)
        syn_list.append("test")
        syn = syn_list[len(syn_list)-1]
        syn_list.add_syn("test", "testytest")
        self.assertIn("testytest", syn.syns)

    def test_store_synonyms(self):
        for file in self.files:
            syn_list = SynonymList(file.path)
            syn_list.store_synonyms()
            syn_list = SynonymList(file.path)
            syn_og = SynonymList(file.og_path)
            self.assertListEqual(syn_list, syn_og)

    def test_store_changed_syns(self):
        for file in self.files:
            syn_list = SynonymList(file.path)
            syn_list.append("test")
            syn_list.add_syn("test", "testing")
            syn_list.store_synonyms()
            syn_list = SynonymList(file.path)
            syn_og = SynonymList(file.og_path)
            syn_og.append("test")
            syn_og.add_syn("test", "testing")
            self.assertListEqual(syn_list, syn_og)


