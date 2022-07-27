
pd.options.display.float_format = '{:.3f}'.format

def riskFreeRate():
    url_rf = 'https://home.treasury.gov/resource-center/data-chart-center/interest-rates/TextView?type=daily_treasury_yield_curve&field_tdr_date_value_month=202207'
    dfs_rf = pd.read_html(url_rf, attrs={"class":"views-table"}, index_col='Date')
    df_rf = dfs_rf[0]
    risk_free_rate = df_rf.iloc[-1,16] /100
    return risk_free_rate

def equityRiskPremium():
    ssl._create_default_https_context = ssl._create_unverified_context
    url_rf = 'https://pages.stern.nyu.edu/~adamodar/New_Home_Page/datafile/ctryprem.html'
    dfs_rf = pd.read_html(url_rf)
    df_rf = dfs_rf[0]
    new_header = df_rf.iloc[0] #grab the first row for the header
    df_rf = df_rf[1:] #take the data less the header row
    df_rf.columns = new_header #set the header row as the df header
    df_rf.set_index('Country', inplace=True)
    df_rf.columns = ["Moody's Rating", "Adj Default Spread", "Country Risk Premium", "Equity Risk Premium", "Country Risk Premium"]
    df_rf['Equity Risk Premium'] = df_rf['Equity Risk Premium'].str.rstrip('%').astype('float')
    erp = df_rf.loc['United States']['Equity Risk Premium'] / 100
    return erp

def stockBio(symbol):
    dfs = []
    stock = yf.Ticker(symbol)
    stock_bio = stock.info
    stock_df = pd.DataFrame(list(stock_bio.items()))
    stock_df.columns = ['key','value']
    stock_df.set_index("key", inplace = True)
    df_financials = stock.financials
    df_financials.apply(pd.to_numeric)
#    dfs.append(stock_df)
#    dfs.append(df_financials)
 #   return dfs
    myDict = {}
 #   stock_df = stockBio(symbol)[0]
 #   df_financials = stockBio(symbol)[1]
    myDict['stock_beta'] = stock_df.loc['beta'].values[0]
    myDict['interest_expense'] = abs(df_financials.iloc[10,0])
    myDict['total_debt'] = stock_df.loc['totalDebt'].values[0]
    myDict['income_tax_expense'] = abs(df_financials.iloc[14,0])
    myDict['income_before_tax'] = df_financials.iloc[2,0]
    myDict['enterprise_value'] = stock_df.loc['enterpriseValue'].values[0]
    myDict['freeCashflow'] = stock_df.loc['freeCashflow'].values[0]
    myDict['total_cash'] = stock_df.loc['totalCash'].values[0]
    myDict['shares_outstanding'] = stock_df.loc['sharesOutstanding'].values[0]
    myDict['current_price'] = stock_df.loc['currentPrice'].values[0]
    myDict['company'] = stock_df.loc['longName'].values[0]
    return myDict

def getCalcData():
    holder = stockBio # prevents repeated calls to the api
    myDictCalc = {}
    myDictCalc['cost_of_equity'] = ((holder['stock_beta'] * (equityRiskPremium())) + (riskFreeRate()))
    myDictCalc['cost_of_debt_preTax'] = (holder['interest_expense'] / holder['total_debt'])
    myDictCalc['tax_rate'] = (holder['income_tax_expense'] / holder['income_before_tax'])
    myDictCalc['cost_of_debt_postTax'] = myDictCalc['cost_of_debt_preTax'] * (1 - myDictCalc['tax_rate'])
    myDictCalc['debt_to_cap'] = holder['total_debt'] / holder['enterprise_value']
    myDictCalc['WACC'] = (1 - myDictCalc['debt_to_cap']) * myDictCalc['cost_of_equity'] + (myDictCalc['debt_to_cap'] * myDictCalc['cost_of_debt_postTax'])
    return myDictCalc

