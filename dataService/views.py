# -*- coding: utf-8 -*-

#from django.shortcuts import render

# Create your views here.
from django.http import HttpResponse, JsonResponse

from neomodel import db
from .models import *
from .utils.configuration import TABLE_STRUCTURE, FIXED_FILTERS, DATA_FOLDER, CONVERTERS, BLACKLIST

import gzip
import strconv
import json
import re
import pandas as panda
import urllib

HOST = "localhost"
PORT = "80"

# ----- Funzioni di utility -----

def processFilter(el):
	result = []
	
	if el["param_type"] == "numeric":
		if el["min"]:
			result.append({ el["param"] + "__gte": float(el["min"]) })
		if el["max"]:
			result.append({ el["param"] + "__lte": float(el["max"]) })
	elif el["param_type"] == "string":
		if el["value"]:
			result.append({ el["param"] + "__iexact": el["value"] })
	elif el["param_type"] == "lola":
		if el["value"]:
			result.append({ el["param"] + "__icontains": el["value"] })

	return result


def discardRow(filters, node):

	# ---- inizializzo la risposta da restituire
	discard = False

	#print filters

	# ---- per ogni filtro, verifico se il nodo la contiene e se verifica le proprietà specificate nel filtro
	for el in filters:
		#print "Value:", el["value"], "\tdeclared:", not el["value"] is "None", "\t string:", node[el["param"]], "\tsearch: ", re.search(el["value"], node[el["param"]], re.I | re.U)
		# --- se la chiave non è presente, scarta
		if  not node.has_key(el["param"]):
			print "Key", el["param"], "not present in", node
			discard = True
			break
		# --- se il tipo è stringa e non verifica la proprietà, scarta
		elif ( el["type"] == "string" ) and ( not el["value"] is None ) and ( not re.match(el["value"], node[el["param"]], re.I) ):
			discard = True
			break


	# ---- restituisco la risposta al metodo
	return discard

# ---- Metodo utilizzato per calcolare il filtro corretto per un attributo generico di un nodo
def inferFilterFromType(container, key, value):

	answer = {
		"container": container,
		"label": key,
		"param": key
	}

	if isinstance(value,list):
		t = type(value[0])
	else:
		t = type(value)

	#print key, ' type: ', t

	if t is str or t is unicode:

		#print "Returning string"
		answer['type'] = "string"
		answer['value'] = None

	elif t is int or t is float:
		
		#print "Returning numeric"
		answer['type'] = "numeric"
		answer['min'] = None
		answer['max'] = None

	elif t is bool:

		#print "Returning boolean"
		answer['type'] = "boolean"
		answer['value'] = None
	
	else:
		#print "Skipping value"
		answer['type'] = "unknown"

	return answer

# ---- Metodo utilizzato per ricavare velocemente uno specifico file (separato perchè usato più volte)
def getFile(username, experiment, filename):

	user = User.nodes.get(username=username)
	experiment = user.created.get(name=experiment)
	file = experiment.composedBy.get(name=filename)

	return file

# -------------------------------

def signup(request):

	response = {
		"status": None
	}

	data = json.loads(request.body)

	username = data["username"]
	password = data["password"]
	email = data["email"]

	print "Username:", username, "Password:", password, "e-mail:", email

	user_exists = User.nodes.get_or_none(username=username)

	if not user_exists:
		User(username=username, password=password, email=email).save()
		response["status"] = "Success"
	else:
		response["status"] = "Exists"

	print response
	return JsonResponse(response)

def login(request):

	response = {
		"status": None
	}

	data = json.loads(request.body)

	username = data["username"]
	password = data["password"]

	print "Username:", username, "Password:", password

	user_exists = User.nodes.get_or_none(username=username, password=password)

	if user_exists:
		response["status"] = "Success"
	else:
		response["status"] = "Mismatch"
		
	print response
	return JsonResponse(response)

