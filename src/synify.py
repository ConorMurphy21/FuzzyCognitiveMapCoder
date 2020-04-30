from src.synonymList import SynonymList
from src.userQuery import UserQuery
from shutil import copyfile


def main():

    file = UserQuery.get_files("Choose an almost syn file to copy and then synify")
    if not file:
        print("no file selected. exiting program.")
        return
    # file = "C:/Users/conor/PycharmProjects/FuzzyCognitaveMapDecoder/resources/syn.csv"
    arr = file.split(".")
    temp = arr[0] + "_synify." + arr[1]
    copyfile(file, temp)
    synonyms = SynonymList(temp)
    synonyms.synify()
    synonyms.store_synonyms()


if __name__ == "__main__":
    main()
