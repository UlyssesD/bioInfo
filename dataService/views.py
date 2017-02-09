# -*- coding: utf-8 -*-

#from django.shortcuts import render

# Create your views here.
from django.http import HttpResponse, JsonResponse

from neomodel import db
from .models import *
from .utils.configuration import TABLE_STRUCTURE

import json


# ----- Funzioni di utility -----

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

	# ---- costruisco la riga di header della tabella
	for el in structure:
		response["header"].append(el["label"])


	# ---- ricavo tutte le righe di un file per iterare sugli elementi
	annotations = file.contains.all()[(page - 1)*limit:min( response['count'], (page * limit) )]

	# ---- per ogni annotazione ricavo la variante associata e le colonne del genotipo
	for a in annotations:

		# ---- inizializzo un dictionary di supporto per ricostruire la riga
		row = {}

		# ---- ricavo la varianta a cui si riferisce l'annotazione
		variants = a.forVariant.all()

		for v in variants:
			
			# ---- ricavo le informazioni della riga del file per la variante contenute nell'arco
			v_infos = a.forVariant.relationship(v)

			#for key,value in v.__dict__.items():
			#	print key, ': ', value
			print type(v.ALT)

			# ---- memorizzo le informazioni sulla variante
			for key in ["CHROM", "POS", "REF", "ALT", "MUTATION"]:
				attr = getattr(v, key)
				row[key] = attr or "-"

			for key in ["END", "ID", "QUAL", "FILTER", "HETEROZIGOSITY", "dbSNP"]:
				attr = getattr(v_infos, key)
				print key, ": ", type(attr)
				row[key] = attr or "-"
			

		# ---- memorizzo le annotazioni della riga
		for key, value in a.attributes.items():
			print key, ": ", type(value)
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

	# ---- restituisco la risposta al client
	return JsonResponse(response)