# ---- Funzione per restituire l'elenco dei cromosomi presenti nel database
def chromosomes(request):

	# ---- inizializzo un dictionary per memorizzare i risultati
	response =  {
		"elements": [
			{
				"option": "-- All --",
				"value": None
			}
		]
	}


	# ---- ricavo tutti i nodi cromosoma nel database
	for chrom in Chromosome.nodes.order_by('chromosome'):
		response["elements"].append(
			{
				"option": chrom.chromosome,
				"value": chrom.chromosome
			})

	# ---- restituisco la risposta al client
	return JsonResponse(response)

# ---- Funzione per restituire l'elenco delle location presenti nel database
def locations(request):

	# ---- inizializzo un dictionary per memorizzare i risultati
	response =  {
		"elements": [
			{
				"option": "-- All --",
				"value": None
			}
		]
	}

	# ---- inizializzo un insieme per costruire l'elenco delle possibili location
	temp = set()

	# ---- ricavo tutti i nodi cromosoma nel database
	for info in Info.nodes.all():
		
		for loc in info.Func_refGene:
			if loc not in temp:

				temp.add(loc)

				response["elements"].append(
					{
						"option": loc,
						"value": loc
					}
				)

	# ---- restituisco la risposta al client
	return JsonResponse(response)

# ---- Funzione che restituisce l'elenco dei geni presenti nel database
def genes(request):

	query_term = str(request.GET.get('q', None))
	
	# ---- inizializzo un dictionary per memorizzare i risultati
	response = {
		"elements": []
	}


	# ---- ricavo tutti i nodi gene nel database
	for gene in Gene.nodes.filter(gene_id__istartswith=query_term).order_by('gene_id'):
		response["elements"].append(gene.gene_id)

	return JsonResponse(response)


# ---- Funzione che restituisce tutti gli esperimenti (progetti) di un utente
def experiments(request, username):

	# ---- inizializzo un dictionary per memorizzare i risultati
	response = {

		'rows': []
	}

	# ---- ricavo tutti gli esperimenti associati ad un utente
	user = User.nodes.get(username=username)
	experiments = user.created.all()

	# ---- per ogni esperimento, ricavo la specie ed il numero di file di cui è composto
	for e in experiments:

		print e
		
		experiment = {
			'name': e.name,
			'species': e.forSpecies.all()[0].species,
			'files': len(e.composedBy.all())
		}

		response['rows'].append(experiment)

	# ---- restituisco la risposta al client
	return JsonResponse(response)


# ---- Funzione che restituisce tutti i file che appartengono ad uno specifico esperimento
def files(request, username, experiment):

	# ---- inizializzo un dictionary per memorizzare i risultati
	response = {

		'elements': []
	}

	# ---- ricavo l'esperimento di interesse
	user = User.nodes.get(username=username)
	experiment = user.created.get(name=experiment)

	# ---- ricavo i file che fanno parte dell'esperimento selezionato
	files = experiment.composedBy.all()

	for f in files:

		file = {
			'filename': f.name,
			'extension': f.extension
		}

		response['elements'].append(file)

	# ---- restituisco la risposta al client
	return JsonResponse(response)


# ---- Funzione che restituisce le statistiche di un file
def statistics(request, username, experiment, filename):

	# ---- ricavo il nodo corrispondente al file di interesse
	#file = getFile(username, experiment, filename)
	response = {
		"elems": []
	}

	stats = panda.read_csv(DATA_FOLDER + username + "_" + experiment + "_" + filename + ".stats.gz", sep="\t", compression="infer")

	print stats

	keys = stats.columns.values

	for row in stats.values.tolist():
		for idx in range(len(keys)):
			response["elems"].append({
				"name": keys[idx],
				"value": row[idx]
			})
	
	print response
	# ---- restituisco la risposta al client
	#return JsonResponse(file.statistics)
	return JsonResponse(response)

# ---- Funzione che restituisce l'elenco dei valori sui quali filtrare le informazioni di un file
# def filters(request, username, experiment, filename):
	
# 	# ---- inizializzo un dictionary per memorizzare i risultati
# 	response = {
# 		'list': []
# 	}

# 	# ---- ricavo il nodo corrispondente al file di interesse
# 	file = getFile(username, experiment, filename)

# 	# ---- ricavo gli attributi fissi su cui filtrare (discriminando rispetto al formato del file)
# 	fixed = FIXED_FILTERS[file.extension]

