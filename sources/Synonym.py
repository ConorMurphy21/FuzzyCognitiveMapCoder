import re

from autocorrect import Speller


class Synonym:

    spell = Speller(lang="en")

    strip_prog = re.compile("[^a-z\'/]")

    def __init__(self, anchor):
        self.anchor = anchor
        self.syns = []

    def __str__(self):
        return str(self.anchor) + ": " + str(self.syns)

    def __eq__(self, o: object) -> bool:
        if type(self) != type(o):
            return False
        if self.anchor != o.anchor:
            return False
        return self.syns == o.syns

    def remove_synonym(self, syn):
        if syn in self.syns:
            self.syns.remove(syn)
        else:
            for s in self.syns:
                s_word = self.strip_word(s)
                auto_word = self.auto_word(s_word)
                fit = self.get_likeness(s, s_word, auto_word)
                if fit > 0.94:
                    self.syns.remove(s)
                    return

    def add_synonym(self, syn):
        self.syns.append(syn)

    def get_fit_once(self, word):
        s_word = self.strip_word(word)
        auto_word = self.auto_word(s_word)
        return self.get_fit(s_word, auto_word)

    # returns a number between 0 and 1 on how likely the synonym fits the anchor
    def get_fit(self, word, auto_word) -> float:
        weight = self.get_likeness(self.strip_word(self.anchor), word, auto_word)
        for syn in self.syns:
            if weight == 1:
                break
            temp = self.get_likeness(self.strip_word(syn), word, auto_word)
            if temp > weight:
                weight = temp
        return weight

    # for now this method is very arbitrary, but should do the job
    @staticmethod
    def get_likeness(anchor, word, auto_word) -> float:
        if word == anchor:
            return 1

        if word in anchor:
            return 0.85

        if auto_word == anchor:
            return 0.95

        if auto_word in anchor:
            return 0.8

        if anchor in word:
            return 0.75

        if anchor in auto_word:
            return 0.7

        return 0

    @staticmethod
    def strip_word(word) -> str:
        strip = Synonym.strip_prog.sub(" ", word.lower())
        strip = " ".join(strip.split())  # replace multiple whitespace with one space
        if strip == "":  # dumb ascii art stays separate
            strip = word
        return strip

    @staticmethod
    def auto_word(striped_word) -> str:
        return Synonym.spell.autocorrect_sentence(striped_word)
