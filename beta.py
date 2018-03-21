# -*-coding: utf-8 -*-
# Author:Zhang Haitao
# Email:13163385579@163.com
# TIME:2018-03-21  11:17
# NAME:assetPricing2-beta.py


from dout import *
import numpy as np
import statsmodels.formula.api as sm


def _get_comb():
    #page 123
    eretD = read_df('eretD', freq='D')
    eretD = eretD.stack()
    eretD.index.names = ['t', 'sid']
    eretD.name = 'eret'
    rpD=read_df('rpD','D')
    combD = eretD.to_frame().join(rpD)

    eretM = read_df('eretM', freq='M')
    eretM = eretM.stack()
    eretM.index.names = ['t', 'sid']
    eretM.name = 'eret'
    rpM=read_df('rpM','M')
    combM = eretM.to_frame().join(rpM)
    return combD,combM

def _beta(subx):
    beta=sm.ols('eret ~ rp',data=subx).fit().params['rp']
    return beta

#TODO:upgrade this funcntion use rolling
def _for_one_stock(x, months, history, thresh, type_func):
    '''
    calculate the indicator for one stock,and get a time series

    :param x:series or pandas DataFrame
    :param months:list,contain the months to calculate the indicators
    :param history:history length,such as 12M
    :param thresh:the mimium required observe number
    :param type_func:the function name from one of [_skew,_coskew,_idioskew]
    :return:time series
    '''
    sid=x.index.get_level_values('sid')[0]
    x=x.reset_index('sid',drop=True)
    values=[]
    for month in months:
        subx=x.loc[:month].last(history)
        subx=subx.dropna()
        if subx.shape[0]>thresh:
            values.append(type_func(subx))
        else:
            values.append(np.nan)
    print(sid)
    return pd.Series(values,index=months)

def groupby_rolling(multiIndDF, prefix, dict, type_func):
    values = []
    names = []
    for history, thresh in dict.items():
        days = multiIndDF.index.get_level_values('t').unique()
        months = days[days.is_month_end]
        value = multiIndDF.groupby('sid').apply(lambda df: _for_one_stock(df, months, history, thresh, type_func))
        values.append(value.T)
        names.append(prefix + '_' + history)
    result = pd.concat(values, axis=0, keys=names)
    return result

def monthly_cal(comb, prefix, dict, type_func, fn):
    result=groupby_rolling(comb,prefix,dict,type_func)
    result.to_csv(os.path.join(DATA_PATH,fn+'.csv'))
    return result

def cal_beta():
    dictD = {'1M': 15, '3M': 50, '6M': 100, '12M': 200, '24M': 450}
    dictM = {'12M': 10, '24M': 20, '36M': 24, '60M': 24}
    combD,combM=_get_comb()
    monthly_cal(combD,'D',dictD,_beta,'betaD')
    monthly_cal(combM,'M',dictM,_beta,'betaM')


if __name__=='__main__':
    cal_beta()
