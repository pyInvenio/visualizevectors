import pandas as pd
import numpy as np
import json
import os

import json

def is_json(myjson):
  try:
    json.loads(myjson)
  except ValueError as e:
    return False
  return True

chatsembeddingscsv = pd.read_csv('static/chats-embeddings-ada-002.csv')
chats = pd.read_csv('static/chats.csv')
chatText = chats['chat_text'].values
chatsembeddingscsv = chatsembeddingscsv.dropna()
chatsembeddingscsv = chatsembeddingscsv.reset_index(drop=True)
chatsembeddingscsv = chatsembeddingscsv.drop(columns=['Unnamed: 0'])
thread_id = chatsembeddingscsv['thread_id'].values
# save all vectors under embeddings into a text file as a json
embeddings = chatsembeddingscsv['embedding'].values

dict = {}

for i in range(len(embeddings)):
    dict[thread_id[i]] = {
        "embedding": embeddings[i],
        "chat": chatText[i]
    }
    


with open('static/embeddings.txt', 'w', encoding='utf-8') as f:
    json.dump(dict, f, ensure_ascii=False, indent=4)