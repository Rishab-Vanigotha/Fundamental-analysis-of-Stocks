import bs4
import requests
from bs4 import BeautifulSoup
import time
import pandas as pd
import numpy as np
import warnings

warnings.filterwarnings('ignore')
tickers = pd.read_html('https://indiancompanies.in/listed-companies-in-nse-with-symbol/')[0]
tickers.columns = tickers.iloc[0]
tickers = tickers.iloc[1:,:]
tickers = list(tickers.SYMBOL)
names = [x.upper() for x in input("enter the stock names").split()]
print(names)
fundamentals = {}

ori = 'https://www.screener.in/'
login_route = 'login/'
header = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/105.0.0.0 Safari/537.36' , 'origin':'https://www.screener.in', 'referer': '/login/','referrer-policy':'same-origin'}
s=requests.session()
csrf = s.get(ori+login_route).cookies['csrftoken']
payload = {
        'username': 'jainamjain1480@gmail.com',
        'password': 'Ggaknrkr@123',
        'csrfmiddlewaretoken': csrf
    }
login_req = s.post(ori+login_route,headers=header,data=payload)
login_req.status_code

soup_beforelogin = None
soup_afterlogin =None
def scrape(name):
    req=requests.get('https://www.screener.in/company/{}/consolidated'.format(name.upper()))
    soup_beforelogin = bs4.BeautifulSoup(req.text,'html')
    def getcompany_id():
        attr =soup_beforelogin.find('main', {'class': 'flex-grow container'}).find('div',{'id':'company-info'})
        id =attr['data-warehouse-id']
        print(id)
        return id

    soup_afterlogin = BeautifulSoup(s.get(ori+'api/company/{}/quick_ratios/'.format(getcompany_id())).text,'html.parser')
    #print(soup_afterlogin)
    return soup_beforelogin, soup_afterlogin


def get_fund(soup_beforelogin,soup_afterlogin):
    for i in range(9):
        if i==2 or i ==8:
            continue
        else:
            name=soup_beforelogin.find_all('li',{'class': 'flex flex-space-between'})[i].find('span',{'class':'name'}).text
            num=soup_beforelogin.find_all('li',{'class': 'flex flex-space-between'})[i].find('span',{'class':'number'}).text
            if num =='':
                fundamentals[name.strip()]=np.nan
            else:
                fundamentals[name.strip()]=float(num.replace(',',''))
    for i in range(8):
        name=soup_afterlogin.find_all('li',{'class': 'flex flex-space-between'})[i].find('span',{'class':'name'}).text
        num=soup_afterlogin.find_all('li',{'class': 'flex flex-space-between'})[i].find('span',{'class':'number'}).text
        if num == '':
            fundamentals[name.strip()]=np.nan
        else:
            fundamentals[name.strip()]=float(num.replace(',',''))
    return fundamentals

def pl_n_years(soup, section_id, class_name, n):
    section_html = soup.find('section',{'id': section_id})
    table_html = section_html.find('table',{'class': class_name})

    headers = []
    for header in table_html.find_all('th'):
        headers.append(  header.text or 'Type')

    table_df = pd.DataFrame(columns = headers)

    for row_ele in table_html.find_all('tr')[1:]:
            row_data = row_ele.find_all('td')
            row = [tr.text.strip() for tr in row_data]
            length = len(table_df)
            table_df.loc[length] = row 
    df = table_df[table_df['Type']=='Net Profit']
    ls = df.iloc[:,-4:-1].values
    return ls

df =None
pl_df = None
for i in range(len(names)):
    soup_beforelogin, soup_afterlogin = scrape(names[i])
    dic = get_fund(soup_beforelogin, soup_afterlogin)
    if i==0:
        df = pd.DataFrame([dic])
        df.loc[i,'Company Name'] = names[i]
    else:
        df.loc[len(df.index)] = dic
        df.loc[len(df.index)-1,'Company Name'] = names[i]
    pl = pl_n_years(soup_beforelogin,'profit-loss','data-table responsive-text-nowrap',3)
    if i == 0:
        pl_df = pd.DataFrame(pl,columns=['3 years ago','2 year ago','1 year ago'])
        pl_df.loc[i,'Company Name'] = names[i]
        #print(pl_df)
    else:
        pl = pl.flatten()
        pl_df = pl_df.append(pd.Series(pl, index=pl_df.columns[:len(pl)]), ignore_index=True)
        pl_df.loc[len(pl_df.index)-1,'Company Name'] = names[i]
pl_df.set_index('Company Name',inplace=True)
for i in range(len(pl_df)):
    for j in range(len(pl_df.columns)):
        if pl_df.iloc[i,j] == '':
            pl_df.iloc[i,j] = np.nan
        else:
            print(pl_df.iloc[i,j])
            pl_df.iloc[i,j] = float(pl_df.iloc[i,j].replace(',',''))
        #print(pl_df)
df = df.set_index('Company Name')
print(df,sep = '\n')
print(pl_df,sep = '\n')

pl_strategy = df[['Current Price','High price']]
pl_strategy.reset_index(inplace=True)
for i in range(len(pl_strategy)):
    if (pl_strategy['High price'][i] - 0.1*pl_strategy['High price'][i]) > pl_strategy['Current Price'][i]:
        pl_strategy.loc[i,'PL_strategy'] = "Buy"
    else:
        pl_strategy.loc[i,'PL_strategy'] = "Hold"
print(pl_strategy)