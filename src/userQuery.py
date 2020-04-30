from tkinter import Tk
from tkinter.filedialog import askopenfilenames, askopenfilename
from pip._vendor.distlib.compat import raw_input
from src.synonym import Synonym


# responsible for querying whenever user input is required
class UserQuery:

    def __init__(self, synonyms):
        self.synonyms = synonyms

    # queries user about two possible anchors that are too close together
    def guesses_close_together(self, uncoded, guesses) -> (str, bool):
        print("The uncoded word '" + uncoded + "' has multiple options that are close together.")
        print("The close ones are: " + str(guesses) + ".")
        return self.get_synonym(uncoded)

    # queries user about an anchor that the user is not confident about
    def guess_under_thresh(self, uncoded, guess) -> (str, bool):
        print("The confidence for the coding of '" + uncoded + "' is less than the threshold.")
        print("The current guess is '" + guess + "'.")
        return self.get_synonym(uncoded)

    # queries user for an anchor
    # returns the result of the query, and whether the anchor is new or not
    # checks to see if anchor seems mis-spelled
    # confirms with user if the anchor is new
    def get_synonym(self, uncoded) -> (str, bool):
        print("Please enter your code for '" + uncoded+"'.")
        result = raw_input().strip()
        match, exists = self.syn_exists(result)
        if exists == 1:
            return result, 0
        if exists >= 0.85:
            print("Your synonym has a " + str(exists) + " match with " + match + ".")
            print("Enter 'c' to confirm " + match +
                  ", 'n' to confirm new synonym: " + result + ", or 'r' to try again.")
            result = self.repeat_until_valid(['c', 'n', 'r'])
            if result == 'c':
                return match, 0
            elif result == 'n':
                return result, 1
            else:
                return self.get_synonym(uncoded)
        else:
            print("Your synonym is not an existing synonym.")
            print("Type 'c' to confirm the creation of a synonym, or 'r' to retry.")
            result = self.repeat_until_valid(['c', 'r'])
            if result == 'c':
                return result, 1
            else:
                return self.get_synonym(uncoded)

    # checks if an anchor exists or not
    # allows exclusion
    # it may be worth considering whether or not we should check all the synonyms or just the anchors
    def syn_exists(self, code, exclude="") -> (str, bool):
        code_s = Synonym.strip_word(code)
        auto = Synonym.auto_word(code_s)
        exists = 0
        match = ""
        for syn in self.synonyms:
            if syn.anchor == exclude:
                continue
            syn_exists = syn.get_fit(code_s, auto)
            if syn_exists > exists:
                exists = syn_exists
                match = syn
        return match, exists

    # query user to find out how they want to treat a double anchor
    def get_double_anchor_action(self, anchor, headers) -> str:
        if len(headers) != 2:
            print(str(headers) + " were all mapped to " + anchor + ".")
            print("Actions for this process are currently unsupported due to its rarity.")
            return 'n'
        else:
            print(headers[0] + " and " + headers[1] + " were both mapped to " + anchor + ".")
            print("Would you like to split, combine, remap or do nothing?")
            print("Enter 's', 'c', 'r', 'n' respectively.")

            return self.repeat_until_valid(['s', 'c', 'r', 'n'])

    # for now, by default when splitting an anchor, the original anchor will remain, and only the second
    # will be queried for
    # this is that query
    # returns none if the user decides to quit out of this process
    def get_second_split_anchor(self, anchor, double1, double2):
        print("In order to split " + anchor + " into two different codes, we will need a second code/anchor.")
        print("This could be " + double1 + " or " + double2 + " or something new all together.")
        result = raw_input()
        if result == double1 and anchor != double1:
            return double1
        elif result == double1 or (result == double2 and anchor == double2):
            print("The second anchor cannot be the same as the original anchor.")
            print("You can enter 'q' and then choose 'combine' or 'remap' when queried again.")
            print("Otherwise enter 'r' to to try a different code.")
            result = self.repeat_until_valid(['r', 'q'])
            if result == 'r':
                return self.get_second_split_anchor(anchor, double1, double2)
            else:  # result == 'q'
                return
        elif result == double2:
            return double2

        match, exists = self.syn_exists(result, anchor)
        if exists == 1:
            print("This code already exists.")
            print("You can remap to '" + result + "' by entering 'q' and then choosing remap when queried again.")
            print("Otherwise enter 'r' to to try a different code.")
            result = self.repeat_until_valid(['r', 'q'])
            if result == 'r':
                return self.get_second_split_anchor(anchor, double1, double2)
            else:  # result == 'q'
                return
        if exists >= 0.85:
            print("Your code has a " + str(exists) + " match with '" + match + "'.")
            print("Enter 'c' to confirm '" + result + "', 'r' to try again or 'q' to remap or combine instead.")
            result = self.repeat_until_valid(['c', 'r', 'q'])
            if result == 'c':
                return match
            elif result == 'r':
                return self.get_second_split_anchor(anchor, double1, double2)
            else:  # result == 'q'
                return
        else:
            print("'" + result + "' is a valid new anchor, type 'c' to confirm making '" + result + "' a new anchor.")
            print("Type 'r' to retry, 'q' to quit.")
            result = self.repeat_until_valid(['c', 'r', 'q'])
            if result == 'c':
                return match
            elif result == 'r':
                return self.get_second_split_anchor(anchor, double1, double2)
            else:  # result == 'q'
                return

    # returns whether the first anchor is chosen or not
    def choose_between_anchors(self, anchor1, anchor2, synonym) -> bool:
        print("Does '" + synonym + "' fall under '" + anchor1 + "'(1), or '" + anchor2 + "'(2).")
        result = self.repeat_until_valid(['1', '2', anchor1, anchor2])
        if result == anchor1 or result == '1':
            return True
        elif result == anchor2 or result == '2':
            return False

    def request_switch_synonym(self, syn: str, new: str, old: str) -> bool:
        print("'" + syn + "' is currently a synonym for '" + old + "'.")
        print("Would you like to make '" + syn + "' be a a synonym for '" + new + "' instead?")
        print("(y/n)")
        return self.repeat_until_valid(['y', 'n']) == 'y'

    def handle_overlap(self) -> str:
        print("Some of the files that you selected have already been processed by this algorithm.")
        print("This should never happen, and if it did you should probably exit this program.")
        print("On the off chance this is just a miss-click, or you are testing here are some options.")
        print("Enter 'q' to quit, 'c' to continue, or 'd' to only process the ones that have not been processed")
        print("If you continue, your frequency table will be unreliable.")
        return self.repeat_until_valid(['q', 'c', 'd'])

    # continue requesting until the response is in a requested format
    @staticmethod
    def repeat_until_valid(valid_exps) -> str:
        result = raw_input()
        while result not in valid_exps:
            print(result + " is not a recognized response, please try again.")
            result = raw_input()
        return result

    # get a list of files on which to run the algorithm on
    @staticmethod
    def get_files(request):
        #return 'C:/Users/conor/PycharmProjects/FuzzyCognitaveMapDecoder/resources/toy_test/001_test.csv'
        Tk().withdraw()  # we don't want a full GUI, so keep the root window from appearing
        return askopenfilename()  # show an "Open" dialog box and return the path to the selected file
