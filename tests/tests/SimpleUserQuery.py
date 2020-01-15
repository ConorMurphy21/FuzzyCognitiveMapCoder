class SimpleUserQuery:

    def __init__(self, gct_result=None, gct_exists=None,
                 gut_result=None, gut_exists=None,
                 gs_result=None, gs_exists=None,
                 double_action=None,
                 ssa=None,
                 cba=None,  # can set to 0, 1 or 2 for random
                 rss=None,  # can set to 0, 1 or 2 for random
                 ):
        self.gct = gct_result, gct_exists
        self.gut = gut_result, gut_exists
        self.gs = gs_result, gs_exists
        self.double_action = double_action
        self.ssa = ssa
        self.cba = cba
        self.rss = rss

    def guesses_close_together(self, uncoded, guesses) -> (str, bool):
        return self.gct

    def guess_under_thresh(self, uncoded, guess) -> (str, bool):
        return self.gut

    def get_synonym(self, uncoded) -> (str, bool):
        return self.gs

    def get_double_anchor_action(self, anchor, headers) -> str:
        return self.double_action

    def get_second_split_anchor(self, anchor, double1, double2) -> str:
        return self.ssa

    def choose_between_anchors(self, anchor1, anchor2, synonym) -> bool:
        return self.cba

    def request_switch_synonym(self, syn: str, new: str, old: str) -> bool:
        return self.rss
