# -*- coding: utf-8 -*-

#from django.shortcuts import render

# Create your views here.
from django.http import HttpResponse, JsonResponse

from neomodel import db
from .models import *
from .utils.configuration import TABLE_STRUCTURE, FIXED_FILTERS

import json
import re


# ----- Funzioni di utility -----

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

		'rows': []
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

		response['rows'].append(file)

	# ---- restituisco la risposta al client
	return JsonResponse(response)


# ---- Funzione che restituisce le statistiche di un file
def statistics(request, username, experiment, filename):

	# ---- ricavo il nodo corrispondente al file di interesse
	file = getFile(username, experiment, filename)

	# ---- restituisco la risposta al client
	return JsonResponse(file.statistics)


# ---- Funzione che restituisce l'elenco dei valori sui quali filtrare le informazioni di un file
def filters(request, username, experiment, filename):
	
	# ---- inizializzo un dictionary per memorizzare i risultati
	response = {
		'list': []
	}

	# ---- ricavo il nodo corrispondente al file di interesse
	file = getFile(username, experiment, filename)

	# ---- ricavo gli attributi fissi su cui filtrare (discriminando rispetto al formato del file)
	fixed = FIXED_FILTERS[file.extension]

	# ---- aggiungo i filtri fissi alla response
	response['list'] += fixed

	# ---- inizializzo una struttura dati per ricavare i filtri "generali"
	filters = {}

	# ---- ricavo tutte le righe di un file per iterare sugli elementi
	annotations = file.contains.all()

	# ---- per ogni annotazione inferisco il giusto filtro (se non già calcolato)
	for a in annotations:

		for key, value in a.attributes.items():
			
			if not filters.has_key(key):
				
				f = inferFilterFromType("Info", key, value)
				
				if not f["type"] == 'unknown':
					filters[key] = f

		# ---- prendo un genotipo di esempio
		g = a.supportedBy.all()[0]

		g_infos = a.supportedBy.relationship(g)

		for key, value in g_infos.attributes.items():
				
			if not filters.has_key("Genotype " + key):
					
				f = inferFilterFromType("SupportedBy", key, value)
				
				if not f["type"] == 'unknown':
					f["label"] = "Genotype " + key
					filters["Genotype " + key] = f

		# ---- ricavo le informazioni sui genotipi per la riga
		# genotypes = a.supportedBy.all()
		
		# for g in genotypes:

		# 	# ---- ricavo le informazioni della riga del file per il genotipo considerato riportate nell'arco
		# 	g_infos = a.supportedBy.relationship(g)

		# 	for key, value in g_infos.attributes.items():
				
		# 		if not filters.has_key("Genotype " + key):
					
		# 			f = inferFilterFromType(key, value)
					
		# 			if not f["type"] == 'unknown':
		# 				f["label"] = "Genotype " + key
		# 				filters["Genotype " + key] = f


	for key, value in filters.items():
		response['list'].append(value)


	# ---- restituisco la risposta al client
	return JsonResponse(response)

# ---- Funzione che restituisce le n righe di un file
def details(request, username, experiment, filename):


	# ---- inizializzo un dictionary per memorizzare i risultati
	response = {
		'count': 0,
		'header': [],
		'rows': []
	}

	# ---- ricavo il nodo corrispondente al file di interesse
	file = getFile(username, experiment, filename)

	# ---- ricavo dal file di configurazione la struttura della tabella per costruire la response
	structure = TABLE_STRUCTURE[file.extension]

	# ---- salvo il numero di righe totali
	response['count'] = file.statistics["total"]
	
	# ---- ricavo le informazioni dalla GET sulla paginazione (se disponibile)
	page = int(request.GET.get('page', 1))
	limit = int(request.GET.get('limit', response['count']))
	query_filters = request.GET.get('filters', None)
	# ---- inizializzo delle strutture dati per suddividere i filtri in base alla classe che li contiene (da usare nel seguito per filtrare i risultati)
	variant_filters = []
	for_variant_filters = []
	info_filters = []
	supported_by_filters = []
	genotype_filters = []

	# ---- se presenti, divido i filtri per categoria
	if query_filters:
		query_filters = json.loads(query_filters)
		for el in query_filters['list']:
			
			if el["container"] == "Variant":
				variant_filters.append(el)
			
			elif el["container"] == "ForVariant":
				for_variant_filters.append(el)
			
			elif el["container"] == "Info":
				info_filters.append(el)
			
			elif el["container"] == "SupportedBy":
				supported_by_filters.append(el)
			
			elif el["container"] == "Genotype":
				genotype_filters.append(el)



	# ---- costruisco la riga di header della tabella
	for el in structure:
		response["header"].append(el["label"])


	# ---- ricavo tutte le righe di un file per iterare sugli elementi
	annotations = file.contains.all()

	# ---- per ogni annotazione ricavo la variante associata e le colonne del genotipo
	for a in annotations:

		# ---- inizializzo un dictionary di supporto per ricostruire la riga
		row = {}
		row_discard = False

		# ---- ricavo la varianta a cui si riferisce l'annotazione
		variants = a.forVariant.all()

		for v in variants:
			
			# ---- eseguo un test per verificare se (qualora siano stati applicati filtri) sia possibile scartare la riga
			discard = False
			
			if variant_filters:
				discard = discardRow(variant_filters, v.__dict__)

				if discard:

					#print "v:", v, "skipped" 
					row_discard = True
					break

			# ---- ricavo le informazioni della riga del file per la variante contenute nell'arco
			v_infos = a.forVariant.relationship(v)

			#for key,value in v.__dict__.items():
			#	print key, ': ', value

			# ---- memorizzo le informazioni sulla variante
			for key in ["CHROM", "POS", "REF", "ALT", "MUTATION"]:
				attr = getattr(v, key)
				row[key] = attr or "-"

			for key in ["END", "ID", "QUAL", "FILTER", "HETEROZIGOSITY", "dbSNP"]:
				attr = getattr(v_infos, key)
				#print key, ": ", type(attr)
				row[key] = attr or "-"
			
		if row_discard:
			continue

		#print "Row:", row , "saved"
		# ---- memorizzo le annotazioni della riga
		for key, value in a.attributes.items():
			#print key, ": ", type(value)
			row[key] = value or '-'

		# ---- ricavo le informazioni sui genotipi per la riga
#		genotypes = a.supportedBy.all()


#		for g in genotypes:

			# ---- ricavo le informazioni della riga del file per il genotipo considerato riportate nell'arco
#			g_infos = a.supportedBy.relationship(g)

#			genotype = {
#				'sample': g.sample,
#				'phased': g_infos.phased,
#				'state': g_infos.state
#				}

#			genotype.update(dict(g_infos.attributes))

#			row['genotypes'].append(genotype)
		
		# ---- inizializzo un dizionario per costruire la riga della tabella
		table_row = []

		for el in structure:
			
			if el["type"] == "single":
				table_row.append(row[ el["params"] ] if row.has_key(el["params"]) else "-")
			
			elif el["type"] == "custom":
				
				template = str(el["template"])

				for param in el["params"]:
					template = template.replace(param, str(row[param]) )				
				
				table_row.append(template)


		# ---- aggiungo la riga ricostruita alla risposta
		response['rows'].append(table_row)
		response['count'] = len(response['rows'])

	print 'Row count: ', len(response['rows'])
	
	# ---- applico la paginazione per la response
	response['rows'] = response['rows'][(page - 1)*limit:min( response['count'], (page * limit) )]

	# ---- restituisco la risposta al client
	return JsonResponse(response)