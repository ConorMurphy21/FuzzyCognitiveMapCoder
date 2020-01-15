import csv
from collections import OrderedDict
import os

from sources.Synonym import Synonym
from sources.SynonymList import SynonymList
from sources.UserQuery import UserQuery


class FuzzyCogMap:
    # get header list
    def __init__(self, file: str, user_query, synonyms: SynonymList, thresh=0.85, dif_thresh=0.15,
                 log_thresh=0.93):
        self.thresh = thresh
        self.dif_thresh = dif_thresh
        self.log_thresh = log_thresh
        self.file_name = file
        self.file = open(file, "r", encoding="utf-8-sig")
        self.reader = csv.reader(self.file)
        self.headers = next(self.reader)
        self.anchors = {'': ''}  # any headers that are empty should be mapped to empty
        self.user_query = user_query
        self.synonyms = synonyms
        self.combine_anchors = {}

    # get a list of codes for each of the headers
    def get_codes(self):
        it = iter(self.headers)
        next(it)
        for header in it:
            if not header:  # don't worry about empty headers
                continue

            sorted_possibles = self.get_possibles(header)

            max_weight = first_element(sorted_possibles.values())
            options = OrderedDict()
            for key in sorted_possibles.keys():
                dif = max_weight - sorted_possibles[key]
                if dif > self.dif_thresh:
                    break
                options[key] = sorted_possibles[key]

            self.choose_anchor_from_options(header, options)

        # At this point we need to make sure that we didn't double up any of our anchors
        self.handle_double_anchor()

        # add new synonyms to the synonym table (old ones won't be added)
        for key, value in self.anchors.items():
            if key == '':
                continue
            self.synonyms.add_syn(value, key)

    def get_possibles(self, word: str) -> OrderedDict:
        possibles = OrderedDict()
        striped = Synonym.strip_word(word)
        auto = Synonym.auto_word(striped)
        for synonym in self.synonyms:
            weight = synonym.get_fit(striped, auto)
            possibles[synonym.anchor] = weight
            if weight == 1:
                break
        return OrderedDict(sorted(possibles.items(), key=lambda x: x[1], reverse=True))

    # should choose, an anchor for the header
    # if it is too hard to say, get user input
    # if they request a new anchor, call the syn_logger
    def choose_anchor_from_options(self, header, options):
        max_weight = first_element(options.values())
        if len(options) == 1 or max_weight == 1:
            if max_weight > self.thresh:
                val = first_element(options.keys())
                exists = True
            else:  # max_weight < threshold
                val, exists = self.user_query.guess_under_thresh(header, first_element(options.keys()))
        else:  # edge case if there are multiple guesses that are equal
            val, exists = self.user_query.guesses_close_together(header, options)

        # set the anchor value to val
        self.anchors[header] = val
        if not exists:  # if it doesn't exist add it as a new synonym
            self.synonyms.append(val)

    # ask user if they want to split the word or combine them
    def handle_double_anchor(self):
        doubles = self.get_double_anchors()
        check_again = False
        for anchor in doubles:
            headers = []
            for uncoded in self.anchors.keys():
                if self.anchors[uncoded] == anchor:
                    headers.append(uncoded)

            action = self.user_query.get_double_anchor_action(anchor, headers)
            if action == 'c':
                self.combine_double_anchor(anchor, headers)
            elif action == 'r':
                self.remap_double_anchor(headers)
                check_again = True
            elif action == 's':
                self.split_anchor(anchor, headers[0], headers[1])
                # we need to get the codes again now that we have switched
                self.get_codes()
            # this should hopefully never happen, should log it if it does
            else:
                pass

        # some of the above actions could cause more double anchors, so re-check
        if check_again:
            self.handle_double_anchor()

    def get_double_anchors(self) -> list:
        anchor_values = list(self.anchors.values())
        double_anchors = []
        i = 1
        for anchor in anchor_values:
            for j in range(i, len(anchor_values)):
                if anchor_values[j] == anchor and anchor not in double_anchors:
                    double_anchors.append(anchor)
            i += 1
        return double_anchors

    def combine_double_anchor(self, anchor, headers):
        self.combine_anchors[anchor] = headers[0], headers[1]

    def remap_double_anchor(self, doubles):
        for uncoded in doubles:
            val, exists = self.user_query.get_synonym(uncoded)
            sorted_possibles = self.get_possibles(uncoded)
            max_weight = first_element(sorted_possibles.values())
            max_element = first_element(sorted_possibles.keys())
            if max_weight > 0.94:
                self.user_query.request_switch_synonym(uncoded, max_element, val)
            self.anchors[uncoded] = val
            if not exists:
                self.synonyms.append(val)

    def split_anchor(self, anchor, double1, double2):
        second_anchor = self.user_query.get_second_split_anchor(anchor, double1, double2)
        if not second_anchor:
            return

        self.synonyms.append(second_anchor)
        syn_switches = []
        for syn in self.synonyms.at(anchor).syns:
            # if second_anchor is chosen by user switch the syn to the new anchor
            if not self.user_query.choose_between_anchors(anchor, second_anchor, syn):
                syn_switches.append(syn)

        for syn in syn_switches:
            self.synonyms.switch_syn(anchor, second_anchor, syn)

    # store the coded map in a csv file
    def store_coded_map(self, location, suffix):
        # get the file name with some variables, make it less dependant on format
        name = os.path.basename(self.file_name)
        new_name = os.path.splitext(name)[0] + suffix + ".csv"

        with open(location + new_name, 'w', encoding="utf-8-sig", newline='') as csv_file:
            writer = csv.writer(csv_file)
            first_inds = {v: 0 for v in self.combine_anchors.keys()}
            headers = []
            combs = []
            anchor_list = list(self.anchors.values())
            for i in range(len(anchor_list)):
                anchor = anchor_list[i]
                if anchor in first_inds.keys() and not first_inds[anchor]:
                    first_inds[anchor] = i
                elif anchor in first_inds.keys():
                    combs.append((first_inds[anchor], i))
                    headers.append(anchor)
                else:
                    headers.append(anchor)

            writer.writerow(headers)

            first_rows = {v: [] for v in self.combine_anchors.keys()}
            for row in self.reader:
                anchor = self.anchors[row[0]]
                row[0] = anchor  # replace the uncoded word with the coded word

                if anchor in first_rows.keys() and not first_rows[anchor]:
                    first_rows[anchor] = row
                    continue
                elif anchor in first_rows.keys():
                    # start at 1 because we don't want to average the row header
                    for i in range(1, len(row)):
                        row[i] = float(row[i]) / 2 + float(first_rows[anchor][i]) / 2

                for i, j in combs:
                    row[j] = (float(row[i]) + float(row[j])) / 2

                # sort backwards so all the indexes of the future pops stay the same
                sorted_firsts = sorted(list(first_inds.values()), reverse=True)
                for i in sorted_firsts:
                    row.pop(i)

                writer.writerow(row)  # write the new row
        self.file.close()


def first_element(ls):
    return next(iter(ls))
