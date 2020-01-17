from sources.SynonymList import SynonymList
from sources.UserQuery import UserQuery
from shutil import copyfile


def main():

    file = UserQuery.get_files("Choose an almost syn file to copy and then synify")[0]
    # file = "C:/Users/conor/PycharmProjects/FuzzyCognitaveMapDecoder/resources/syn.csv"
    arr = file.split(".")
    temp = arr[0] + "_synify." + arr[1]
    copyfile(file, temp)
    synonyms = SynonymList(temp)
    synonyms.synify()
    synonyms.store_synonyms()


if __name__ == "__main__":
    main()
