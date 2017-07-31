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

import psycopg2

import time
import sys
import re
from gensim import corpora, models

import warnings
warnings.filterwarnings("ignore",category=DeprecationWarning)

from pprint import pprint as pp


# --------------------------------
# class:     Application
# description: code for the click handling and interface of the program. 
# params:     none
# returns:    none
# --------------------------------
class Application:
	def __init__(self,master):
		self.master = master

		#1 Create a builder
		self.builder = builder = pygubu.Builder()

		#2 Load a UI file
		builder.add_from_file('word_explore.ui')
		#builder.add_from_file('packing_notebook.ui')

		# Create the widget using a master as parent
		self.mainwindow = builder.get_object('main_window', master)
		#self.mainwindow = builder.get_object('main', master)

		#connect scrollbar
		# listbox = self.builder.get_object('WLTerms_Treeview')
		# scroll = self.builder.get_object("scrollbarhelper_2")
		# listbox.configure(yscrollcommand=scroll.set)
		# scroll.configure(command=listbox.yview)

		#GKList = self.builder.get_object("GKResults_Listbox")
		#GKList.pack(fill=tk.BOTH)


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
	# method:     on_GKSelectAll_button_click
	# description: select all the items in the results 
	# params:     none
	# returns:    none
	# --------------------------------
	def on_GKSelectAll_button_click(self):
		resultsbox = self.builder.get_object('GKResults_Listbox')
		resultsbox.select_set(0,tk.END)

	# --------------------------------
	# method:     on_WGKSelectNone_button_click
	# description: deselect all items in results
	# params:     none
	# returns:    none
	# --------------------------------
	def on_GKSelectNone_button_click(self):
		resultsbox = self.builder.get_object('GKResults_Listbox')
		resultsbox.selection_clear(0,tk.END)

	# --------------------------------
	# method:     on_GKAddToMaster_button_click
	# description: add the currently selected items to the masterlist
	# params:     none
	# returns:    none
	# --------------------------------	
	def on_GKAddToMaster_button_click(self):
		resultsbox = self.builder.get_object('GKResults_Listbox')
		master = self.builder.get_object('MasterList_Listbox')
		selected =resultsbox.curselection()	
		for i in selected:master.insert(tk.END,resultsbox.get(i))

	# --------------------------------
	# method:     on_WNSearch_button_click
	# description: what to do when the search button is clicked
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
	# method:     on_WNSelectAll_button_click
	# description: select all items in all lists
	# params:     none
	# returns:    none
	# --------------------------------
	def on_WNSelectAll_button_click(self):	
		resultsbox1 = self.builder.get_object('WNSynonyms_Listbox') 	#get object
		resultsbox1.select_set(0,tk.END)								#add all to selection
		resultsbox2 = self.builder.get_object('WNHyponyms_Listbox')
		resultsbox2.select_set(0,tk.END)
		resultsbox3 = self.builder.get_object('WNHypernyms_Listbox')
		resultsbox3.select_set(0,tk.END)

	# --------------------------------
	# method:     on_WNSelectNone_button_click
	# description: clear the selected items in all lists
	# params:     none
	# returns:    none
	# --------------------------------
	def on_WNSelectNone_button_click(self):
		resultsbox = self.builder.get_object('WNSynonyms_Listbox')	#get object
		resultsbox.selection_clear(0,tk.END)						#clear all from selection
		resultsbox = self.builder.get_object('WNHyponyms_Listbox')
		resultsbox.selection_clear(0,tk.END)
		resultsbox = self.builder.get_object('WNHypernyms_Listbox')
		resultsbox.selection_clear(0,tk.END)

	# --------------------------------
	# method:     on_WNAddToMaster_button_click
	# description: add the currently selected items to the master list
	# params:     none
	# returns:    none
	# --------------------------------
	def on_WNAddToMaster_button_click(self):
		resultsbox = self.builder.get_object('WNSynonyms_Listbox')
		master = self.builder.get_object('MasterList_Listbox')
		selected =resultsbox.curselection()	
		for i in selected:master.insert(tk.END,resultsbox.get(i))

		resultsbox = self.builder.get_object('WNHypernyms_Listbox')
		master = self.builder.get_object('MasterList_Listbox')
		selected =resultsbox.curselection()	
		for i in selected:master.insert(tk.END,resultsbox.get(i))

		resultsbox = self.builder.get_object('WNHyponyms_Listbox')
		master = self.builder.get_object('MasterList_Listbox')
		selected =resultsbox.curselection()	
		for i in selected:master.insert(tk.END,resultsbox.get(i))

	# --------------------------------
	# method:     on_MLDelete_button_click
	# description: delete items from the masterlist. cannot be undone.
	# params:     none
	# returns:    none
	# --------------------------------
	def on_MLDelete_button_click(self):
		master = self.builder.get_object('MasterList_Listbox')
		#s = master.curselection()
		for i in master.curselection()[::-1]:master.delete(i,i)

	# --------------------------------
	# method:     on_MLSave_button_click
	# description: create a new masterlist file, or add to the one that is already there
	# params:     none
	# returns:    none
	# --------------------------------	
	def on_MLSave_button_click(self):
		filenamebox = self.builder.get_object('MLFilename_Entry')
		filename = filenamebox.get()
		masterlist = self.builder.get_object('MasterList_Listbox')
		tag1 = self.builder.get_object('MLTag1_Entry')
		tag2 = self.builder.get_object('MLTag2_Entry')
		tag3 = self.builder.get_object('MLTag3_Entry')
		tags=[]
		logging.info("tag1:"+tag1.get()+"\ntag2:"+tag2.get()+"\ntag3:"+tag3.get())
		if (tag1.get() is not None and tag1.get() is not ""):
			tags.append(tag1.get() )
		if (tag2.get() is not None and tag2.get() is not ""):
			tags.append(tag2.get())
		if (tag3.get() is not None and tag3.get() is not ""):
			tags.append(tag3.get())

		with open(filename) as infile:
			d = json.load(infile)

		logging.info('mastlistitems\n'+str(list(masterlist.get(0,tk.END))))
		
		for i in masterlist.get(0,tk.END):
			d.update({i:tags})
		logging.info("dict:"+str(d))
		with open(filename,'w') as outfile:
			json.dump(d,outfile,ensure_ascii=False)

	# --------------------------------
	# method:     on_MLLoad_button_click
	# description: load the json file at the location specified in the filename entry box
	# params:     none
	# returns:    none
	# --------------------------------
	def on_MLLoad_button_click(self):
		filenamebox = self.builder.get_object('MLFilename_Entry')
		filename = filenamebox.get()
		masterlist = self.builder.get_object('MasterList_Listbox')
		with open(filename) as infile:
			d = json.load(infile)

		for i in d.keys():
			masterlist.insert(tk.END,i)


	''' TAB 2 Event Handlers
	--------------------------------------------------------------------------------------
	--------------------------------------------------------------------------------------
	'''

	# --------------------------------
	# method:     on_WLLoad_button_click
	# description: load the json file at the location specified in the filename entry box
	# params:     none
	# returns:    none
	# --------------------------------
	def on_WLLoad_button_click(self):
		tree = self.builder.get_object('WLTerms_Treeview')

		filenamebox = self.builder.get_object('WLFile_Entry')
		filename = filenamebox.get()
		with open(filename) as infile:
			d = json.load(infile)

		for i in d.keys():
			tree.insert('','end',text=i,values=d[i])


	# --------------------------------
	# method:     on_WLRemove_button_click
	# description: remove list items in the event they are not helpful
	# params:     none
	# returns:    none
	# --------------------------------
	def on_WLRemove_button_click(self):
		tree = self.builder.get_object('WLTerms_Treeview')
		selecteditem = tree.selection()
		#delete from last to first to preserve list indexes
		for i in selecteditem[::-1]:
			tree.delete(i)
	
	# --------------------------------
	# method:     on_SQLGenerate_button_click
	# description: load the json file at the location specified in the filename entry box
	# params:     none
	# returns:    none
	# --------------------------------
	def on_SQLGenerate_button_click(self):
		#host=self.builder.get_object('SQLHost_Entry').get()
		#port=self.builder.get_object('SQLPort_Entry').get()
		#db=self.builder.get_object('SQLDB_Entry').get()
		
		tbl=self.builder.get_object('SQLTableName_Entry').get()
		datacol=self.builder.get_object('SQLDataCol_Entry').get()
		geomcol=self.builder.get_object('SQLGeom_Entry').get()
		
		bndrytbl=self.builder.get_object('SQLBoundaryTable_Entry').get()
		bndrygeom=self.builder.get_object('SQLBoundaryGeom_Entry').get()
		bndryname=self.builder.get_object('SQLBoundaryName_Entry').get()

		areacheck = self.builder.get_variable('SQLArea_check_value').get()

		wherestring =""
		tree = self.builder.get_object('WLTerms_Treeview')
		for i in tree.get_children():
			#print tree.item(i)["text"]
			wherestring+= tbl+"."+datacol+" LIKE (\'%"+tree.item(i)["text"]+"%\') OR "

		wherestring=wherestring[:-3] #get rid of the last OR statement tacked onto the end
		
		self.SQLString =""
		# print areacheck
		if areacheck:
			print "area check on"
			self.SQLString= "SELECT "+tbl+".*,"+bndrytbl+"."+bndryname+\
								" FROM "+bndrytbl+" LEFT JOIN "+tbl+""\
								" ON ST_CONTAINS(ST_TRANSFORM("+bndrytbl+"."+bndrygeom+",4326),"+tbl+"."+geomcol+") WHERE "
			#wherestring +="AND ST_CONTAINS(ST_TRANSFORM("+bndrytbl+"."+bndrygeom+\
			#					", 4326),"+tbl+"."+geomcol+")"
			print "SQLSTRING:\n"+self.SQLString
			print "wherestring:\n"+wherestring

		else:
			print "area check off"
			self.SQLString = "SELECT * FROM "+tbl+" WHERE "

		

		self.SQLString+=wherestring

		self.builder.get_object('SQLS_Text').delete("1.0",tk.END)
		self.builder.get_object('SQLS_Text').insert(tk.END,self.SQLString)
	
	# --------------------------------
	# method:     on_SQLDefault_button_click
	# description: throw in the default values for my database information so that i don't need to keep doing this
	# params:     none
	# returns:    none
	# todo:			create a user configurable json file location entrybox
	# --------------------------------
	def on_SQLDefaultVal_button_click(self):
		#filenamebox = self.builder.get_object('WLFile_Entry')
		filename = 'db_defaultinfo.json'#filenamebox.get()
		with open(filename) as infile:
			d = json.load(infile)

		self.builder.get_object('SQLHost_Entry').delete(0,tk.END)
		self.builder.get_object('SQLHost_Entry').insert(0,d['host'])
		self.builder.get_object('SQLPort_Entry').delete(0,tk.END)
		self.builder.get_object('SQLPort_Entry').insert(0,d['port'])
		self.builder.get_object('SQLDB_Entry').delete(0,tk.END)
		self.builder.get_object('SQLDB_Entry').insert(0,d['dbname'])
		self.builder.get_object('SQLTableName_Entry').delete(0,tk.END)
		self.builder.get_object('SQLTableName_Entry').insert(0,d['tablename'])
		self.builder.get_object('SQLDataCol_Entry').delete(0,tk.END)
		self.builder.get_object('SQLDataCol_Entry').insert(0,d['datacolumn'])
		self.builder.get_object('SQLGeom_Entry').delete(0,tk.END)
		self.builder.get_object('SQLGeom_Entry').insert(0,d['geomcolumn'])
		self.builder.get_object('SQLBoundaryTable_Entry').delete(0,tk.END)
		self.builder.get_object('SQLBoundaryTable_Entry').insert(0,d['boundarytable'])
		self.builder.get_object('SQLBoundaryGeom_Entry').delete(0,tk.END)
		self.builder.get_object('SQLBoundaryGeom_Entry').insert(0,d['boundarygeom'])
		self.builder.get_object('SQLBoundaryName_Entry').delete(0,tk.END)
		self.builder.get_object('SQLBoundaryName_Entry').insert(0,d['boundaryname'])		


	# --------------------------------
	# method:     on_SQLSLoad_button_click
	# description: save a json file at the location specified in the filename entry box
	# params:     none
	# returns:    none
	# --------------------------------
	def on_SQLSLoad_button_click(self):
		self.builder.get_object('SQLS_Text').delete("1.0",tk.END)
		fn = self.builder.get_object('SQLSFile_Entry').get()
		f=open(fn)
		self.builder.get_object('SQLS_Text').insert(tk.END,f.read())		

	# --------------------------------
	# method:     on_SQLSSave_button_click
	# description: save the json file at the location specified in the filename entry box
	# params:     none
	# returns:    none
	# --------------------------------
	def on_SQLSSave_button_click(self):
		fn = self.builder.get_object('SQLSFile_Entry').get()
		f=open(fn,'w')
		f.write(self.builder.get_object('SQLS_Text').get("1.0",tk.END))
		f.close()

	# --------------------------------
	# method:     on_CorpusLoad_button_click
	# description: execute a database search using the sql in the previous box
	# params:     none
	# returns:    none
	# todo:			implement as a treeview to increase readability
	# --------------------------------
	def on_CorpusLoad_button_click(self):
		logging.info("starting connection to database")

		#get user credentials
		filenamebox = self.builder.get_object('SQLUserFile_Entry')
		filename = filenamebox.get()
		with open(filename) as infile:
			d = json.load(infile)

		#set up database connection data
		db_name = self.builder.get_object('SQLDB_Entry').get()
		db_user = d["username"]
		db_host = self.builder.get_object('SQLHost_Entry').get()
		db_port = self.builder.get_object('SQLPort_Entry').get()
		db_password = d["password"]
		connString = "dbname='"+db_name+"' user='"+db_user+"' host='"+db_host+"' port='"+db_port+"' password='"+db_password+"'"
		
		#connect to DB
		conn = psycopg2.connect(connString)
		logging.info("creating cursor")		
		curr = conn.cursor() #cursor for reading tweets
		
		selectstring = self.builder.get_object('SQLS_Text').get("1.0",tk.END)
		limit = self.builder.get_object('CorpusLimit_Entry').get()
		selectstring += " LIMIT "+limit
		#get data from postgres table	
		logging.info("executing select statement")
		curr.execute(selectstring)

		#output the tweets that were found
		logging.info('writing tweets into listbox')		
		preview = self.builder.get_object('CorpusPreview_Listbox')
		preview.delete(0,tk.END)
		for tweet in curr:
			s = "tweet:\n\t"+str(tweet)
			logging.info(s)
			preview.insert(tk.END,tweet)
	
	''' TAB 3 Event Handlers
	--------------------------------------------------------------------------------------
	--------------------------------------------------------------------------------------
	'''

	# --------------------------------
	# method:     	on_TopicDefaultValuesLoad_button_click
	# description: 	load the json file at the location specified in the filename entry box
	# params:     	none
	# returns:    	none
	# --------------------------------
	def on_TopicDefaultValuesLoad_button_click(self):
		#filename = 'db_defaultinfo.json'#filenamebox.get()
		filename = self.builder.get_object('TopicDefaultValues_Entry').get()
		with open(filename) as infile:
			d = json.load(infile)

		#set the values...
		self.builder.get_object('TopicHost_Entry').delete(0,tk.END)
		self.builder.get_object('TopicHost_Entry').insert(0,d['host'])
		self.builder.get_object('TopicPort_Entry').delete(0,tk.END)
		self.builder.get_object('TopicPort_Entry').insert(0,d['port'])
		self.builder.get_object('TopicDB_Entry').delete(0,tk.END)
		self.builder.get_object('TopicDB_Entry').insert(0,d['dbname'])
		self.builder.get_object('TopicSocialTable_Entry').delete(0,tk.END)
		self.builder.get_object('TopicSocialTable_Entry').insert(0,d['tablename'])
		self.builder.get_object('TopicSocialData_Entry').delete(0,tk.END)
		self.builder.get_object('TopicSocialData_Entry').insert(0,d['datacolumn'])
		self.builder.get_object('TopicSocialGeom_Entry').delete(0,tk.END)
		self.builder.get_object('TopicSocialGeom_Entry').insert(0,d['geomcolumn'])
		self.builder.get_object('TopicBndryTable_Entry').delete(0,tk.END)
		self.builder.get_object('TopicBndryTable_Entry').insert(0,d['boundarytable'])
		self.builder.get_object('TopicBndryGeom_Entry').delete(0,tk.END)
		self.builder.get_object('TopicBndryGeom_Entry').insert(0,d['boundarygeom'])
		self.builder.get_object('TopicBndryName_Entry').delete(0,tk.END)
		self.builder.get_object('TopicBndryName_Entry').insert(0,d['boundaryname'])

	# --------------------------------
	# method:     	on_TopicParamDefaults_button_click
	# description: 	load the json file at the location specified in the filename entry box
	# params:     	none
	# returns:    	none
	# --------------------------------
	def on_TopicParamDefaults_button_click(self):
		filename = self.builder.get_object('TopicParamsFile_Entry').get()
		with open(filename) as infile:
			d = json.load(infile)

		self.builder.get_object('TopicStopwords_Listbox').delete(0,tk.END)
		for w in d['stopwords']:
			self.builder.get_object('TopicStopwords_Listbox').insert(tk.END,w.replace("\\'","\'"))

		self.builder.get_object('TopicParamTopics_Entry').delete(0,tk.END)
		self.builder.get_object('TopicParamTopics_Entry').insert(0,d['topics'])
		self.builder.get_object('TopicParamWords_Entry').delete(0,tk.END)
		self.builder.get_object('TopicParamWords_Entry').insert(0,d['words'])
		self.builder.get_object('TopicParamAlpha_Entry').delete(0,tk.END)
		self.builder.get_object('TopicParamAlpha_Entry').insert(0,d['alpha'])
		self.builder.get_object('TopicParamPasses_Entry').delete(0,tk.END)
		self.builder.get_object('TopicParamPasses_Entry').insert(0,d['passes'])
		self.builder.get_object('TopicParamUpdate_Entry').delete(0,tk.END)
		self.builder.get_object('TopicParamUpdate_Entry').insert(0,d['update'])

	# --------------------------------
	# method:     	on_TopicModelRun_button_click
	# description: 	load the json file at the location specified in the filename entry box
	# params:     	none
	# returns:    	none
	# --------------------------------
	def on_TopicModelRun_button_click(self):
		start = time.time() #to know how long the model took to run
		
		#get user credentials
		filenamebox = self.builder.get_object('TopicUser_Entry')
		filename = filenamebox.get()
		with open(filename) as infile:
			d = json.load(infile)
		#set up database connection data
		db_name = self.builder.get_object('TopicDB_Entry').get()
		db_user = d["username"]
		db_host = self.builder.get_object('TopicHost_Entry').get()
		db_port = self.builder.get_object('TopicPort_Entry').get()
		db_password = d["password"]
		connString = "dbname='"+db_name+"' user='"+db_user+"' host='"+db_host+"' port='"+db_port+"' password='"+db_password+"'"
		
		#connect to DB
		conn = psycopg2.connect(connString)
		logging.info("creating cursor")		
		curr = conn.cursor() #cursor for reading tweets

		# select only three nHoods to keep problem size reasonable for now....
		poly_tableName = self.builder.get_object('TopicBndryTable_Entry').get()
		poly_identCol = self.builder.get_object('TopicBndryName_Entry').get()
		poly_geomCol = self.builder.get_object('TopicBndryGeom_Entry').get()
		
		socialcol = self.builder.get_object('TopicSocialData_Entry').get()
		socialtable = self.builder.get_object('TopicSocialTable_Entry').get()
		#selectstring = "SELECT "+socialcol+" FROM "+socialtable

		# for testing onle
		selectstring = "SELECT * FROM van_tweets WHERE tweet "\
			"LIKE (\'%obesity%\') OR" \
			" tweet LIKE (\'%unhealthy%\') OR"\
			" tweet LIKE (\'%obese%\') OR tweet LIKE (\'%junk food%\') OR"\
			" tweet LIKE (\'%foodcoma%\') OR"\
			" tweet LIKE (\'%overweight%\') OR"\
			" tweet LIKE (\'%bloated%\') OR"\
			" tweet LIKE (\'%fatty%\') OR"\
			" tweet LIKE (\'%sugartax%\') OR"\
			" tweet LIKE (\'%cholesterol%\') OR"\
			" tweet like (\'%lethargic%\') OR"\
			" tweet like (\'%couchpotato%\') OR"\
			" tweet like (\'%sugar%\') OR"\
			" tweet like (\'%fattest%\') OR"\
			" tweet like (\'%fastfood%\') OR"\
			" tweet like (\'%fast food%\') OR"\
			" tweet like (\'%feel fat%\') OR"\
			" tweet like (\'%bacon%\') OR"\
			" tweet like (\'%burgers%\') OR"\
			" tweet like (\'%sausage%\') OR"\
			" tweet like (\'%kfc%\') OR"\
			" tweet like (\'%mcdonalds%\') OR"\
			" tweet like (\'%a&w%\') OR"\
			" tweet like (\'%AandW%\') OR"\
			" tweet like (\'%wendys%\') OR"\
			" tweet like (\'%subway%\') OR"\
			" tweet like (\'%timhortons%\') OR"\
			" tweet like (\'%tim hortons%\') OR"\
			" tweet like (\'%burgerking%\') OR"\
			" tweet like (\'%burger king%\') OR"\
			" tweet like (\'%taco bell%\') OR"\
			" tweet like (\'%tacobell%\') OR"\
			" tweet like (\'%dairyqueen%\') OR"\
			" tweet like (\'%dairy queen%\') OR"\
			" tweet like (\'%arbys%\') OR"\
			" tweet like (\'%icecream%\') OR"\
			" tweet like (\'%cola%\') OR"\
			" tweet like (\'%soda%\') OR"\
			" tweet like (\'%drpepper%\') OR"\
			" tweet like (\'%dr pepper%\') OR"\
			" tweet like (\'%vanilla-coke%\') OR"\
			" tweet like (\'%fresca%\') OR"\
			" tweet like (\'%mello yello%\') OR"\
			" tweet like (\'%mr pibb%\') OR"\
			" tweet like (\'%mrpibb%\') OR"\
			" tweet like (\'%pibb xtra%\') OR"\
			" tweet like (\'%pepsi%\') OR"\
			" tweet like (\'%mountaindew%\') OR"\
			" tweet like (\'%rootbeer%\') OR"\
			" tweet like (\'%7-up%\') OR"\
			" tweet like (\'%canadadry%\') OR"\
			" tweet like (\'%canada dry%\') OR"\
			" tweet like (\'%orangecrush%\') OR"\
			" tweet like (\'%creamsoda%\') OR"\
			" tweet like (\'%sunkist%\') OR"\
			" tweet like (\'%vernors%\') OR"\
			" tweet like (\'%chickenwings%\') OR"\
			" tweet like (\'%chicken wings%\') OR"\
			" tweet like (\'%buffalowings%\') OR"\
			" tweet like (\'%redbull%\') OR"\
			" tweet like (\'%red bull%\') OR"\
			" tweet like (\'%kitkat%\') OR"\
			" tweet like (\'%kit kat%\') OR"\
			" tweet like (\'%snickers%\') OR"\
			" tweet like (\'%crunchie%\') OR"\
			" tweet like (\'%3muskateers%\') OR"\
			" tweet like (\'%candybar%\') OR"\
			" tweet like (\'%reeses%\') OR"\
			" tweet like (\'%marsbar%\') OR"\
			" tweet like (\'%fried%\') OR"\
			" tweet like (\'%babyruth%\') OR"\
			" tweet like (\'%candy%\') OR"\
			" tweet like (\'%frosting%\') OR"\
			" tweet like (\'%crispy crunch%\') OR"\
			" tweet like (\'%crispycrunch%\') OR"\
			" tweet like (\'%ohhenry%\') OR"\
			" tweet like (\'%mrbig%\') OR"\
			" tweet like (\'%mr big%\') OR"\
			" tweet like (\'%coffeecrisp%\') OR"\
			" tweet like (\'%smarties%\') OR"\
			" tweet like (\'%oreo%\') OR"\
			" tweet like (\'%aero%\') OR"\
			" tweet like (\'%poprocks%\') OR"\
			" tweet like (\'%pop rocks%\') OR"\
			" tweet like (\'%pocky%\') OR"\
			" tweet like (\'%jawbreaker%\') OR"\
			" tweet like (\'%twizzler%\') OR"\
			" tweet like (\'%skittles%\') OR"\
			" tweet like (\'%tootsie roll%\') OR"\
			" tweet like (\'%tootsieroll%\') OR"\
			" tweet like (\'%jellybelly%\') OR"\
			" tweet like (\'%jelly belly%\') OR"\
			" tweet like (\'%jelly beans%\') OR"\
			" tweet like (\'%jellybean%\') OR"\
			" tweet like (\'%butterfinger%\') OR"\
			" tweet like (\'%twix%\') OR"\
			" tweet like (\'%hershey%\') OR"\
			" tweet like (\'%gummi%\') OR"\
			" tweet like (\'%coffee crisp%\') OR"\
			" tweet like (\'%oh henry%\') OR"\
			" tweet like (\'%fries%\') OR"\
			" tweet like (\'%potato chips%\') OR"\
			" tweet like (\'%butter%\') OR"\
			" tweet like (\'%pizza%\') OR"\
			" tweet like (\'%donut%\') OR"\
			" tweet like (\'%fruitloops%\') OR"\
			" tweet like (\'%potatochips%\') OR"\
			" tweet like (\'%nachos%\') OR"\
			" tweet like (\'%poutine%\') OR"\
			" tweet like (\'%fried%\') OR"\
			" tweet like (\'%mozerellasticks%\') OR"\
			" tweet like (\'%mozerella sticks%\') OR"\
			" tweet like (\'%corndog%\') OR"\
			" tweet like (\'%corn dog%\') OR"\
			" tweet like (\'%hotdog%\') OR"\
			" tweet like (\'%hot dog%\') OR"\
			" tweet like (\'%fried%\')"
			#" tweet like (\'%beer%\')"
		
		#limit = self.builder.get_object('CorpusLimit_Entry').get()
		#selectstring += " LIMIT "+limit
		#get data from postgres table	
		logging.info("executing select statement")
		curr.execute(selectstring)


		#create documents list
		logging.info("Starting GENSIM code")
		documents=[]
		logging.info("INCOMMING TWEET CORPUS SIZE: "+str(curr.rowcount))
		for tweet in curr:
			#tweet = str(curr.fetchone()[0])
			documents.append(' '.join(re.sub("(@[A-Za-z0-9]+)|([^0-9A-Za-z \t])|(\w+:\/\/\S+)|(gt)"," ",tweet[0]).split()).lower())
		#stopwords
		logging.info("CORPUS SIZE AFTER REGEX: "+str(len(documents)))
		

		#stoplist work
		s = ""
		for w in self.builder.get_object('TopicStopwords_Listbox').get(0,tk.END):
			s+=w+" "
		stoplist = set(s.split())
		#logging.info("s:\n\t"+s)
		#logging.info("stopwords"+str([i for i in self.builder.get_object('TopicStopwords_Listbox').get(0,tk.END)]))
		#logging.info(stoplist)
		
		#tokenize
		texts = [[word for word in document.lower().split() if word not in stoplist] for document in documents]		
		logging.info("CORPUS SIZE AFTER STOPLIST: "+str(len(texts)))	

		#singles reduction
		all_tokens = sum(texts, [])
		logging.info("beginning tokenization")
		tokens_once = set(word for word in set(all_tokens) if all_tokens.count(word) == 1)
		logging.info("words tokenized, starting single mentioned word reduction")
		texts = [[word for word in text if word not in tokens_once] for text in texts]
		logging.info("words mentioned only once removed")
		#remove nulls
		texts = filter(None,texts)
		logging.info("CORPUS SIZE AFTER EMPTY ROWS REMOVED: "+str(len(texts)))			
		dictionary = corpora.Dictionary(texts)
		
		#create corpus, tfidf, set up model
		corpus = [dictionary.doc2bow(text) for text in texts]
		tfidf = models.TfidfModel(corpus) #step 1. --initialize(train) a model
		corpus_tfidf = tfidf[corpus] # Apply TFIDF transform to entire corpus
		logging.info("starting LDA model")

		#run model
		tnum=int(self.builder.get_object('TopicParamTopics_Entry').get())
		topnval=int(self.builder.get_object('TopicParamWords_Entry').get())
		talpha = float(self.builder.get_object('TopicParamAlpha_Entry').get())
		tpasses = int(self.builder.get_object('TopicParamPasses_Entry').get())
		tupdate = int(self.builder.get_object('TopicParamUpdate_Entry').get())
		model = models.ldamodel.LdaModel(corpus_tfidf, id2word=dictionary, alpha=talpha, num_topics=tnum, update_every=tupdate, passes=tpasses)

		end = time.time()
		elapsed = end-start
		s= "\n\nProcess completed in %.2f minutes"%(elapsed/60)
		logging.info(s)
		
		# print diagnosgtic information
		print "\n\n\n\t\t\ttopics"
		print "\nSelect Statement: "+selectstring
		print "Corpus Size: "+ str(len(texts))
		m =(model.show_topics(num_topics=tnum, num_words=topnval, log=False,formatted=False))
		pp(m)
		

		#setup the columns of the treeview
		tree = self.builder.get_object('TopicModel_Treeview')
		colnum=0
		l =[]
		for c in range(0,tnum+1):
			s="col"+str(colnum)
			l.append(s)
			colnum+=1			
		tree['columns']=tuple(l)
		logging.info("tree[columns]:"+str(tree['columns']))
							
		#write model values to treeview
		a=0	
		tree.column('#0',width=5)
		for i in m:
			v = [ j[0]+str(round(j[1],4)) for j in i[1]]
			logging.info('inserting'+str(v))
			tree.insert('','end',text=str(a),values=v)
			a+=1

		for c in range(0,tnum+1):
			logging.info("settings for: col"+str(c))			
			tree.heading('#'+str(c),text="word "+str(c))
			tree.column('#'+str(c),stretch=tk.NO, width=30)
		tree.column('#11',width=5,stretch=tk.NO)
		# WHY DOES THIS 11TH COLUMN EXIST AT ALL (line 777?)
		#WHY IS THE WIDGET BECOMMING SO FUCKING WIDE!!!

	# --------------------------------
	# method:     	on_TopicModelLoad_button_click
	# description: 	load the json file at the location specified in the filename entry box
	# params:     	none
	# returns:    	none
	# --------------------------------
	def on_TopicModelLoad_button_click(self):
		pass
	# --------------------------------
	# method:     	on_TopicModelSave_button_click
	# description: 	load the json file at the location specified in the filename entry box
	# params:    	none
	# returns:    	none
	# --------------------------------
	def on_TopicModelSave_button_click(self):
		tree = self.builder.get_object('TopicModel_Treeview')
		d ={}
		for i in tree.get_children():
			d["topic"]=i
		pp(d)




# --------------------------------
# class:     GoogleKnowledgeGraph
# description: a class for handling requests to the google knowledge graph
# params:     none
# returns:    none
# --------------------------------
class GoogleKnowledgeGraph(object):
	#set initial params
	def __init__(self):
		self.api_key = open('k.key').read()
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




#program entry point
if __name__=='__main__':
	root = tk.Tk()
	app = Application(root)
	root.mainloop()


