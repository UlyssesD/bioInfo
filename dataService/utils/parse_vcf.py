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

def getMutation(ref, alts, STATS):

	mutations = []

	ref = ref.replace(".", "")

	for alt in alts:

		m = ""
		alt = alt.replace(".", "")
		
		if alt == "*":
			m = "unknown"
			STATS["unknown"] += 1;

		elif len(ref) == len(alt):
			m = "snp"
			STATS["snp"] += 1;

		elif len(ref) < len(alt):
			m = "ins"
			STATS["ins"] += 1;
		
		elif len(ref) > len(alt):
			m = "del"
			STATS["del"] += 1;

		mutations.append(m)
		#addEntryToDict("MUTATION", m)

	return mutations

def getGenotype(gt, STATS):
	
	#print gt
	
	if gt == ".":
		genotype = "undetected"
		return genotype
	
	alleles = gt.split('/')

	if alleles[0] == alleles[1]:
		if alleles[0] == '.':
			genotype = "undetected"
			STATS["undetected"] += 1;

		elif alleles[0] == 0:
			genotype = "hom_ref"
			STATS["hom_ref"] += 1;
		
		else:
			genotype = "hom_alt"
			STATS["hom_alt"] += 1;
	
	elif alleles[0] != alleles[1]:
		genotype = "het"
		STATS["het"] += 1;
	
	#print genotype
	return genotype