# 	# ---- aggiungo i filtri fissi alla response
# 	response['list'] += fixed

# 	# ---- inizializzo una struttura dati per ricavare i filtri "generali"
# 	#filters = {}

# 	# ---- ricavo tutte le righe di un file per iterare sugli elementi
# 	#annotations = file.contains.all()

# 	# ---- per ogni annotazione inferisco il giusto filtro (se non già calcolato)
# 	#for a in annotations:

# 		#for key, value in a.attributes.items():
			
# 			#if not filters.has_key(key):
				
# 				#f = inferFilterFromType("Info", key, value)
				
# 				#if not f["type"] == 'unknown':
# 				#	filters[key] = f

# 		# ---- prendo un genotipo di esempio
# 		#g = a.supportedBy.all()[0]

# 		#g_infos = a.supportedBy.relationship(g)

# 		#for key, value in g_infos.attributes.items():
				
# 			#if not filters.has_key("Genotype " + key):
					
# 				#f = inferFilterFromType("SupportedBy", key, value)
				
# 				#if not f["type"] == 'unknown':
# 					#f["label"] = "Genotype " + key
# 					#filters["Genotype " + key] = f

# 		# ---- ricavo le informazioni sui genotipi per la riga
# 		# genotypes = a.supportedBy.all()
		
# 		# for g in genotypes:

# 		# 	# ---- ricavo le informazioni della riga del file per il genotipo considerato riportate nell'arco
# 		# 	g_infos = a.supportedBy.relationship(g)

# 		# 	for key, value in g_infos.attributes.items():
				
# 		# 		if not filters.has_key("Genotype " + key):
					
# 		# 			f = inferFilterFromType(key, value)
					
# 		# 			if not f["type"] == 'unknown':
# 		# 				f["label"] = "Genotype " + key
# 		# 				filters["Genotype " + key] = f


# 	#for key, value in filters.items():
# 		#response['list'].append(value)


# 	# ---- restituisco la risposta al client
# 	return JsonResponse(response)

# ---- Funzione che restituisce le n righe di un file
# def details(request, username, experiment, filename):


# 	# ---- inizializzo un dictionary per memorizzare i risultati
# 	response = {
# 		'count': 0,
# 		'header': [],
# 		'rows': []
# 	}

# 	# ---- ricavo il nodo corrispondente al file di interesse
# 	file = getFile(username, experiment, filename)

# 	# ---- ricavo dal file di configurazione la struttura della tabella per costruire la response
# 	structure = TABLE_STRUCTURE[file.extension]

# 	# ---- salvo il numero di righe totali
# 	response['count'] = file.statistics["total"]
	
# 	# ---- ricavo le informazioni dalla GET sulla paginazione (se disponibile)
# 	page = int(request.GET.get('page', 1))
# 	limit = int(request.GET.get('limit', response['count']))
# 	query_filters = request.GET.get('filters', None)
# 	# ---- inizializzo delle strutture dati per suddividere i filtri in base alla classe che li contiene (da usare nel seguito per filtrare i risultati)
# 	variant_filters = {
# 		"single": [],
# 		"list": []
# 	}
# 	for_variant_filters = {
# 		"single": [],
# 		"list": []
# 	}
# 	info_filters = {
# 		"single": [],
# 		"list": []
# 	}
# 	supported_by_filters = {
# 		"single": [],
# 		"list": []
# 	}

# 	# ---- se presenti, divido i filtri per categoria
# 	if query_filters:
# 		query_filters = json.loads(query_filters)
# 		for el in query_filters['list']:
			
# 			if el["container"] == "Variant":
# 				if el["param_type"] != "list":
# 					variant_filters["single"] = variant_filters["single"]  + processFilter(el)
# 				else:
# 					if el["value"]:
# 						variant_filters["list"] = variant_filters["list"]  + [el]

			
# 			elif el["container"] == "ForVariant":
# 				if el["param_type"] != "list":
# 					for_variant_filters["single"] = for_variant_filters["single"] + processFilter(el)
# 				else:
# 					if el["value"]:
# 						for_variant_filters["list"] = for_variant_filters["list"] + [el]
			
