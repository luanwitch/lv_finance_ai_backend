class AIContext:

    def __init__(
        self,
        user,
        transactions=None,
        goals=None,
        debts=None,
        invoices=None,
        investments=None,
        categories=None
    ):

        self.user = user

        self.transactions = transactions or []

        self.goals = goals or []

        self.debts = debts or []

        self.invoices = invoices or []

        self.investments = investments or []

        self.categories =  categories or []