def main(argv):  
	
	# ---- VARIABILI DEL METODO

	ROWS = []						# memorizza le righe del file vcf
	SAMPLES = []					# tiene traccia dei campioni presenti nel file

	# utilizzato per memorizzare le colonne del file finale
	HEADERS = ['CHROM', 'POS', 'ID', 'REF', 'ALT', 'QUAL', 'FILTER', 'FORMAT', 'MUTATION', 'state', 'phasing' ]
	
	# utilizzato per memorizzare i valori dei campi stringa del file (utile lato client per generare le select e le autocomplete)
	DICTIONARY = {
		"state": set(["het", "hom_alt", "hom_ref", "undetected"]),
		"MUTATION": set(["del", "ins", "snp", "unknown"]),
		"phasing": set(["phased", "unphased", "undetected"])
	}

	# utilizzato per memorizzare i tipi dei campi presenti nel file (utile lato client per la generazione dei form)					
	TYPES = {}						


	STATS_HEADER = ["total", "snp", "ins", "del", "unknown", "hom_alt", "hom_ref", "het", "undetected", "phased", "unphased"]
	STATS = {
		"total": 0,
		"snp": 0,
		"ins": 0,
		"del": 0,
		"unknown": 0,
		"het": 0,
		"hom_alt": 0,
		"hom_ref": 0,
		"undetected": 0,
		"phased": 0,
		"unphased": 0
	}

	# ---- ricavo le informazioni dalla riga di comando
	input_file = argv[0] 	# ---- nome del file vcf di input
	temp_folder = argv[1]	# ---- cartella temporanea per memorizzare i csv parziali
	data_folder = argv[2]	# ---- cartella dove memorizzare il file csv finale
	username =  argv[3]		# ---- nome utente del proprietario del file
	experiment = argv[4]	# ---- esperimento a cui il file appartiene
	species = argv[5]		# ---- specie del file passato in input
	file_id = argv[6] or os.path.basename(file.name)
	# ---- Apro il file vcf
	print 'Opening .vcf file...'
	file = open(input_file, 'r')
	
	#reader = vcf.Reader(file, encoding='utf-8')

	
	print 'Starting parsing procedure for file ' + os.path.basename(file.name)


	row_count = 0 

	# ---- aggiungo i tipi per i valori fissi del file
	for entry in [("CHROM", "string"), ("POS", "int"), ("ID", "string"), ("REF", "string"), ("ALT", "string"), ("QUAL", "float"), ("FILTER", "string"), ("FORMAT", "string"), ("MUTATION", "string"), ("state", "string"), ("phasing", "string")]:
		addType(entry[0], entry[1], TYPES)

	print "Scanning headers of output file"

	# ---- leggo una prima volta il file per intero per calcolare tutti gli header del file csv finale
	for line in iter(file):

		# ---- salto gli header del file
		if re.match("^##.*", line):
			print "IGNORING LINE"
			continue
		
		if re.match("^#CHROM\t", line):
			print "HEADER OF VCF FILE"

			SAMPLES = line.strip('#\n').split('\t')[9:]
			print SAMPLES, "length:", len(SAMPLES)
			continue

		row_count += 1

		# ---- comincio a parsare le informazioni della riga
		values = line.split('\t')

		# ---- ottengo la lista delle annotazioni della riga
		annotations = values[7].split(';')

		for element in annotations:

			# ---- divido ogni annotazione come una coppia chiave - valore
			key, value = (element.split('=') + [None]*2)[:2]

			if key not in HEADERS:
				HEADERS.append(key)
				
		sys.stdout.write("%d lines scanned %s"%(row_count,"\r"))
		sys.stdout.flush();


	sys.stdout.write("%d lines scanned %s"%(row_count,"\n"))
	sys.stdout.flush();
	
	for idx in range(len(HEADERS)):
		if re.match("(\w*)snp(\w*)", HEADERS[idx]):
			HEADERS[idx] = "dbSNP"
	
	for sample in SAMPLES:
		addType(sample, 'skip', TYPES)
		HEADERS.append(sample)

	print "Processing lines of file..."

	print 

	file = open(input_file,'r')
	output = gzip.open(data_folder + file_id + ".data.gz", "wb")
	writer = csv.DictWriter(output, HEADERS, dialect='excel-tab')

	writer.writeheader()

	row_count = 0
	for line in file:

		# ---- salto gli header del file
		if re.match("^##.*", line):
			#print "IGNORING LINE"
			continue
		
		if re.match("^#CHROM\t", line):
			#print "HEADER OF VCF FILE"

			#SAMPLES = line.strip('#').split('\t')[9:]
			#print SAMPLES, "length:", len(SAMPLES)
			continue

		#print "skipping?"
		row_count += 1
		STATS["total"] += 1;

		# ---- comincio a parsare le informazioni della riga
		values = line.split('\t')

		# ---- comincio a memorizzare le informazioni fisse del file
		row = {
			"CHROM": values[0],
			"POS": int(values[1]),
			"ID": values[2],
			"REF": values[3],
			"ALT": values[4].split(','),
			"QUAL": float(values[5]) if not values[5] == '.' else None,
			"FILTER": values[6],
			"FORMAT": values[8],
			"state": [],
			"phasing": []
		}

		row["MUTATION"] = getMutation(row["REF"], row["ALT"], STATS)

		for entry in ["CHROM", "REF", "FILTER"]:
			addEntryToDict(entry, row[entry], DICTIONARY)

		# ---- ottengo la lista delle annotazioni della riga
		annotations = values[7].split(';')


		for element in annotations:
			#print element
			# ---- divido ogni annotazione come una coppia chiave - valore

			key, value = (element.split('=') + [None]*2)[:2]


			# ---- se un valore è presente considero il caso sia vuoto ('.'), oppure se è formato da una lista di elementi (',' oppure '_')
			if value:

				value = str(value.decode('string_escape'))

				if re.match("(\w*)snp(\w*)", key):
					
					# ---- Se è la prima volta che incontro la chiave oppure non è stato trovato alcun valore in precedenza
					if not row.has_key('dbSNP') or row['dbSNP'] is None:
	
						if value == '.':
							#print key + ': None'
							row['dbSNP'] = None
						else:
							converted = inferType('dbSNP', value.replace(" ", "").replace('_', ',').replace(';',',').split(','), TYPES, DICTIONARY)
							#print key + ':', strconv.convert_series(value.replace('_', ',').split(','))
							row['dbSNP'] = converted if len(converted) > 1 else [ converted[0] ]

							if not STATS.has_key('in_dbSNP'):
								print "new STAT: dbSNP"
								STATS_HEADER.append('in_dbSNP')
								STATS['in_dbSNP'] = len(row['dbSNP'])
							else:
								STATS['in_dbSNP'] += len(row['dbSNP'])
					# ---- Se ho già incontrato la chiave, controllo che sia diversa
					else:

						if value != '.':
							converted = inferType('dbSNP', value.replace(" ", "").replace('_', ',').replace(';',',').split(','), TYPES, DICTIONARY)
							
							for el in converted:
								if el not in row['dbSNP']:
									row['dbSNP'].append(el)
									STATS['in_dbSNP'] += 1					
				
				else:
					if value == '.':
						#print key + ': None'
						row[key] = None
					else:
						converted = inferType(key, value.replace(" ", "").replace('_', ',').replace(';',',').split(','), TYPES, DICTIONARY)
						#print key + ':', strconv.convert_series(value.replace('_', ',').split(','))
						row[key] = converted if len(converted) > 1 else converted[0]
					
						#print "Row[" + key + "]:", row[key]

			else:
				#print key + ': True'
				addType(key, "boolean", TYPES)
				row[key] = True

			

		#for key in row.keys():


			

				# if re.match('1000g(\w*)_all', key):
				# 	if value == None or value == '.':
				# 		if STATS.has_key('not_in_1000g'):
				# 			STATS['not_in_1000g'] += 1
				# 		else:
				# 			STATS['not_in_1000g'] = 1
				# 	else:
				# 		if not STATS.has_key('in_1000g'):
				# 			STATS['in_1000g'] = 1
				# 		else:
				# 			STATS['in_1000g'] += 1


		# ---- memorizzo le informazioni dei campioni
		if len(SAMPLES) > 0 and row["FORMAT"] != '.':

			attrs = row["FORMAT"].split(':')
			s = 0
			for sample in values[9:]:
				
				if sample == '.':
					row["state"].append("undetected")
					row[SAMPLES[s]] = sample
					s = s + 1
					continue

				temp = []
				sample = sample.split(':')
				for i in range(len(sample)):
					sample[i] = sample[i].replace("_",";").replace(",",";").strip('\n')
					temp.append(attrs[i] + "=" + sample[i])
					
					if attrs[i] == "GT":

						if re.match('^(.)+/(.)+$', sample[i]):
							
							gt_state = getGenotype(sample[i], STATS)
						   
							if gt_state == "undetected":
								
								row["phasing"].append("undetected")
							else:
								STATS["unphased"] += 1;
								row["phasing"].append("unphased")
							
							row["state"].append(gt_state)

						elif re.match('^(.)+|(.)+$', sample[i]):
							
							#print "sample is phased"
							sample[i] = sample[i].replace("|", "/")
							gt_state = getGenotype(sample[i], STATS)
						   
							if gt_state == "undetected":
								row["phasing"].append("undetected")
							else:
								STATS["phased"] += 1;
								row["phasing"].append("phased")
							
							row["state"].append(gt_state)
						
						elif sample[i] == ".":
							row["phasing"].append("undetected")
							row["state"].append("undetected")
						

				row[SAMPLES[s]] = temp
				s = s + 1


		#print row
		writer.writerow(row)

	#	ROWS.append(row)

		sys.stdout.write("%d lines scanned %s"%(row_count,"\r"))
		sys.stdout.flush();

	#    if not (row_count % 100000):

	#        print ""
			
	#        dataframe = pd.DataFrame(ROWS)
			
	#        dataframe.to_csv( data_folder + username + "_" + experiment + "_" + os.path.basename(file.name) + ".data.gz", sep="\t", index=False, compression="gzip", mode='a')
		   
	#        del ROWS[:]

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