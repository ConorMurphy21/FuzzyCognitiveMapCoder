import csv

from src.Synonym import Synonym
from src.UserQuery import UserQuery


class SynonymList(list):
    def __init__(self, csv_file):
        # frequency of each
        super().__init__()
        # whether the synonym list has changed since it was last stored
        self.changed = False
        self.csv_file = csv_file
        self.map = {}  # there are too many annoyances to making this class a dict,
        # but I do want access to synonyms via anchors in o(1)

        with open(csv_file, "r", encoding="utf-8-sig") as syn_file:
            reader = csv.reader(syn_file)

            # try to read the first line
            try:
                anchors = next(reader)
            except StopIteration:
                raise ValueError("Synonym file is empty.")

            # setup an array of synonyms with the anchors as the headers
            i = 0
            for anchor in anchors:
                # super used not self, so changed stays false
                super().append(Synonym(anchor))
                self.map[anchor] = i
                i += 1

            # make sure there is a row of frequencies
            try:
                self.freqs = next(reader)  # this column is the frequency
            except StopIteration:
                raise ValueError("Synonym file has no frequencies.")

            # make sure there is a frequency associated with each synonym
            if len(self.freqs) != len(self):
                raise ValueError("The frequency row, and header row do not line up correctly.")

            # make sure all the values in the frequency list are all ints
            for i in range(len(self.freqs)):
                try:
                    self.freqs[i] = int(self.freqs[i])
                except ValueError:
                    raise ValueError("Invalid Frequency Row.")

            for row in reader:
                i = 0
                for word in row:
                    if word:
                        # this will throw errors, if the file is improperly formatted
                        # but that is ok because it should throw errors
                        # self[i].add_synonym(word)
                        self.add_syn(anchors[i], word)
                    i += 1

    def append(self, synonym: str):
        self.map[synonym] = len(self)
        self.freqs.append(0)
        super().append(Synonym(synonym))
        self.changed = True

    def switch_syn(self, old: str, new: str, syn: str):
        self.add_syn(new, syn)
        self.remove_syn(old, syn)
        self.changed = True

    def remove_syn(self, anchor: str, syn: str):
        synonym = self.at(anchor)
        synonym.remove_synonym(syn)
        self.changed = True

    def at(self, key: str) -> Synonym:
        return self[self.map[key]]

    # only insert unique values
    def add_syn(self, anchor, val):
        synonym = self.at(anchor)
        # only add synonyms that are unique
        if synonym.get_fit_once(val) < 0.94:
            synonym.add_synonym(val)
            self.changed = True

    def update_frequencies(self, fcm):
        for anchor in fcm.anchors.values():
            self.freqs[self.map[anchor]] += 1

    def store_synonyms(self):
        with open(self.csv_file, "w", encoding="utf-8-sig", newline='') as syn_file:
            writer = csv.writer(syn_file)
            out = []
            for vals in self:
                out.append(vals.anchor)
            writer.writerow(out)
            writer.writerow(self.freqs)
            i = 0
            remains = True
            while remains:
                remains = False
                out = []
                for vals in self:
                    if i < len(vals.syns):
                        remains = True
                        out.append(vals.syns[i])
                    else:
                        out.append('')

                writer.writerow(out)
                i += 1
        self.changed = False

    '''
        *********************************************
        Everything below this point is for the synify method
        This method is never used in the regular algorithm it is
        solely for the purpose of fixing the syn file.
        
        This goes through the synList object and finds redundant codes,
        and double mappings, and queries the user.
        This is a quick fix because it needs to be quick, that's why the user queries
        are directly in this file.
        *********************************************
    '''
    def synify(self):
        remove = []
        for synonym in self:
            if synonym.anchor in remove:
                continue
            anchor = synonym.anchor
            redundancies = self._get_redundancies(anchor, anchor)
            if len(redundancies) != 0:
                redundancies.append(anchor)
                temp, q = self._handle_redundancies(redundancies, anchor)
                if q:
                    break
                remove += temp

            brake = False
            for syn in synonym.syns:
                redundancies = self._get_redundancies(anchor, syn)
                if len(redundancies) != 0:
                    redundancies.append(anchor)
                    temp, q = self._handle_redundancies(redundancies, syn)
                    if q:
                        brake = True
                        break
                    remove += temp
            if brake:
                break

        for string in remove:
            value = self.at(string)
            self.remove(value)

    def _get_redundancies(self, anchor, syn) -> list:
        redundancies = []
        s_word = Synonym.strip_word(syn)
        auto_word = Synonym.auto_word(syn)
        for synonym in self:
            if synonym.anchor != anchor and synonym.get_fit(s_word, auto_word) > 0.94:
                redundancies.append(synonym.anchor)
        return redundancies

    # return a list of the codes that should be deleted
    def _handle_redundancies(self, redundancies, synonym) -> (list, bool):
        print("'" + synonym + "' is a synonym for multiple anchors, please pick a single code it should map to.")
        query, options = self._options_to_str(redundancies)
        print(query)
        print("please select which one '" + synonym + "' should map to.")
        print("If one of these codes is redundant, enter 'r' to combine redundant codes otherwise"
              " enter 'c' to continue, or 'q' to save and quit.")
        result = UserQuery.repeat_until_valid(options + ['r', 'c', 'q'])
        if result == 'c':
            return [], False
        elif result == 'r':
            return self._combine_redundant_codes(redundancies), False
        elif result == 'q':
            return [], True

        for red in redundancies:
            if red != result:
                self.remove_syn(red, synonym)

        print("If one of these codes is redundant, enter 'r' to combine redundant codes otherwise"
              " enter 'c' to continue, or 'q' to save and quit.")
        result = UserQuery.repeat_until_valid(['r', 'c', 'q'])
        if result == 'c':
            return [], False
        elif result == 'r':
            return self._combine_redundant_codes(redundancies), False
        else:
            return [], True

    # returns a list of codes that should be deleted
    def _combine_redundant_codes(self, redundancies) -> list:
        remove_list = []
        while True:
            if len(redundancies) == 1:
                return remove_list
            print("Enter 'c' when you are happy with these codes.")
            query, options = self._options_to_str(redundancies)
            print("Please enter which code is redundant.")
            print(query)
            options.append('c')
            anchor = UserQuery.repeat_until_valid(options)
            if anchor == 'c':
                return remove_list
            anchor = redundancies[int(anchor)]
            redundancies.remove(anchor)  # no longer an option
            if len(redundancies) == 1:
                to_anchor = redundancies[0]
            else:
                print("Please enter which code " + anchor + " should fall under.")
                print(query)
                to_anchor = UserQuery.repeat_until_valid(options)
                if to_anchor == 'c':
                    return remove_list
                to_anchor = redundancies[int(to_anchor)]
            print("All synonyms of '" + anchor + "' will now map to: '" + to_anchor + "'.")
            self._move_all(anchor, to_anchor)
            remove_list.append(anchor)
            self.at(anchor).syns = []  # so that the removed synonyms don't match with anything
            self.at(anchor).anchor = "walking dead"

    def _move_all(self, anchor: str, to_anchor: str):
        syn = self.at(anchor)
        self.add_syn(to_anchor, anchor)
        for synonym in syn.syns:
            self.add_syn(to_anchor, synonym)

    @staticmethod
    def _options_to_str(li: list, options=None) -> (str, list):
        if not options:
            options = range(len(li))
            options = [str(i) for i in options] # numbers to the string

        if len(options) != len(li):
            raise ValueError("Options and li not the right length")

        string = ""
        for i in range(len(li)):
            string += li[i] + "(" + options[i] + "), "

        string = string[0:len(string)-2]

        return string, options