# 			elif el["container"] == "Info":
# 				if el["param_type"] != "list":
# 					info_filters["single"] = info_filters["single"] + processFilter(el)
# 				else:
# 					if el["value"]:
# 						info_filters["list"] = info_filters["list"] + [el]
			
# 			elif el["container"] == "SupportedBy":
# 				if el["param_type"] != "list":
# 					supported_by_filters["single"] = supported_by_filters["single"] + processFilter(el)
# 				else:
# 					if el["value"]:
# 						supported_by_filters["list"] = supported_by_filters["list"] + [el]



# 	# ---- costruisco la riga di header della tabella
# 	for el in structure:
# 		response["header"].append(el["label"])


# 	# ---- ricavo tutte le righe di un file per iterare sugli elementi
# 	annotations = file.contains

# 	#print "Filter on annotations:", info_filters
# 	for i_f in info_filters["single"]:
# 		annotations = annotations.filter(**i_f)

# 	# ---- per ogni annotazione ricavo la variante associata e le colonne del genotipo
# 	for a in annotations:
		
# 		skip = False

# 		for i_f in info_filters["list"]:

# 			if i_f["value"] not in a.__dict__[i_f["param"]]:
# 				skip = True
# 				break
		
# 		if skip:
# 			continue

# 		# ---- inizializzo un dictionary di supporto per ricostruire la riga
# 		row = {}
# 		row_discard = False

# 		# ---- ricavo la varianta a cui si riferisce l'annotazione
# 		variants = a.forVariant

# 		#print "Filter on variant:", variant_filters

# 		for vf in variant_filters["single"]:
# 			variants = variants.filter(**vf)

# 		if len(variants) == 0:
# 			continue

# 		for v in variants:
			

# 			skip = False

# 			for v_f in variant_filters["list"]:

# 				if v_f["value"] not in v.__dict__[v_f["param"]]:
# 					skip = True
# 					break
		
# 			if skip:
				
# 				row_discard = True
# 				break
# 			# ---- eseguo un test per verificare se (qualora siano stati applicati filtri) sia possibile scartare la riga
# 			#discard = False
			
# 			#if variant_filters:
# 			#	discard = discardRow(variant_filters, v.__dict__)

# 			#	if discard:

# 					#print "v:", v, "skipped" 
# 			#		row_discard = True
# 			#		break

# 			# ---- ricavo le informazioni della riga del file per la variante contenute nell'arco
			

# 			#for key,value in v.__dict__.items():
# 			#	print key, ': ', value

# 			# ---- memorizzo le informazioni sulla variante
# 			for key in ["CHROM", "POS", "REF", "ALT", "MUTATION"]:
# 				attr = getattr(v, key)
# 				row[key] = attr or "-"

			
# 		if row_discard:
# 			continue

# 		#print "Row:", row , "saved"
# 		# ---- memorizzo le annotazioni della riga
# 		for key in ["DP", "Gene_refGene", "Func_refGene", "QD", "SIFT_score", "otg_all", "NM", "LM", "FS", "MQ0", "END", "ID", "QUAL", "FILTER", "HETEROZIGOSITY", "dbSNP"]:
# 			attr = getattr(a, key)
# 			row[key] = attr or '-'

# 		#for key, value in a.attributes.items():
# 			#print key, ": ", type(value)
# 		#	row[key] = value or '-'

# 		# ---- ricavo le informazioni sui genotipi per la riga
# 		genotypes = a.supportedBy
# 		#print "Filters for Genotypes:", supported_by_filters
# 		for sbf in supported_by_filters["single"]:
# 			genotypes = genotypes.match(**sbf)

# 		# ---- verifico (se presenti) che siano verificate le proprietà rispetto i genotipi
# 		if len(genotypes) == 0:
# 			continue
		

# #		for g in genotypes:

# 			# ---- ricavo le informazioni della riga del file per il genotipo considerato riportate nell'arco
# #			g_infos = a.supportedBy.relationship(g)

# #			genotype = {
# #				'sample': g.sample,
# #				'phased': g_infos.phased,
# #				'state': g_infos.state
# #				}

