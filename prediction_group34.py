# -*- coding: utf-8 -*-
"""1130 randomfor.ipynb

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1imdNvWeLotjVTkQ8riUO5VFvLsJL31qN
"""

from google.colab import drive
drive.mount('/content/drive')

#basic
import json
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
#Vectorizer/scaler
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import MinMaxScaler
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder
#feature/model selection
from sklearn.feature_selection import SelectFromModel
from sklearn.model_selection import cross_val_score

#model
from sklearn.ensemble import RandomForestRegressor
#metric
from sklearn.metrics import mean_absolute_error

"""#Preprocessing

"""

trainpath= '/content/drive/MyDrive/Colab Notebooks/ml_assign/train.json'
testpath= '/content/drive/MyDrive/Colab Notebooks/ml_assign/test.json'

def extract_combine_edit_author(df):
  # Extract editor and author number as new features
  df['no_of_editors'] = df.copy()['editor'].fillna(value= '').apply(len)
  df['no_of_authors'] = df.copy()['author'].fillna(value= '').apply(len)
  # combine editors and authors into one feature
  df['edit_author'] = df['editor']
  df['edit_author'].fillna(df['author'], inplace= True)
  df['edit_author_str'] = df['edit_author'].apply(lambda namelist:
                                                          ' '.join(namelist) if isinstance(namelist, list)
                                                          else '')
  df = df.fillna(value= '')
  return df

def year_extractor(df):
  # we can directly use the extracted years since they achieve a good result
  df['extracted_pub_year'] = df.copy()['publisher'].str.extract(r'.*((19|20)\d{2})').iloc[:, 0] # year numbers in publisher are completely correct
  df['extracted_title_year'] = df.copy()['title'].str.extract(r'.*((19|20)\d{2})').iloc[:, 0]
  df['extracted_year'] = df.copy()['extracted_pub_year'].fillna(df.copy()['extracted_title_year']).str.strip().fillna(0).apply(int)
  df.drop(['extracted_pub_year', 'extracted_title_year'], axis=1, inplace=True)
  return df

def has_generator(df):
  df['has_edit_author'] = df.copy()['edit_author'].notna()
  df['has_publisher'] = df.copy()['publisher'].notna()
  df['has_abstract'] = df.copy()['abstract'].notna()
  df['has_year_in_title'] = df.copy()['extracted_year'].apply(lambda x: False if x == 0 else True)
  return df

def text_preprocessor(col): # it is suitable for titles and abstracts
  processed_col = col.fillna('').str.strip().str.lower().apply(strip_punctuation_and_numbers).apply(extra_space_eliminator)#.apply(tokenization).apply(stopwords_remove).apply(lemmatizer)
  return processed_col

def name_preprocessor(col):
  def single_name_preprocessor(l):
    return [re.sub(r'[^\w\s\u00C0-\u017F]', '', extra_space_eliminator(name.strip().lower())) for name in l]
  return col.fillna('').apply(single_name_preprocessor)

import re
def strip_punctuation(t):
  return re.sub(r'[^\w\s\u00C0-\u017F]', ' ', t)
def strip_punctuation_(t):
  return re.sub(r'[^\w\s\u00C0-\u017F]', '', t)
def strip_punctuation_and_numbers(t):
  return re.sub(r'[^\w\s\u00C0-\u017F]|[\d]', ' ', t)
def strip_numbers(t):
  return re.sub(r'[\d]', '', t)
def extra_space_eliminator(t):
  return re.sub(r'\s+', ' ', t)

def data_preprocess(datapath):
  with open(datapath, 'r') as f:
    data = json.load(f)
  # Convert to a dataframe
  df = pd.DataFrame(data)
  #feature extraction
  df_copy = df.copy()
  df_copy = extract_combine_edit_author(df_copy)
  df_copy = year_extractor(df_copy) # 0 in the column extract_year means missing value, which can be checked in the has_year column
  df_copy = has_generator(df_copy)
  df_copy['cleaned_title'] = text_preprocessor(df_copy['title'])
  df_copy['cleaned_abstract'] = text_preprocessor(df_copy['abstract'])
  df_copy['edit_author_str'] = df_copy['edit_author'].apply(lambda namelist:
                                                          ' '.join(namelist) if isinstance(namelist, list)
                                                          else '')
  df_copy['edit_author_str'] = df_copy['edit_author_str'].apply(strip_punctuation).str.strip().apply(extra_space_eliminator)
  df_copy['publisher'] = df_copy['publisher'].str.strip().fillna('')
  df_copy['abstract'] = df_copy['abstract'].str.strip().fillna('')
  print(df_copy.shape)


  if'year'in df.columns:
    X=df_copy.drop('year', axis=1)
    y=df_copy['year'].values
  else:
    X=df_copy
    y=None
  return X,y

#feature transform
def transformer(X_train,test):
   transformers = [
    ('edit_author_str', CountVectorizer(strip_accents= 'unicode', lowercase=True, ngram_range=(1, 1), decode_error= 'ignore'), 'edit_author_str'),
    ('title', TfidfVectorizer(), 'title'),
    ('abstract',TfidfVectorizer(), 'abstract') ,
    ('ENTRYTYPE', CountVectorizer(), 'ENTRYTYPE'),
    ('publisher', CountVectorizer(), 'publisher'),
    ('no_of_authors',  MinMaxScaler(), ['no_of_authors']),
    ('has_edit_author', OneHotEncoder(), ['has_edit_author']),
    ('has_publisher', OneHotEncoder(), ['has_publisher']),
    ('has_abstract', OneHotEncoder(), ['has_abstract']),
    ('has_year_in_title', OneHotEncoder(), ['has_year_in_title'])
 ]
   featurizer = ColumnTransformer(transformers=transformers, remainder='drop')
   X_train_trans = featurizer.fit_transform(X_train)
   test_trans =featurizer.transform(test)
   print(X_train_trans.shape)
   print(test_trans.shape)
   return X_train_trans,test_trans

"""# model"""

X_train,y =data_preprocess(datapath=trainpath)
test,y_none =data_preprocess(datapath=testpath)

X_train_trans,test_trans = transformer(X_train,test)

rf_1 = RandomForestRegressor(n_jobs=-1)
rf_1.fit(X_train_trans, y)

select = SelectFromModel(rf_1, prefit=True)
X_new = select.transform(X_train_trans)
test_selected = select.transform(test_trans)

rf_2 = RandomForestRegressor(n_jobs=-1)
rf_2.fit(X_new, y)

y_pred = rf_2.predict(test_selected)
print(f"The predicted values for the test set are: {y_pred}")

test['year'] = y_pred
test.to_json("predicted.json", orient='records', indent=2)