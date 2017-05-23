# !/usr/bin/env python   # Script python per il parsing di file in formato VCF da inserire in Neo4j
# -*- coding: utf-8 -*-

import pandas as pd
import re
import csv
import gzip
import uuid
import sys, os
from collections import OrderedDict


# ----- Funzioni ausiliarie -----
def addType(key, type, TYPES):

	if not TYPES.has_key(key):
		TYPES[key] = type


def addEntryToDict(key, value, DICTIONARY):
	if not DICTIONARY.has_key(key):
		DICTIONARY[key] = set([value])
	else:
		DICTIONARY[key].update([value])


def inferType(key, array, TYPES, DICTIONARY):
	
	for i in range(len(array)):

		if re.match('^-?(\d)+\.(\d)+(e[+-]\d+)?$', array[i].strip()):
			
			addType(key, "float", TYPES)
			array[i] = float(array[i].strip())

		elif re.match('-?^(\d)+$', array[i].strip()):
			
			addType(key, "int", TYPES)
			array[i] = int(array[i].strip())

		else:
			addType(key, "string", TYPES)
			addEntryToDict(key, array[i], DICTIONARY)

	return array


def main(argv):  
	
	# ---- VARIABILI DEL METODO

	ROWS = []						# memorizza le righe del file vcf

	# utilizzato per memorizzare le colonne del file finale
	HEADERS = [ "seqname", "source", "feature", "start", "end", "score", "strand", "frame", "gene_id", "transcript_id" ]
	
	# utilizzato per memorizzare i valori dei campi stringa del file (utile lato client per generare le select e le autocomplete)
	DICTIONARY = {
		"frame": set(["0", "1", "2"])
	}

	# utilizzato per memorizzare i tipi dei campi presenti nel file (utile lato client per la generazione dei form)					
	TYPES = {}						


	STATS_HEADER = ["total", ]
	STATS = {
		"total": 0,
		
	}

	# ---- ricavo le informazioni dalla riga di comando
	input_file = argv[0] 	# ---- nome del file vcf di input
	temp_folder = argv[1]	# ---- cartella temporanea per memorizzare i csv parziali
	data_folder = argv[2]	# ---- cartella dove memorizzare il file csv finale
	username =  argv[3]		# ---- nome utente del proprietario del file
	experiment = argv[4]	# ---- esperimento a cui il file appartiene
	species = argv[5]		# ---- specie del file passato in input
	file_id = argv[6] or str(uuid.uuid4())
	# ---- Apro il file vcf
	print 'Opening .gtf file...'
	file = open(input_file, 'r')
	
	#reader = vcf.Reader(file, encoding='utf-8')

	
	print 'Starting parsing procedure for file ' + os.path.basename(file.name)


	row_count = 0 

	# ---- aggiungo i tipi per i valori fissi del file
	for entry in [("seqname", "string"), ("source", "string"), ("feature", "string"), ("start", "int"), ("end", "int"), ("score", "float"), ("strand", "string"), ("frame", "string"), ("gene_id", "string"), ("transcript_id", "string")]:
		addType(entry[0], entry[1], TYPES)

	print "Scanning headers of output file"

	# ---- leggo una prima volta il file per intero per calcolare tutti gli header del file csv finale
	for line in iter(file):

		# ---- salto gli header del file
		if re.match("^#.*", line):
			print "IGNORING LINE"
			continue

		row_count += 1

		# ---- comincio a parsare le informazioni della riga
		values = line.split('\t')

		# ---- ottengo la lista delle annotazioni della riga
		attributes = values[8].split(';')

		for element in attributes:

			# ---- divido ogni annotazione come una coppia chiave - valore
			key, value = (element.strip(' \n').split(' ') + [None]*2)[:2]

			if key != '' and (key not in HEADERS):
				HEADERS.append(key)
				
		sys.stdout.write("%d lines scanned %s"%(row_count,"\r"))
		sys.stdout.flush();


	sys.stdout.write("%d lines scanned %s"%(row_count,"\n"))
	sys.stdout.flush();

	print HEADERS
	print "Processing lines of file..."

	file = open(input_file,'r')
	output = gzip.open(data_folder + file_id + ".data.gz", "wb")
	writer = csv.DictWriter(output, HEADERS, dialect='excel-tab')

	writer.writeheader()

	row_count = 0
	for line in file:

		# ---- salto gli header del file
		if re.match("^#.*", line):
			#print "IGNORING LINE"
			continue

		#print "skipping?"
		row_count += 1
		STATS["total"] += 1;

		# ---- comincio a parsare le informazioni della riga
		values = line.split('\t')

		# ---- comincio a memorizzare le informazioni fisse del file
		row = {
			"seqname": values[0],
			"source": values[1],
			"feature": values[2],
			"start": int(values[3]),
			"end": int(values[4]),
			"score": float(values[5]) if not values[5] == '.' else None,
			"strand": values[6] if not values[6] == '.' else None,
			"frame": values[7] if not values[6] == '.' else None,

		}

		for entry in ["seqname", "source", "feature"]:
			addEntryToDict(entry, row[entry], DICTIONARY)

		# ---- aggiorno le statistiche sulla feature
		if not STATS.has_key(row["feature"]):
			STATS_HEADER.append(row["feature"])
			STATS[row["feature"]] = 1
		else:
			STATS[row["feature"]] += 1

		# ---- ottengo la lista delle annotazioni della riga
		attributes = values[8].split(';')


		for element in attributes:
			#print element
			# ---- divido ogni annotazione come una coppia chiave - valore

			key, value = (element.strip(' \n').split(' ') + [None]*2)[:2]

			if key != '':
				# ---- se un valore è presente considero il caso sia vuoto ('.'), oppure se è formato da una lista di elementi (',' oppure '_')
				if value:

					value = str(value.decode('string_escape'))

					if value == '.':
						#print key + ': None'
						row[key] = None
					else:
						converted = inferType(key, value.replace('"', '').split(','), TYPES, DICTIONARY)
						#print key + ':', strconv.convert_series(value.replace('_', ',').split(','))
						row[key] = converted if len(converted) > 1 else converted[0]
						
						#print "Row[" + key + "]:", row[key]

				else:
					#print key + ': True'
					addType(key, "boolean", TYPES)
					row[key] = True

		#print row
		writer.writerow(row)

	#	ROWS.append(row)

		sys.stdout.write("%d lines scanned %s"%(row_count,"\r"))
		sys.stdout.flush();

	output.close()
	
	print ""
	print "STATS:", STATS
	
	for entry in DICTIONARY.keys():
		DICTIONARY[entry] = sorted(DICTIONARY[entry])

	SORTED = OrderedDict()

	for h in HEADERS:
		SORTED[h] = TYPES[h]
	
	# ---- costruisco il dataframe con pandas
	#dataframe = pd.DataFrame(data=ROWS, columns=CSV_HEADERS)
	#dataframe = pd.DataFrame(ROWS)
	
	# ---- memorizzo il risultato in un file csv
	#dataframe.to_csv( data_folder + username + "_" + experiment + "_" + os.path.basename(file.name) + ".data.gz", sep="\t", index=False, compression="gzip", mode='a')
	
	# ---- scrivo il file di statistiche
	statistics = gzip.open(data_folder + file_id + ".stats.gz", "wb")
	writer = csv.DictWriter(statistics, STATS_HEADER, dialect='excel-tab')
	writer.writeheader()
	writer.writerow(STATS)
	statistics.close()
 
	# ---- costrisco il dataframe dei tipi
	key_types = pd.DataFrame.from_dict(SORTED, orient="index")

	key_types.to_csv( data_folder + file_id + ".types.data.gz", sep="\t", index_label="Key", header=["Type"], compression="gzip")

	# ---- costruisco il dataframe dei valori
	dict_values = pd.DataFrame.from_dict(DICTIONARY, orient="index")

	dict_values.to_csv( data_folder + file_id + ".dictionary.data.gz", sep="\t", index_label="Key", compression="gzip")


	#print dataframe.dtypes


if __name__ == "__main__":
   main(sys.argv[1:])