# #			genotype.update(dict(g_infos.attributes))

# #			row['genotypes'].append(genotype)
		
# 		# ---- inizializzo un dizionario per costruire la riga della tabella
# 		table_row = []

# 		for el in structure:
			
# 			if el["type"] == "single":
# 				table_row.append(row[ el["params"] ] if row.has_key(el["params"]) else "-")
			
# 			elif el["type"] == "custom":
				
# 				template = str(el["template"])

# 				for param in el["params"]:
# 					template = template.replace(param, str(row[param]) )				
				
# 				table_row.append(template)


# 		# ---- aggiungo la riga ricostruita alla risposta
# 		response['rows'].append(table_row)
# 		response['count'] = len(response['rows'])

# 	print 'Row count: ', len(response['rows'])
	
# 	# ---- applico la paginazione per la response
# 	response['rows'] = response['rows'][(page - 1)*limit:min( response['count'], (page * limit) )]

# 	# ---- restituisco la risposta al client
# 	return JsonResponse(response)

def search(request, key):

	# ---- inizializzo un dictionary per memorizzare i risultati
	response = {

		'options': []
	}

	data = json.loads(request.body)

	username = data["username"]
	experiment = data["experiment"]
	filename = data["file"]
	term = data["term"].lower()

	print username, experiment, file, key, term

	dictionary = panda.read_csv(DATA_FOLDER + username + "_" + experiment + "_" + filename + ".dictionary.data.gz", sep="\t", compression="infer")
	dictionary.drop(dictionary[(dictionary["Key"].map(lambda k: k in BLACKLIST))].index.tolist(), axis=0, inplace=True)

	entries = dictionary[(dictionary["Key"] == key)].iloc[:,1:].T.dropna()
	response["options"] = entries.iloc[:,0].tolist()
	#print entries
	#response["options"] = entries[(entries.iloc[:,0].map(lambda entry: entry.lower().startswith(term)))].iloc[:,0].tolist()

	#response["options"].sort()
	#if len(response["options"]) > 0:
	#	response["options"] = response["options"]

 	#print response["options"]
	# ---- restituisco la risposta al client
 	return JsonResponse(response)

# ---- Funzione che restituisce l'elenco dei valori sui quali filtrare le informazioni di un file
def filters(request, username, experiment, filename):
	
	# ---- inizializzo un dictionary per memorizzare i risultati
	response = {

 		'list': []
 	}

 	# ---- leggo il csv specificato dall'input
	keys = panda.read_csv(DATA_FOLDER + username + "_" + experiment + "_" + filename + ".types.data.gz", sep="\t", compression="infer")
	dictionary = panda.read_csv(DATA_FOLDER + username + "_" + experiment + "_" + filename + ".dictionary.data.gz", sep="\t", compression="infer")

	# ---- rimuovo dal dataset (se esistono) tutte le chiavi che sono presenti nella BLACKLIST
	keys.drop(keys[(keys["Key"].map(lambda k: k in BLACKLIST))].index.tolist(), axis=0, inplace=True)
	dictionary.drop(dictionary[(dictionary["Key"].map(lambda k: k in BLACKLIST))].index.tolist(), axis=0, inplace=True)
	
	#print keys
	#print dictionary

	for index, row in keys.iterrows():

		if row.Type == "int" or row.Type == "float":
			response["list"].append({
					"label": row.Key,
					"type": "numeric",
					"importance": 4,
					"length": 0,
					"min": None,
					"max": None
				})
		
		elif row.Type == "boolean":
			response["list"].append({
					"label": row.Key,
					"type": "boolean",
					"length": 0,
					"importance": 2,
					"value": None
				})

		elif row.Type == "string":
			entries = dictionary[ dictionary["Key"] == row.Key ].iloc[:,1:].T.dropna()
			
			# print row.Key, ", empty?", entries.empty

			if not entries.empty:
				print "Number of entries for key", row.Key, ":", len(entries.iloc[:,0])

			 	if len(entries.iloc[:,0]) <= 30:
					
			 		response["list"].append({
			 			"label": row.Key,
			 			"type": "select",
			 			"importance": 1,
			 			"length": len(entries.iloc[:,0]),
			 			"options": sorted(entries.iloc[:,0].tolist()),
			 			"value": None
			 		})

			 	else:
					
			 		response["list"].append({
			 			"label": row.Key,
			 			"type": "autocomplete",
			 			"importance": 3,
			 			"length": len(entries.iloc[:,0]),
			 			"url": "http://" + HOST + ":" + PORT + "/dataService/search/" + urllib.quote(row.Key, safe='') + "/",
			 			"options": entries.iloc[:,0].tolist(),
			 			"value": None
			 		})
			else:

				response["list"].append({
					"label": row.Key,
					"type": "string",
					"importance": 5,
					"length": 0,
					"value": None
				})

 	# ---- restituisco la risposta al client
 	return JsonResponse(response)

