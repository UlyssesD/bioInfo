# -*- coding: utf-8 -*-

#from django.shortcuts import render

# Create your views here.
from django.http import HttpResponse, JsonResponse

from neomodel import db
from .models import *
from .utils.configuration import TABLE_STRUCTURE, FIXED_FILTERS, DATA_FOLDER, CONVERTERS

import strconv
import json
import re
import pandas as panda

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
	file = getFile(username, experiment, filename)

	# ---- restituisco la risposta al client
	return JsonResponse(file.statistics)


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

# ---- Funzione che restituisce l'elenco dei valori sui quali filtrare le informazioni di un file
def filters(request, username, experiment, filename):
	
	# ---- inizializzo un dictionary per memorizzare i risultati
	response = {

 		'list': []
 	}

 	# ---- leggo il csv specificato dall'input
	keys = panda.read_csv(DATA_FOLDER + username + "_" + experiment + "_" + filename + ".types.data.gz", sep="\t", compression="infer")
	dictionary = panda.read_csv(DATA_FOLDER + username + "_" + experiment + "_" + filename + ".dictionary.data.gz", sep="\t", compression="infer")

	#data.columns = data.columns.str.strip().split(',')

	#print keys
	#print dictionary

	for index, row in keys.iterrows():

		if row.Type == "int" or row.Type == "float":
			response["list"].append({
					"label": row.Key,
					"type": "numeric",
					"min": None,
					"max": None
				})
		
		elif row.Type == "boolean":
			response["list"].append({
					"label": row.Key,
					"type": "boolean",
					"value": None
				})

		elif row.Type == "string":
			entries = dictionary[ dictionary["Key"] == row.Key ].iloc[:,1:].T.dropna()
			
			# print row.Key, ", empty?", entries.empty

			if not entries.empty:
				print "Number of entries for key:", len(entries.iloc[:,0])

			 	if len(entries.iloc[:,0]) <= 30:
					
			 		response["list"].append({
			 			"label": row.Key,
			 			"type": "select",
			 			"options": entries.iloc[:,0].tolist(),
			 			"value": None
			 		})

			 	else:
					
			 		response["list"].append({
			 			"label": row.Key,
			 			"type": "string",
			 			#"options": entries.iloc[:,0].tolist(),
			 			"value": None
			 		})
			else:

				response["list"].append({
					"label": row.Key,
					"type": "string",
					"value": None
				})

 	# ---- restituisco la risposta al client
 	return JsonResponse(response)

# ---- Funzione che restituisce le righe di un file da mostrare in tabella
def details(request, username, experiment, filename):

	# ---- inizializzo un dictionary per memorizzare i risultati
	response = {
		'count': 0,
		'header': [],
		'rows': []
	}

	# ---- ricavo dal file di configurazione la struttura della tabella per costruire la response
	#structure = TABLE_STRUCTURE[".vcf"]

	# ---- ricavo le informazioni dalla GET sulla paginazione (se disponibile)
	page = int(request.GET.get('page', 1))
	limit = int(request.GET.get('limit', response['count']))
	query_filters = request.GET.get('filters', None)

	#print query_filters
	# ---- costruisco la riga di header della tabella
	#for el in structure:
	#	response["header"].append(el["label"])


	# ---- leggo il csv specificato dall'input
	data = panda.read_csv(DATA_FOLDER + username + "_" + experiment + "_" + filename + ".data.gz", sep="\t", compression="infer")


	#response["count"] = len(data.index)
	filtered = data
	

	if query_filters:

		query_filters = json.loads(query_filters)
		#print query_filters
		for filt in query_filters['list']:
			
			#print filt["label"], "in list", filtered.columns.tolist(), "?", (filt["label"] in filtered.columns.tolist())

			#if filt["type"]  == 'numeric':
			#	filtered = filtered[( filtered[ filt["key"] ].map(lambda v: filt["min"]  <= v <= filt["max"] ) )]
			if filt["type"]  == 'string' or filt["type"] == 'select' or filt["type"] == 'autocomplete':
				if filt["value"]:
					print filt["label"], ", key term: ", filt["value"]
					filtered = filtered[( filtered[filt["label"] ].map(lambda v: filt["value"] in str(v).strip("[]").replace("'", "").replace(" ", "").split(',')) )]
			elif str(filt["type"])  == 'numeric':
				if filt["min"] or filt["max"]:
					filt["min"] = filt["min"] or -float('Inf')
					filt["max"] = filt["max"] or float('Inf')
					filtered = filtered[( filtered[ filt["label"] ].map(lambda v: any_in_range(v, filt["min"], filt["max"]) ) )]

			if filtered.empty:
				print "No result for selected filters."
				break

	#print filtered

	response["count"] = len(filtered.index)
	response["header"] = list(data.columns.values)
	#for el in filtered:
	#for el in data[(data['Gene.refGene'].map(lambda x: 'SOD1' in x)) & (data.POS >= 0)].iterrows():
	#	print el


	

	response["rows"] = filtered.where((panda.notnull(filtered)), None).sort_values(by=["CHROM","POS"])[(page - 1)*limit:min( response['count'], (page * limit) )].values.tolist()
	#print data.query('"KCNE1" in gene_refGene')
	#print data.gene_refGene.unique()


	return JsonResponse(response)

def any_in_list(array, value):
	
	res = False

	print value, "in",array.strip('[]').split(',')

	for v in str(array).strip('[]').split(','):
		res = res | (v == value)

	return res

def any_in_range(array, min, max):

	res = False

	for v in str(array).strip('[]').split(','):
			#print type(float(v)), (min <= float(v) <= max)
			res = res | (min <= float(v) <= max)

	return res