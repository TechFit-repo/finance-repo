import dropbox
import pandas as pd
import os
import io
import numpy as np
import datetime
year = datetime.datetime.today().year
pd.options.mode.chained_assignment = None
token = ' token '
dbx = dropbox.Dropbox(token)
dbx.users_get_current_account()

class FinanceAutomation:
    def __init__(self,revolut='/Finance/Revolut/',boi='/Finance/BOI/',aib='/Finance/AIB/'):
        # Revolut
        list1 = []
        for revolut_entry in dbx.files_list_folder(revolut).entries:
            list1.append(revolut_entry.name)
        revolut_trans = []
        for filename in list1:
            metadata, revolut_load = dbx.files_download(os.path.join(revolut + filename))
            with io.BytesIO(revolut_load.content) as transactions:
                revolut_load_csv = pd.read_csv(transactions, error_bad_lines=False, sep=';')
                revolut_trans.append(revolut_load_csv)
        revolut_db = pd.concat(revolut_trans, axis=0, ignore_index=True)
        self.revolut_df = revolut_db

        if len(revolut_db) ==  0:
            print("No transactions found in Revolut...")
        else:
            r_total = len(revolut_db)
        self.revolut_total = r_total

        # BOI
        list2 = []
        for boi_entry in dbx.files_list_folder(boi).entries:
            list2.append(boi_entry.name)
        boi_trans = []
        for filename in list2:
            metadata, boi_load = dbx.files_download(os.path.join(boi + filename))
            with io.BytesIO(boi_load.content) as transactions:
                boi_load_csv = pd.read_csv(transactions, error_bad_lines=False, sep=',')
                boi_trans.append(boi_load_csv)
        boi_db = pd.concat(boi_trans, axis=0, ignore_index=True)
        self.boi_df = boi_db
        if len(boi_db) ==  0:
            print("No transactions found in BOI...")
        else:
            b_total = len(boi_db)
        self.boi_total = b_total

        # AIB
        list3 = []
        for aib_entry in dbx.files_list_folder(aib).entries:
            list3.append(aib_entry.name)
        aib_trans = []
        for filename in list3:
            metadata, aib_load = dbx.files_download(os.path.join(aib + filename))
            with io.BytesIO(aib_load.content) as transactions:
                aib_load_csv = pd.read_csv(transactions, error_bad_lines=False, sep=',')
                aib_trans.append(aib_load_csv)
        aib_db = pd.concat(aib_trans, axis=0, ignore_index=True)
        self.aib_df = aib_db
        if len(aib_db) ==  0:
            print("No transactions found in AIB...")
        else:
            a_total = len(aib_db)
        self.aib_total = a_total

    def processTransaction(self):
        # Revolut
        revolut_df_process = self.revolut_df
        revolut_df_process["Date"] = pd.to_datetime(revolut_df_process["Completed Date"].str.replace(' ', '/').apply(lambda x: x + '/' + str(year) if (len(x) <= 6) else x), format='%d/%b/%Y')
        revolut_df_process = revolut_df_process[["Date","Reference","Paid Out (EUR)","Paid In (EUR)"," Balance (EUR)","Category"]]
        revolut_df_process.rename(columns = {"Paid Out (EUR)" : "Debit",  "Paid In (EUR)" : "Credit",
                                             "Reference" : "Description", " Balance (EUR)" : "Balance"}, inplace=True)
        print("Loading Revolut Transactions: " + str(self.revolut_total))
        revolut_account = revolut_df_process

        # BOI
        boi_df_process = self.boi_df
        boi_df_process["Date_Clean"] = pd.to_datetime(boi_df_process["Date"], format='%d/%m/%Y')
        boi_df_process = boi_df_process[["Date_Clean","Details","Debit","Credit","Balance"]]
        boi_df_process.rename(columns = {"Date_Clean" : "Date", "Details" : "Description"}, inplace=True)
        boi_df_process["Category"] = np.where(boi_df_process["Debit"].isnull(),'Income','Expense')
        print("Loading BOI Transactions: " + str(self.boi_total))
        boi_account = boi_df_process

        # AIB
        aib_df_process = self.aib_df
        aib_df_process["Date"] = pd.to_datetime(aib_df_process[" Posted Transactions Date"], format='%d/%m/%Y')
        aib_df_process = aib_df_process[["Date"," Description1"," Debit Amount"," Credit Amount","Balance"]]
        aib_df_process.rename(columns = {" Description1" : "Description",
                                        " Debit Amount" : "Debit"," Credit Amount" : "Credit"}, inplace=True)
        aib_df_process["Category"] = np.where(aib_df_process["Debit"].isnull(),'Income','Expense')
        print("Loading aib Transactions: " + str(self.aib_total))
        aib_account = aib_df_process

        master_account = revolut_account.append([boi_account,aib_account])
        master_account["Debit"] = master_account["Debit"].astype(str).str.replace(',', '').astype('float')
        master_account["Credit"] = master_account["Credit"].astype(str).str.replace(',', '').astype('float')
        master_account["Balance"] = master_account["Balance"].astype(str).str.replace(',', '').astype('float')
        self.master_account = master_account

    def isTaxable(self):
        master_account_expenses = self.master_account
        # Taxable Expense
        master_account_expenses["isTaxableExpense"] = np.where(master_account_expenses["Category"]=='Expense', 'Y',
                                                               np.where(master_account_expenses["Category"]=='Transport', 'Y',
                                                                        np.where(master_account_expenses["Category"].str.contains('Transfers'),'N',
                                                                                 np.where(master_account_expenses["Description"].str.contains('Top-Up'),'N',
                                                                                          np.where((master_account_expenses["Description"]=='TRANSFER'),'N',
                                                                                                   np.where(master_account_expenses["Description"].str.contains('REVO'),'N',
                                                                                                            np.where(master_account_expenses["Description"].str.contains('VDP'),'N','N')))))))
        # Taxable Income
        master_account_expenses["isTaxableIncome"] = np.where((master_account_expenses["Category"]=='Income'),'Y',
                                                              np.where((master_account_expenses["Description"]=='TRANSFER'),'N','N'))
        self.master_account_statement = master_account_expenses

    def calculateTax(self):
        tax_cal = self.master_account_statement
        tax_cal["Month"] = pd.DatetimeIndex(tax_cal["Date"]).year.astype(str) + '-' + pd.DatetimeIndex(tax_cal["Date"]).month.astype(str)
        Income = tax_cal[tax_cal["isTaxableIncome"] == 'Y']
        Expense = tax_cal[tax_cal["isTaxableExpense"] == 'Y']
        tax_cal_Income = Income.groupby("Month")["Credit"].sum()
        tax_cal_Expense = Expense.groupby("Month")["Debit"].sum()
        std_rate = .20
        high_rate = .40
        tax_month = pd.merge(tax_cal_Income, tax_cal_Expense, left_on='Month', right_on='Month')
        monthly_tax = tax_month
        monthly_tax["Taxable_Income"] = monthly_tax["Credit"]-monthly_tax["Debit"]
        monthly_tax["Overall_Tax"] = monthly_tax["Taxable_Income"].apply(lambda x: (x-2942)*high_rate+2942*std_rate if(x>2942) else x*std_rate)
        monthly_tax["Net_Income"] = monthly_tax["Taxable_Income"] - monthly_tax["Overall_Tax"]
        monthly_tax["Year-Month"] = monthly_tax.index
        self.monthly_tax = monthly_tax


    def toDropbox(self, path1 = '/Transactions/Master_Account.csv', path2 = '/Transactions/Monthly_Tax.csv'):
        df_string1 = self.master_account_statement.to_csv(index=False)
        df_bytes1 = bytes(df_string1, 'utf8')
        dbx.files_upload(
            f=df_bytes1,
            path=path1,
            mode=dropbox.files.WriteMode.overwrite)

        df_string2 = self.monthly_tax.to_csv(index=False)
        df_bytes2 = bytes(df_string2, 'utf8')
        dbx.files_upload(
            f=df_bytes2,
            path=path2,
            mode=dropbox.files.WriteMode.overwrite)

if __name__ == '__main__':
    finance = FinanceAutomation()
    finance.processTransaction()
    finance.isTaxable()
    finance.calculateTax()
    finance.toDropbox()
