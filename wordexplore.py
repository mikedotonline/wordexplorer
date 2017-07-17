# --------------------------------
# program:     word explore
# description: a python program to build extra terms from google knowldge graph api and store them via json objects
# TODO: all
# -------------------------------- 

#gui environment
import Tkinter as tk 
import ttk
import pygubu

#remote call handling
import urllib
import json

import nltk
from nltk.corpus import wordnet as wn #use NLTK for access to wordNet

from datetime import datetime

from itertools import chain

import logging #get some logging going to make it easier to debug
logging.basicConfig(level=logging.INFO) #optional argument, filename="tk_freebase-explorer.log" and filemode='w'


class Application:
	def __init__(self,master):
		self.master = master

		#1 Create a builder
		self.builder = builder = pygubu.Builder()

		#2 Load a UI file
		builder.add_from_file('word_explore.ui')

		# Create the widget using a master as parent
		self.mainwindow = builder.get_object('main_window', master)

		#connect callbacks
		builder.connect_callbacks(self)
		#callbacks={'on_GKSearch_button_click':self.on_GKSearch_button_click} 
		#builder.connect_callbacks(callbacks)
	
	# --------------------------------
	# method:     on_GKSearch_button_click
	# description: waht to do when the search button is clicked
	# params:     none
	# returns:    none
	# --------------------------------
	def on_GKSearch_button_click(self):
		rw = self.builder.get_object('GKResults_Listbox')
		#rw.insert(tk.END,'hi')
		et = self.builder.get_object('GKSearchTerm_Entry')
		limnum = self.builder.get_object('GKLimitNum_Entry')
		types_entry = self.builder.get_object('GKTypes_Entry')
		st = et.get() #get what is in the entry box
		lim = limnum.get()
		types=types_entry.get()

		
		#empty old stuff
		rw.delete(0,tk.END)


		#load_searchTerm = self.GKSearchTerm_Entry.get() #get the text from the searchTerm text input box
		#self.GKResults_Listbox.delete(0,END)#clear previous Entries

		#get the limiting number
		#todo:error handling for non numbers        
		#load_limit = int(self.GKLimitNum_Entry.get())
		
		#create a knowledge graph object
		gkg = GoogleKnowledgeGraph()
		#perform a search
		itemlist = gkg.get_response(st.lower(),lim,types)

		#old - iterate through response items
		for i in itemlist["itemListElement"]:
			rw.insert(tk.END,i['result']['name']) #add the items to the listbox

	# --------------------------------
	# method:     on_GKSearch_button_click
	# description: waht to do when the search button is clicked
	# params:     none
	# returns:    none
	# --------------------------------
	def on_WNSearch_button_click(self):
		#create instance objects for each pygubu control
		synonyms_listbox = self.builder.get_object('WNSynonyms_Listbox')
		hypernyms_listbox = self.builder.get_object('WNHypernyms_Listbox')
		hyponyms_listbox = self.builder.get_object('WNHyponyms_Listbox')

		searchterm_entrybox = self.builder.get_object('WNSearchTerm_Entry')

		searchterm = searchterm_entrybox.get() #get what is in the entry box
		
		#empty old stuff
		synonyms_listbox.delete(0,tk.END)
		hypernyms_listbox.delete(0,tk.END)
		hyponyms_listbox.delete(0,tk.END)

		#create a wordnet object
		wnobject = WordNet(searchterm)
		
		#perform a search and return all relevant information
		synonyms_list = list(chain.from_iterable(wnobject.get_synonyms()))

		hypernyms_list = list(chain.from_iterable(wnobject.get_hypernyms()))
		hyponyms_list = list(chain.from_iterable(wnobject.get_hyponyms()))

		#populate the lists of words
		for i in synonyms_list:
			synonyms_listbox.insert(tk.END,i) #add the items to the listbox
		for i in hypernyms_list:
			hypernyms_listbox.insert(tk.END,i) #add the items to the listbox
		for i in hyponyms_list:
			hyponyms_listbox.insert(tk.END,i) #add the items to the listbox		



# --------------------------------
# class:     GoogleKnowledgeGraph
# description: a class for handling requests to the google knowledge graph
# params:     none
# returns:    none
# --------------------------------

class GoogleKnowledgeGraph(object):
	#set initial params
	def __init__(self):
		#self.api_key = open('k.key').read()
		self.api_key=''
		self.service_url = 'https://kgsearch.googleapis.com/v1/entities:search'
	# --------------------------------
	# method:     get_response
	# description:query the google knowledge api and grab some json to play with
	# params:   query, the term that we will search
	#           limit, the number of search results to display
	#           types, the thype of things to reply with: Products, Things, People,etc.
	# returns:  response, the json object back from google
	# --------------------------------
	def get_response(self,query,limit,types):
		self.params= {
		'query':query,
		'limit':limit,
		'indent':True,
		'types':types,
		'key':self.api_key,
		}

		url = self.service_url + '?' + urllib.urlencode(self.params)
		t = datetime.now()
		response = json.loads(urllib.urlopen(url).read())
		logging.info("response completed in: "+str(datetime.now()-t))
		return response 

# --------------------------------
#class WordNet
#description: this class finds all semantic equivalent terms
#parameter: the search term
# --------------------------------
class WordNet:
	def __init__ (self,word):
		self.word = word
		#searchString = self.word+".n.01" #use first definition
		#self.term = wn.synset(searchString) #make a synset of the term

		#for debugging, write out a lists of everything that is going on
		# for i,j, in enumerate(wn.synsets(word)):
		# 	logging.info("word",i,j.name())
		# 	logging.info("Synonyms:"+", ".join(j.lemma_names()))
		# 	logging.info("Hypernyms:"+" ,".join(list(chain(*[l.lemma_names() for l in j.hypernyms()]))))
		# 	logging.info("Hyponyms:"+" ,".join(list(chain(*[l.lemma_names() for l in j.hyponyms()]))))


	
	# --------------------------------
	#method get_hyponyms
	#description: creates a list of all the semantic children 
	#returns: a list of hyponyms
	# --------------------------------
	def get_hyponyms(self):
	# 	hyponyms = set()
	# 	for hyponym in synset.hyponyms():
	# 		hyponyms |= set(self.get_hyponyms(hyponym))
	# 	return hyponyms | set(synset.hyponyms())
		li=[]
		for i,j in enumerate(wn.synsets(self.word)):
			li.append(list(chain(*[l.lemma_names() for l in j.hyponyms()])))
		return li

	# --------------------------------
	#method get_synonyms
	#description: creates a list of all the term synonyms
	#returns: a list of synonyms
	# --------------------------------
	def get_synonyms(self):
		li=[]
		for i,j, in enumerate(wn.synsets(self.word)):
			li.append(j.lemma_names())
		return li 


	# --------------------------------
	#method get_hypernyms
	#description: creates a list of all the semantic parents 
	#returns: a list of hypernyms
	# --------------------------------	
	def get_hypernyms(self):
		li=[]
		for i,j in enumerate(wn.synsets(self.word)):
			li.append(list(chain(*[l.lemma_names() for l in j.hypernyms()])))
		return li




if __name__=='__main__':
	root = tk.Tk()
	app = Application(root)
	root.mainloop()