# ---- Funzione che restituisce le righe di un file da mostrare in tabella
def count(request, username, experiment, filename):

	# ---- inizializzo un dictionary per memorizzare i risultati
	response = {
		'count': 0,
	}

	# ---- ricavo dal file di configurazione la struttura della tabella per costruire la response
	#structure = TABLE_STRUCTURE[".vcf"]

	data = json.loads(request.body)
	
	first = max(data["first"] - 1, 1) or 1
	query_filters = data["filters"] or None

	print "POST params = { first:", str(first), "}"

	# ---- ricavo le informazioni dalla GET sulla paginazione (se disponibile)
	#page = int(request.body.get('page', 100))
	#limit = int(request.body.get('limit', 200))
	#last = int(request.body.get('last', 100))
	#query_filters = request.body.get('filters', "lallero")

	with gzip.open(DATA_FOLDER + username + "_" + experiment + "_" + filename + ".data.gz", 'r') as f:
		header = f.readline().rstrip().split('\t')


	# ---- leggo il csv specificato dall'input
	keys = panda.read_csv(DATA_FOLDER + username + "_" + experiment + "_" + filename + ".types.data.gz", sep="\t", compression="infer")
	
	# ---- rimuovo dal dataset (se esistono) tutte le chiavi che sono presenti nella BLACKLIST
	keys.drop(keys[(keys["Key"].map(lambda k: k in BLACKLIST))].index.tolist(), axis=0, inplace=True)

	# ---- ricavo dalla lista dei tipi quelli che hannno tipo booleano (per rimpiazzare i valori "NaN" con "False")
	keys = keys[keys["Type"] == "boolean"]

	# ---- leggo il csv specificato dall'input
	chunksize = 100000
	chunks = panda.read_csv(DATA_FOLDER + username + "_" + experiment + "_" + filename + ".data.gz", sep="\t", names=header, skiprows=first, chunksize=chunksize, compression="infer")

	if query_filters:
		filters_frame = panda.DataFrame(data=query_filters['list'])
		#filters_frame = filters_frame[(panda.notnull(filters_frame["min"])) | (panda.notnull(filters_frame["max"])) | (panda.notnull(filters_frame["value"]))]
		filters_frame.dropna(inplace=True, thresh=5)
		filters_frame.sort_values(["importance", "length"], ascending=[True, False], inplace=True)


		print filters_frame

	for data in chunks:
		# ---- elimino dal dataset le colonne (se presenti) marcate nella blacklist
		data.drop(BLACKLIST, axis=1, inplace=True, errors="ignore")

		if len(keys.index) > 0:
			for key in keys.values.tolist():
				data[key[0]] = data[key[0]].fillna(False, inplace=True)


		#response["count"] = len(data.index)
		filtered = data

		if query_filters and len(filters_frame.index) > 0:
		#if query_filters:

			#print query_filters
			for filt in filters_frame.where((panda.notnull(filters_frame)), None).values.tolist():
				print filt
			#for filt in query_filters['list']:
					
				#print filt["label"], "in list", filtered.columns.tolist(), "?", (filt["label"] in filtered.columns.tolist())

				#if filt["type"]  == 'numeric':
				#	filtered = filtered[( filtered[ filt["key"] ].map(lambda v: filt["min"]  <= v <= filt["max"] ) )]
				if filt[5] == 'boolean':
					filtered = filtered[(filtered[ filt[1] ] == filt[6] )]
				elif filt[5]  == 'string' or filt[5] == 'select' or filt[5] == 'autocomplete':
					#if filt[6]:
					#print filt[1], ", key term: ", filt[6]
					filtered = filtered[( filtered[filt[1] ].map(lambda v: filt[6].lower() in str(v).lower().strip("[]").replace("'", "").replace(" ", "").split(',')) )]
				elif filt[5]  == 'numeric':
					filt[4] = float(filt[4]) if filt[4] is not None  else -float('Inf')
					filt[3] = float(filt[3]) if filt[3] is not None  else float('Inf')
					#print "min:", filt[4], "max:", filt[3]
					
					filtered = filtered[( filtered[ filt[1] ].map(lambda v: any_in_range(v, filt[4], filt[3]) ) )]

				if filtered.empty:
					print "No result for selected filters."
					break

		if filtered.empty:
			continue

		response["count"] = response["count"] + len(filtered.index)



	return JsonResponse(response)


