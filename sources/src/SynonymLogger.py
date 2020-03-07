import csv
import os
from src import FuzzyCogMap


# Responsible for logging the encodings of this algorithm
# This logs to a csv, and does not show priority to rare events, that is for another log
class SynonymLogger:
    # open and read in the csv files
    def __init__(self, log_csv, path, synonyms):
        self.headers = []  # if file isn't found that's ok, we can make one and set the headers
        self.headers.append("")
        # this needs to occur after all changes are made to the synonyms
        for syn in synonyms:
            self.headers.append(syn.anchor)
        # keep log open for appending to
        # no try catch, if this throws an error then it throws and error
        self.log_csv = open(path + log_csv, "a", encoding="utf-8-sig", newline='')
        self.log_writer = csv.writer(self.log_csv)
        # write the headers to the log file
        self.log_writer.writerow(self.headers)

        # this is important, kind of dumb, but necessary, unavoidable
        self.headers.pop(0)

    # add a new column in the log for this FCM
    def update_log_csv(self, fcm: FuzzyCogMap):

        row = [os.path.basename(fcm.file_name)]
        inv_map = {v: k for k, v in fcm.anchors.items()}
        for key, (a, b) in fcm.combine_anchors.items():
            inv_map[key] = a + "/" + b

        for anchor in self.headers:
            try:
                row.append(inv_map[anchor])
            except KeyError:
                row.append("")  # add empty row when there isn't a match

        self.log_writer.writerow(row)

    def close(self):
        self.log_csv.close()
