# -*- coding: utf-8 -*-

#from django.shortcuts import render

# Create your views here.
from django.http import HttpResponse, JsonResponse

from neomodel import db
from .models import *

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
		'rows': []
	}

	# ---- ricavo il nodo corrispondente al file di interesse
	file = getFile(username, experiment, filename)


	response['count'] = file.statistics["total"]

	# ---- ricavo le informazioni dalla GET sulla paginazione (se disponibile)
	page = int(request.GET.get('page', 1))
	limit = int(request.GET.get('limit', response['count']))

	# ---- ricavo tutte le righe di un file per iterare sugli elementi
	annotations = file.contains.all()[(page - 1)*limit:min( response['count'], (page * limit) )]

	# ---- per ogni annotazione ricavo la variante associata e le colonne del genotipo
	for a in annotations:

		# ---- inizializzo un dictionary di supporto per ricostruire la riga
		row = {
			'variant': {},
			'annotation': {},
			'genotypes': []
		}

		# ---- ricavo la varianta a cui si riferisce l'annotazione
		variants = a.forVariant.all()

		for v in variants:
			
			# ---- ricavo le informazioni della riga del file per la variante contenute nell'arco
			v_infos = a.forVariant.relationship(v)

			# ---- memorizzo le informazioni sulla variante
			row['variant'] = {
				'CHROM': v.CHROM,
				'POS': v.POS,
				'REF': v.REF,
				'ALT': v.ALT,
				'MUTATION': v.MUTATION,
				'START': v_infos.START,
				'END': v_infos.END,
				'ID': v_infos.ID,
				'QUAL': v_infos.QUAL,
				'FILTER': v_infos.FILTER,
				'HETEROZIGOSITY': v_infos.HETEROZIGOSITY,
				'dbSNP': v_infos.dbSNP
			}

		# ---- memorizzo le annotazioni della riga
		row['annotation'] = a.attributes

		# ---- ricavo le informazioni sui genotipi per la riga
		genotypes = a.supportedBy.all()


		for g in genotypes:

			# ---- ricavo le informazioni della riga del file per il genotipo considerato riportate nell'arco
			g_infos = a.supportedBy.relationship(g)

			genotype = {
				'sample': g.sample,
				'phased': g_infos.phased,
				'state': g_infos.state
				}

			genotype.update(dict(g_infos.attributes))

			row['genotypes'].append(genotype)


		# ---- aggiungo la riga ricostruita alla risposta
		response['rows'].append(row)


	return JsonResponse(response)