# ---- Funzione che restituisce le righe di un file da mostrare in tabella
def details(request, username, experiment, filename):

	# ---- inizializzo un dictionary per memorizzare i risultati
	response = {
		'first': 1,
		'last': 1,
		'count': 0,
		'header': [],
		'show_header': [],
		'active_filters': [],
		'rows': []
	}

	# ---- ricavo dal file di configurazione la struttura della tabella per costruire la response
	#structure = TABLE_STRUCTURE[".vcf"]

	data = json.loads(request.body)



	limit = data["limit"] or 10
	last = data["last"] or 1
	query_filters = data["filters"] or None

	# ---- ricavo le informazioni dalla GET sulla paginazione (se disponibile)
	#page = int(request.body.get('page', 100))
	#limit = int(request.body.get('limit', 200))
	#last = int(request.body.get('last', 100))
	#query_filters = request.body.get('filters', "lallero")

	#print request.body
	print "POST params = { limit:", str(limit) + ", last:", str(last), "}"#, query_filters
	#print query_filters
	# ---- costruisco la riga di header della tabella
	#for el in structure:
	#	response["header"].append(el["label"])

	with gzip.open(DATA_FOLDER + username + "_" + experiment + "_" + filename + ".data.gz", 'r') as f:
		header = f.readline().rstrip().split('\t')


	# ---- leggo il csv specificato dall'input
	keys = panda.read_csv(DATA_FOLDER + username + "_" + experiment + "_" + filename + ".types.data.gz", sep="\t", compression="infer")
	
	# ---- rimuovo dal dataset (se esistono) tutte le chiavi che sono presenti nella BLACKLIST
	keys.drop(keys[(keys["Key"].map(lambda k: k in BLACKLIST))].index.tolist(), axis=0, inplace=True)

	# ---- ricavo dalla lista dei tipi quelli che hannno tipo booleano (per rimpiazzare i valori "NaN" con "False")
	keys = keys[keys["Type"] == "boolean"]

	print keys
	# ---- leggo il csv specificato dall'input
	chunksize = 100000
	chunk_number = 0
	chunks = panda.read_csv(DATA_FOLDER + username + "_" + experiment + "_" + filename + ".data.gz", sep="\t", names=header, skiprows=last, chunksize=chunksize, compression="infer")



	if query_filters:
		filters_frame = panda.DataFrame(data=query_filters['list'])
		#lola = filters_frame[(panda.notnull(filters_frame["min"])) | (panda.notnull(filters_frame["max"])) | (panda.notnull(filters_frame["value"]))]
		filters_frame.dropna(inplace=True, thresh=5)
		filters_frame.sort_values(["importance", "length"], ascending=[True, False], inplace=True)

		

		for f in filters_frame.where((panda.notnull(filters_frame)), None).values.tolist():
			
			if f[5] == "numeric":

				if f[4] is not None:
					response["active_filters"].append({
					"name": f[1],
					"var": "min",
					"value": ">=" + str(f[4])
					})
				if f[3] is not None:
					response["active_filters"].append({
					"name": f[1],
					"var": "max",
					"value": "<=" + str(f[3])
					})
			else:
				response["active_filters"].append({
					"name": f[1],
					"var": "value",
					"value": "=" + str(f[6])
					})
				
		print filters_frame

	for data in chunks:
		# ---- elimino dal dataset le colonne (se presenti) marcate nella blacklist
		data.drop(BLACKLIST, axis=1, inplace=True, errors="ignore")

		if len(keys.index) > 0:
			for key in keys.values.tolist():
				data[key[0]] = data[key[0]].fillna(False, inplace=True)


		#response["count"] = len(data.index)
		filtered = data

		if query_filters and len(filters_frame.index) > 0:
		#if query_filters:

			#print query_filters
			for filt in filters_frame.where((panda.notnull(filters_frame)), None).values.tolist():
			#for filt in query_filters['list']:
					
				#print filt["label"], "in list", filtered.columns.tolist(), "?", (filt["label"] in filtered.columns.tolist())

				#if filt["type"]  == 'numeric':
				#	filtered = filtered[( filtered[ filt["key"] ].map(lambda v: filt["min"]  <= v <= filt["max"] ) )]
				if filt[5] == 'boolean':
					filtered = filtered[(filtered[ filt[1] ] == filt[6] )]
				elif filt[5]  == 'string' or filt[5] == 'select' or filt[5] == 'autocomplete':
					#if filt[6]:
					#print filt[1], ", key term: ", filt[6]
					filtered = filtered[( filtered[filt[1] ].map(lambda v: filt[6].lower() in str(v).lower().strip("[]").replace("'", "").replace(" ", "").split(',')) )]
				elif filt[5] == 'numeric':
					#if filt[4] or filt[3]:

						filt[4] = filt[4] if filt[4] is not None  else -float('Inf')
						filt[3] = filt[3] if filt[3] is not None  else float('Inf')
						filtered = filtered[( filtered[ filt[1] ].map(lambda v: any_in_range(v, filt[4], filt[3]) ) )]

				if filtered.empty:
					print "No result for selected filters."
					break

		if filtered.empty:
			chunk_number = chunk_number + 1
			continue

		rows = filtered.where((panda.notnull(filtered)), None).values.tolist()
		indexes = filtered.index.tolist()

		for idx in range(len(rows)):

			for i in range(len(rows[idx])):
				if isinstance(rows[idx][i], str):
					rows[idx][i] = rows[idx][i].replace("'", "").strip('[]').split(',')

			response["rows"].append(rows[idx])

			if len(response["rows"]) == 1:
				response["first"] = last + indexes[idx]

			if len(response["rows"]) == limit:
				response["last"] = last + indexes[idx] + 1 # + chunk_number * chunksize 
				break

		#print filtered.index.tolist()

		response["header"] = list(data.columns.values)

		if len(response["rows"]) == limit:
			break

		chunk_number = chunk_number + 1
		#response["rows"] = response["rows"] + filtered.where((panda.notnull(filtered)), None).values.tolist()
		#response["count"] = response["count"] + len(filtered.index)
		#break
	#for el in filtered:
	#for el in data[(data['Gene.refGene'].map(lambda x: 'SOD1' in x)) & (data.POS >= 0)].iterrows():
	#	print el

	#response["rows"] = response["rows"][(page - 1)*limit:min( response['count'], (page * limit) )]
	#print "Last row selected:", response['last']

	#response["rows"] = filtered.where((panda.notnull(filtered)), None).values.tolist()
	#print data.query('"KCNE1" in gene_refGene')
	#print data.gene_refGene.unique()
	

	response["show_header"] = [True]*8 + [False]*(len(response["header"]) - 8)
	response["count"] = len(response["rows"])

	print "last:", response["last"]

	return JsonResponse(response)

def any_in_list(array, value):
	
	res = False

	#print value, "in",array.strip('[]').split(',')

	for v in str(array).strip('[]').split(','):
		res = res | (v == value)

	return res

def any_in_range(array, min, max):

	res = False
	
	for v in str(array).strip('[]').split(','):
			#print v
			res = res | (min <= float(v) <= max)

	return res