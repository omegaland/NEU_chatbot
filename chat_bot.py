import flask
import pandas as pd

import os
import sys
from flask import Flask, request
import difflib

abspath = os.path.abspath(__file__)
dname = os.path.dirname(abspath)
os.chdir(dname)





app = flask.Flask(__name__)
app.config["DEBUG"] = True



### Data import

data = pd.read_csv("./starbucks_size_prep.csv", delimiter=',')
print(data)

data = data.reset_index()
data_dict = data.to_dict('index')
data_ubevs = data.groupby('Beverage').mean()


@app.route('/', methods=['GET'])
def home():

    
    return  """<h1>Starbucks Menu Archive</h1>
            <p>This site is a prototype API for Starbucks Menu. This follows
            the tutorial here https://programminghistorian.org/en/lessons/creating-apis-with-python-and-flask </p>"""

@app.route('/webhook', methods = ['POST'])
def webhook():
    req = request.get_json()
    query_result = req.get('queryResult')
    print(query_result, file=sys.stdout)
    print(type(query_result), file=sys.stdout)

    intent = query_result['intent']['displayName']
    selected_drink = query_result['parameters'].get('drink_type')
    selected_specific = query_result['parameters'].get('specific_drinks')
    if intent == 'Specific Drink Information':
        res = information_return(data,data_ubevs,selected_specific)
        return {
      "fulfillmentText": res,
      "source": 'webhook'
    } 
    elif intent == 'Specific Drinks':
      q_res = drink_return(selected_drink)
      return {
        "fulfillmentText": f'[from webhook] Here are our {selected_drink}!\n{q_res}',
        "source": 'webhook'
      }
    elif intent == 'Buy Drink':
      res = buy_drink(selected_specific,
      {'Size':query_result['parameters'].get('drink_size'),
      'Milk':query_result['parameters'].get('bev_type')},
      data)
      return {
        "fulfillmentText": res,
        "source": 'webhook'
      }


def buy_drink(specific_drink,params,data):
    global sp_df
    sp_df = data.loc[data['Beverage'] == specific_drink,:]
    sp_df_o = sp_df.copy()
    
    if sp_df.shape[0] == 1:
        return f'Ordering one {specific_drink}! Is this correct?'
    else:
        if (params.get('Size') != ''):
            sp_df = sp_df.loc[(sp_df['size'] == params['Size']),:]
        if params.get('Milk') != '':
            sp_df = sp_df.loc[(sp_df['milk_option'] == params['Milk']),:]
        if sp_df.shape[0] == 0:
            return f'sorry we do not have this combination available for \
                {specific_drink}. The available sizes are \
                    {", ".join(sp_df_o["size"].unique())}. The available milk options are\
                     {", ".join(sp_df_o["milk_option"].unique())}.'
        elif sp_df.shape[0] == 1:
            return f'Ordering one {sp_df.iloc[0,22]} {specific_drink} with {sp_df.iloc[0,21]}! Is this correct?'
        else:
            return f'Ordering one {sp_df.iloc[0,22]} {specific_drink} with {sp_df.iloc[0,21]}! Is this correct?'


def drink_return(category):
  if category == 'frappuccino':
    res = data.loc[data['Beverage_category'].apply(lambda x:'Frappuccino' in x),'Beverage'].unique()
  elif category == 'coffee':
    res = data.loc[(data['Beverage_category']=='Coffee') |
    (data['Beverage_category'].apply(lambda x:'Espresso' in x)),'Beverage'].unique()
  elif category == 'teas':
    res = data.loc[data['Beverage_category'].apply(lambda x:'Tea' in x),'Beverage'].unique()
  elif category == 'caffeine free':
    res = data.loc[data['Caffeine (mg)'] == '0','Beverage'].unique()
  res[-1] = 'and '+res[-1]
  res = ', '.join(res)
  res = res + '\n Please let me know if you would like to learn more or order one of these drinks!'
  return res

def information_return(data_df, u_names, search):
    u_df = u_names.copy()
    u_df['similarity'] = pd.Series(u_df.index).apply(
    lambda x: difflib.SequenceMatcher(None, x, search).ratio()).to_list()
    
    u_df = u_df.sort_values(by = 'similarity',ascending = False)
    
    res_df = data_df.loc[data_df['Beverage'] == u_df.index[0],:]
    
    res_list = (res_df['size'] + ' (Calories: '+ 
                res_df['Calories'].astype(str)
                + ', Caffeine [mg]: '+ res_df['Caffeine (mg)'].astype(str) +')')
    
    res = ', '.join(res_list)
    res = u_df.index[0] + ' is available in the following sizes!\n'+res+'Would you\
        like to order?'
    return res





# A route to return all of the available entries in our catalog.
@app.route('/api/v1/resources/drinks/all', methods=['GET'])
def api_all():
    return data_dict




# A route to return low carbs entries in our catalog.
@app.route('/api/v1/resources/drinks/low_carbs', methods=['GET'])
def api_low_carbs():
    result = data[data[' Total Carbohydrates (g) ']<5]['Beverage']
    result = str(set(result.values))

    return result


# A route to return low fat entries in our catalog.
@app.route('/api/v1/resources/drinks/low_total_fat', methods=['GET'])
def api_low_total_fat():
    result = data[data[' Total Fat (g)']<1]['Beverage']
    result = str(set(result.values))

    return result


# app.run()
# The line below is needed for it to be run on repl
# app.run(host='0.0.0.0', port=8080)
