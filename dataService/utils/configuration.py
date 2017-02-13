# -*- coding: utf-8 -*-


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
			"params": "Gene.refGene"
		},
		{
			"label": "Location",
			"type": "single",
			"params": "Func.refGene"
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
			"label": "CHROM",
			"param": "CHROM",
			"type": "string"
		},
		{
			"label": "POS",
			"param": "POS",
			"type": "numeric"
		},
		{
			"label": "REF",
			"param": "REF",
			"type": "string"
		},
		{
			"label": "ALT",
			"param": "ALT",
			"type": "string"
		},
		{
			"label": "MUTATION",
			"param": "MUTATION",
			"type": "string"
		},
		{
			"label": "END",
			"param": "END",
			"type": "numeric"
		},
		{
			"label": "ID",
			"param": "ID",
			"type": "string"
		},
		{
			"label": "QUAL",
			"param": "ID",
			"type": "numeric"
		},
		{
			"label": "FILTER",
			"param": "FILTER",
			"type": "string"
		},
		{
			"label": "HETEROZIGOSITY",
			"param": "HETEROZIGOSITY",
			"type": "numeric"
		},
		{
			"label": "dbSNP",
			"param": "dbSNP",
			"type": "string"
		},
		{
			"label": "sample",
			"param": "sample",
			"type": "string"
		},
		{
			"label": "phased",
			"param": "phased",
			"type": "boolean"
		},
		{
			"label": "state",
			"param": "state",
			"type": "string"
		},
		
	]
}