def growthRate(growth_rate):
    holderGrowth = calcData
  #  growth_rate = growth_rate
  #  growth_rate = float(input('Enter the expected growth rate: '))
    if growth_rate > holderGrowth['WACC']:
        print('Growth rate cannot exceed WACC, reverting to default values')
        growth_rate = calcData['WACC'] - riskFreeRate()
    else:
        growth_rate = growth_rate
        
    return growth_rate

def getNPV():
    holder = stockBio
    holderNPV = calcData
    currentYear = datetime.now().year
    years_list = []
    freecashflow_list = []
    discount_factor_list = []
    for i in range(1,7):
        years_list.append(int(currentYear + i - 1))
        freecashflow_list.append(holder['freeCashflow'] * ((1 + growth_rate) ** i))
    for i in range(1,6):
        discount_factor_list.append(1/((1 + holderNPV['WACC']))**i)
    discount_factor_list.append(1/((1 + holderNPV['WACC']))**5) # terminal year
    
    df_npv = pd.DataFrame(columns = ['years','free cash flow', 'discount factor','present value'])
    
    df_npv['years'] = years_list
    df_npv['free cash flow'] = freecashflow_list
    df_npv['discount factor'] = discount_factor_list
    df_npv['present value'] = df_npv['free cash flow'] * df_npv['discount factor']
    
    terminal_year_cashflow = df_npv['free cash flow'].iloc[-1]
    discount_factor_terminalYear = df_npv['discount factor'].iloc[-1]

    present_value_TerminalYear = (terminal_year_cashflow / (holderNPV['WACC'] - growth_rate)) * discount_factor_terminalYear
    #present_value_TerminalYear = (terminal_year_cashflow / .01 ) * discount_factor_terminalYear
    #df_npv.loc[df_npv['years'] == currentYear + 3, ['years']] = 'Terminal Year'
    df_npv['years'].iloc[-1] = 'Terminal Year'
    df_npv['present value'].iloc[-1] = present_value_TerminalYear
    df_npv.set_index('years', inplace=True)
    npv = df_npv['present value'].sum()
    
    return [npv, df_npv]

def equityValue():
    holderEQV = stockBio
    equity_value = getNPV()[0] + holderEQV['total_cash'] - holderEQV['total_debt']
    return equity_value

def shareValuation():
    holderSV = stockBio
    share_valuation = equityValue() / holderSV['shares_outstanding']
    return share_valuation

def printstockBio():
  #  df = pd.DataFrame(list(stockBio.items()), columns=['Key', 'Value'])
    df = PrettyTable(['Key', 'Value'])
    count = 0
    for key,value in stockBio.items():
        if count > 0 & count < 9:
            if (isinstance(value, int)) | (isinstance(value, float)):
                df.add_row([key,"${0:,.0f}".format(value)])
                count += 1
            else:
                df.add_row([key,value])
                count += 1
        else:
            df.add_row([key,value])
         #   count += 1
    display(df)
    
def printcalcData():
    #df = pd.DataFrame(list(calcData.items()), columns=['Key', 'Value'])
    df = PrettyTable(['Key', 'Value'])
    count = 0   
    for key,value in calcData.items():
        if count <= 5:
            df.add_row([key,"{0:,.3f} %".format(value*100)])
            count += 1
        elif (count >= 6) & (count <= 8):
            df.add_row([key,"${0:,.2f}".format(value)])
            count += 1
        else:
            df.add_row([key,value])
    display(df)

def recommendation(share_valuation):
    if share_valuation > stockBio['current_price']:
        recommendation = 'BUY'
    elif (share_valuation >= stockBio['current_price'] * .90):
        recommendation = "HOLD"
    else:
        recommendation = "SELL"
    return recommendation

symbol = input('Enter the stock symbol: ')
growth_rate = float(input('Enter growth rate: '))
stockBio = stockBio(symbol)
calcData = getCalcData()
growth_rate = growthRate(growth_rate)
calcData['NPV'] = getNPV()[0]
calcData['Equity Value'] = equityValue()
calcData['Fair Value']= shareValuation()
calcData['Recommendation'] = recommendation(calcData['Fair Value'])
printstockBio()
printcalcData()
display(getNPV()[1])
