from abc import ABC, abstractmethod
from datetime import date
from typing import override

# Setting up the Account class
class Account(ABC):
    def __init__(self, account_id: str, owner_name: str, opening_balance: float):
        if opening_balance < 0:
            raise ValueError("Opening balance can't be negative")

        self._account_id = account_id
        self._owner_name = owner_name
        self._log = self.TransactionLog()
        self._log.record("OPEN", opening_balance)

    @property
    def account_id(self):
        return self._account_id

    @property
    def owner_name(self):
        return self._owner_name

    @property
    def balance(self):
        return self._log.total()

    @property
    def is_overdrawn(self):
        return self.balance < 0

    @abstractmethod
    def account_type(self):
        pass

    @abstractmethod
    def apply_interest(self):
        pass

    def deposit(self, amount):
        # Checking for negative number
        # Returning deposit transaction message if amount is successful
        if amount <= 0:
            raise ValueError("Enter a Positive Number")
        else:
            self._log.record("DEPOSIT", amount)
            return f"Deposited ${amount:.2f} to account {self._account_id}. New balance: ${self.balance:.2f}"

    def withdraw(self, amount):
        # Converting withdraw amount to negative and subtracting it from the balance
        if amount <= 0:
            raise ValueError("Enter a Positive Number")
        else:
            self._log.record("WITHDRAW", -abs(amount))
            return f"Withdrew ${amount:.2f} from account {self._account_id}. New balance: ${self.balance:.2f}"

    # String formatting
    def __str__(self):
        return f"[{self.account_type()}] {self._account_id} | {self._owner_name} | ${self.balance:.2f}"

    def __repr__(self):
        return f"{self.__class__.__name__}(id={self._account_id}, owner={self._owner_name}, balance={self.balance:.2f})"

    # TransactionLog class to track transactions
    # Updates information after transaction
    class TransactionLog:
        def __init__(self):
            self._txs = []

        def record(self, tx_type: str, amount: float):
            self._txs.append(self.Transaction(tx_type, amount, date.today()))

        def total(self):
            return sum(tx.amount for tx in self._txs)

        def __len__(self):
            return len(self._txs)

        def __contains__(self, tx_type:str):
            return any(tx.tx_type == tx_type for tx in self._txs)

        def __str__(self):
            return "\n".join(str(tx) for tx in self._txs)


        class Transaction:
            def __init__(self, tx_type: str, amount: float, date_: date):
                self.tx_type = tx_type
                self.amount = amount
                self.date_ = date_


            def __str__(self):
                if self.amount >= 0:
                    amt_str = f"+${self.amount:.2f}"
                else:
                    amt_str = f"${abs(self.amount):.2f}"

                return f"{self.date_} | {self.tx_type:<10} | {amt_str}"

            def __eq__(self, other):
                if not isinstance(other, Account.TransactionLog.Transaction):
                    return False
                return (
                    self.tx_type == other.tx_type and
                    self.amount == other.amount and
                    self.date_ == other.date_
                )

class CheckingAccount(Account):
    def __init__(self, account_id:str, owner_name:str, opening_balance: float, overdraft_fee: float = 35.0):
        super().__init__(account_id, owner_name, opening_balance)
        self._overdraft_fee = overdraft_fee

    def account_type(self):
        return "Checking"
    def apply_interest(self):
        if self.balance > 0:
            interest = self.balance * .005
            self._log.record("INTEREST", interest)
            return f"Applied .5% interest to {self._account_id}: +${interest:.2f}"
        else:
            return f"No interest applied to {self.account_id}"

class SavingsAccount(Account):
    def __init__(self, account_id: str, owner_name: str, opening_balance:float, interest_rate: float = 0.03):
        super().__init__(account_id, owner_name, opening_balance)
        self._interest_rate = interest_rate

    def account_type(self):
        return "Savings"

    @override
    def withdraw(self, amount):
        if amount > self.balance:
            raise ValueError("Insufficient funds")
        else:
            return super().withdraw(amount)

    def apply_interest(self):
        interest = self._interest_rate * self.balance
        self._log.record("INTEREST", interest)
        return f"Applied {self._interest_rate*100:.1f}% interest to {self.account_id}: +${interest:.2f}"


class LoanAccount(Account):
    def __init__(self, account_id: str, owner_name:str, loan_amount: float, interest_rate: float = 0.05):
        super().__init__(account_id, owner_name, 0)
        self._log.record("LOAN",-abs(loan_amount))
        self._interest_rate = interest_rate


    def withdraw(self, amount):
        raise NotImplementedError("Withdrawals are not allowed for LoanAccount")

    def account_type(self):
        return "Loan"

    def apply_interest(self):
        interest = self._interest_rate * abs(self.balance)
        self._log.record("INTEREST", -abs(interest))
        return f"Applied {self._interest_rate * 100:.1f}% interest to {self.account_id}: -${interest:.2f}"

    @property
    def amount_owed(self):
        return abs(self.balance)

class InterestPolicy(ABC):
    @abstractmethod
    def calculate(self, account: Account):
        return f"${account.balance:.2f}"
    @abstractmethod
    def describe(self):
        pass

class SimpleInterestPolicy(InterestPolicy):
    def __init__(self, rate: float):
        self._rate = rate

    def calculate(self, account):
        return f"{abs(account.balance) * self._rate}:.1f"
    def describe(self):
        return f"Simple interest at {self._rate:.1f}%"

class BonusInterestPolicy(InterestPolicy):
    def __init__(self, base_rate:float, bonus_rate: float, threshold: float):
        self._base_rate = base_rate
        self._bonus_rate = bonus_rate
        self._threshold = threshold

    def calculate(self, account: Account):
        if account.balance > self._threshold:
            return f"{account.balance * self._bonus_rate:.2f}"
        else:
            return f"{account.balance * self._base_rate:.2f}"

    def describe(self):
        return f"Bonus interest: {self._base_rate:.1f}% base, {self._bonus_rate:.1f}% above ${self._threshold:.1f}"


class Customer:
    def __init__(self, customer_id: str, name:str):
        self._customer_id = customer_id
        self._name = name

        self._accounts = []

    def add_account(self, account:Account):
        self._accounts.append(account)

    def remove_account(self, account:Account):
        for acc in self._accounts:
            if account.account_id == acc.account_id:
                self._accounts.remove(acc)
                return True
        return False

    def apply_policy_to_all(self, policy):
        results = []

        for acc in self._accounts:
            amount = policy.calculate(acc)
            acc._log.record("INTEREST", amount)

            results.append(f"{acc.accound_id}: +${amount:.2f}")

        return results

    def net_worth(self):
        return sum(account.balance for account in self._accounts)

    def __len__(self):
        return len(self._accounts)

    def __contains__(self, account:Account):
        return any(acc.account_id == account.account_id for acc in self._accounts)

    def __str__(self):
        return f"Customer {self._name} (ID: {self._customer_id}) | {len(self)} accounts | Net: ${self.net_worth():.2f}"







