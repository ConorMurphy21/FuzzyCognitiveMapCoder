import csv
import os
import datetime
from src.synonymList import SynonymList
from src.userQuery import UserQuery
from src.fuzzyCogMap import FuzzyCogMap
from src.synonymLogger import SynonymLogger


# for now there is nothing to make sure the user knows what settings were correct.
# the user my mis-spell a setting and not realise the program is using the default.
# Or, a user may think a setting exists that does not
def get_settings():
    # default values
    val_map = {
        "log_csv": "syn.csv",
        "syn_csv": "syn.csv",
        "path": "log",
        "thresh": "0.84",
        "dif_thresh": "0.1",
        "log_thresh": "0.89",
        "suffix": "_COD",
        "pro_files": "processed_files.csv"
    }
    with open("settings.txt", "r") as settings:
        # populate values with what is in the settings file
        for line in settings:
            args = line.split("=")
            if len(args) != 2:  # skip any lines not following the format
                continue
            name = args[0].strip()
            value = args[1].strip()
            val_map[name] = value

    # the user submitted path is just the local path, so we need to append it to the
    # current directory
    val_map["path"] = os.path.curdir + os.path.sep + val_map["path"]
    return val_map


def get_processed_files(filename: str) -> list:
    try:
        with open(filename, "r", encoding="utf-8-sig") as file:
            reader = csv.reader(file)
            try:
                return next(reader)
            except StopIteration:
                return []
    except IOError:
        return []


def store_processed_files(file: str, old_pros: list, new_pros: list):
    old_pros += new_pros
    with open(file, "w", encoding="utf-8-sig") as file:
        writer = csv.writer(file)
        writer.writerow(old_pros)


# makes directory for this batch, and then returns what directory it made
# notably, the path returned includes a path sep at the end
def make_path_directory(location: str) -> str:
    dt_date = datetime.datetime.now()
    location += '(' + dt_date.strftime('%d.%m.%Y') + ')'
    i = 1
    temp_loc = location + os.path.sep
    while os.path.exists(temp_loc):
        temp_loc = location + '(' + str(i) + ')' + os.path.sep
        i += 1
    os.makedirs(temp_loc)
    return temp_loc


def file_collisions(files, pro_files) -> list:
    collisions = []
    for f1 in files:
        base_f1 = os.path.basename(f1)
        for f2 in pro_files:
            if base_f1 == os.path.basename(f2):
                collisions.append(f2)
    return collisions


def main():
    # get the values from the settings, or default
    val_map = get_settings()
    # get our synonym list from the provided syn_csv (location found from settings)
    synonyms = SynonymList(val_map["syn_csv"])
    # set up our user query object (this can change to become a GUI later if need be)
    uq = UserQuery(synonyms)
    # query use for which files to run the algorithm on (this should soon change to smart pick which files)
    files = uq.get_files("Please select the files you would like to code")

    # find a list of files that have already been processed by this algorithm
    pro_files = get_processed_files(val_map["pro_files"])

    # find any overlapping files, query user, and adjust accordingly
    overlap = file_collisions(files, pro_files)
    if len(overlap) != 0:
        result = uq.handle_overlap()
        if result == 'c':
            pro_files = [x for x in pro_files if x not in overlap]
        elif result == 'd':
            files = [x for x in files if x not in overlap]
        else:  # result == 'q'
            return

    # todo: remove
    print(files)

    # initialize all of the new fcms and store them in an array
    fcms = []
    for file in files:
        fcm = FuzzyCogMap(file,
                          uq,
                          synonyms,
                          float(val_map["thresh"]),
                          float(val_map["dif_thresh"]),
                          float(val_map["log_thresh"])
                          )
        fcms.append(fcm)

    # keep updating the codes until there are no new updates
    ''' 
        todo: I am unsure as to whether every time the synonyms change it should start from the start, or just keep
        doing this until there are no changes, I think both will work, it's just whether one is more natural for
        reading logs of, or for interacting with
    '''
    synonyms.changed = True  # to make this a do while instead of just while
    while synonyms.changed:
        # get codes may cause this to be set to true, so keep setting it back until it stays False
        synonyms.changed = False
        for fcm in fcms:
            fcm.get_codes()

    # we do this here because from here on there should be no more user queries, so it's safe to create it now
    val_map["path"] = make_path_directory(val_map["path"])
    print(val_map["path"])
    # at this point all of the synonyms should be in their final form so we can store them
    synonyms.store_synonyms()
    # we create this now because the synonyms for the header will not change from this point forward
    syn_logger = SynonymLogger(val_map["log_csv"], val_map["path"], synonyms)

    # now we can get the codes for all of the previously run fcms
    # we need to do this, because of the synonyms may have changed due to the above fcms
    for file in pro_files:
        fcm = FuzzyCogMap(file,
                          uq,
                          synonyms,
                          float(val_map["thresh"]),
                          float(val_map["dif_thresh"]),
                          float(val_map["log_thresh"])
                          )
        fcm.get_codes()
        # immediately store contents as older stuff fcms should be at the top
        syn_logger.update_log_csv(fcm)
        fcm.store_coded_map(val_map["path"], val_map["suffix"])

    # now that the old ones are stored, we can store the new ones
    # there should be no need to run get_codes because nothing should have changed
    if synonyms.changed:
        print("Something went wrong, this statement never should have been reached!")

    # finally store all of the most recently run fcms
    for fcm in fcms:
        # todo: update the frequency based on what the codes are for this one
        syn_logger.update_log_csv(fcm)
        fcm.store_coded_map(val_map["path"], val_map["suffix"])

    # updated the processed file list to include the ones that just ran
    store_processed_files(val_map["pro_files"], pro_files, files)

    syn_logger.close()


if __name__ == "__main__":
    main()
