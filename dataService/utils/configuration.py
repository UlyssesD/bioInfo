# -*- coding: utf-8 -*-


# ---- variabile temporanea per identificare l'address delle API di Django (da modificare per funzionare correttamente)
API_ADDRESS = "localhost:8000"

# ----- elenco degli attributi da visualizzare nelle colonne della tabella per i differenti formati di file
# ----- (utilizzati per costruire la response a seguito della chiamata all'API)
TABLE_STRUCTURE = {
	".vcf": [
		{
			"label": "Position",
			"type": "custom",
			"params": ["CHROM", "POS", "END"],
			"template": "CHROM:POS-END"
		},
		{
			"label": "Allele variation",
			"type": "custom",
			"params": ["REF", "ALT"],
			"template": "REF &rarr; ALT"
		},
		{
			"label": "Depth",
			"type": "single",
			"params": "DP"
		},
		{
			"label": "Gene",
			"type": "single",
			"params": "Gene_refGene"
		},
		{
			"label": "Location",
			"type": "single",
			"params": "Func_refGene"
		},
		{
			"label": "dbSNP",
			"type": "single",
			"params": "dbSNP"
		},
		{
			"label": "Quality",
			"type": "single",
			"params": "QUAL"
		},
		{
			"label": "CQ ratio",
			"type": "single",
			"params": "QD"
		},
		{
			"label": "FS",
			"type": "single",
			"params": "FS"
		},
		{
			"label": "MQ0",
			"type": "single",
			"params": "MQ0"
		}

	]
}

# ---- elenco degli attributi da filtrare ricavati a partire dagli attributi FISSI nei file
FIXED_FILTERS = {
	".vcf": [
		{
			"label": "Chromosome",
			"container": "Variant",
			"param": "CHROM",
			"param_type": "string",
			"type": "select",
			"options": None,
			"url": "http://" + API_ADDRESS + "/dataService/chromosomes/",
			"value": None
		},
		{
			"label": "Start",
			"container": "Variant",
			"param": "POS",
			"param_type": "numeric",
			"type": "numeric",
			"min": None,
			"max": None
		},
		{
			"label": "Reference",
			"container": "Variant",
			"param": "REF",
			"param_type": "string",
			"type": "string",
			"value": None
		},
		{
			"label": "State",
			"container": "SupportedBy",
			"param": "state",
			"param_type": "string",
			"type": "select",
			"options": [
				{
					"option": "-- All --",
					"value": None
				},
				{
					"option": "hom_ref",
					"value": "hom_ref"
				},
				{
					"option": "hom_alt",
					"value": "hom_alt"
				},
				{
					"option": "het",
					"value": "het"
				},
				{
					"option": "uncalled",
					"value": "uncalled"
				},

			],
			"value": None
		},
		{
			"label": "Read depth",
			"container": "Info",
			"param": "DP",
			"param_type": "numeric",
			"type": "numeric",
			"min": None,
			"max": None
		},
		{
			"label": "Mutation",
			"container": "Variant",
			"param": "MUTATION",
			"type": "select",
			"options": [
				{
					"option": "-- All --",
					"value": None
				},
				{
					"option": "snp",
					"value": "snp"
				},
				{
					"option": "indels",
					"value": "indel"
				},
				{
					"option": "unknown",
					"value": "unknown"
				},

			],
			"param_type": "string",
			"value": None
		},
		{
			"label": "Gene",
			"container": "Info",
			"param": "Gene_refGene",
			"type": "autocomplete",
			"url": "http://" + API_ADDRESS + "/dataService/genes/",
			"param_type": "list",
			"value": None
		},
		{
			"label": "Genomic location",
			"container": "Info",
			"param": "Func_refGene",
			"param_type": "list",
			"type": "select",
			"url":  "http://" + API_ADDRESS + "/dataService/locations/",
			"options": None,
			"value": None
		},
		{
			"label": "dbSNP",
			"container": "Info",
			"param": "dbSNP",
			"param_type": "string",
			"type": "string",
			"value": None
		},
		{
			"label": "Phred quality",
			"container": "Info",
			"param": "QUAL",
			"param_type": "numeric",
			"type": "numeric",
			"min": None,
			"max": None
		},
		{
			"label": "CQ ratio",
			"container": "Info",
			"param": "QD",
			"type": "numeric",
			"param_type": "numeric",
			"min": None,
			"max": None
		},
		{
			"label": "Fisher test",
			"container": "Info",
			"param": "FS",
			"param_type": "numeric",
			"type": "numeric",
			"min": None,
			"max": None
		},
		{
			"label": "SIFT score",
			"container": "Info",
			"param": "SIFT_score",
			"param_type": "numeric",
			"type": "numeric",
			"min": None,
			"max": None
		},
		{
			"label": "MQ0",
			"container": "Info",
			"param": "MQ0",
			"param_type": "numeric",
			"type": "numeric",
			"min": None,
			"max": None
		},
		{
			"label": "1000 Genomes all projects",
			"container": "Info",
			"param": "otg_all",
			"param_type": "numeric",
			"type": "numeric",
			"min": None,
			"max": None
		},
		{
			"label": "Number of methods",
			"container": "Info",
			"param": "NM",
			"param_type": "numeric",
			"type": "numeric",
			"min": None,
			"max": None
		},
		{
			"label": "Method",
			"container": "Info",
			"param": "LM",
			"type": "select",
			"options": [
				{
					"option": "-- All --",
					"value": None
				},
				{
					"option": "Freebayes",
					"value": "FB"
				},
				{
					"option": "Varscan2",
					"value": "VS"
				},
				{
					"option": "Gatk",
					"value": "GA"
				}

			],
			"param_type": "list",
			"value": None
		}

	]
}