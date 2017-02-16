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
			"container": "Variant",
			"param": "CHROM",
			"type": "string",
			"value": None
		},
		{
			"label": "POS",
			"container": "Variant",
			"param": "POS",
			"type": "numeric",
			"min": None,
			"max": None
		},
		{
			"label": "END",
			"container": "ForVariant",
			"param": "END",
			"type": "numeric",
			"min": None,
			"max": None
		},
		{
			"label": "REF",
			"container": "Variant",
			"param": "REF",
			"type": "string",
			"value": None
		},
		{
			"label": "ALT",
			"container": "Variant",
			"param": "ALT",
			"type": "string",
			"value": None
		},
		{
			"label": "MUTATION",
			"container": "Variant",
			"param": "MUTATION",
			"type": "string",
			"value": None
		},
		{
			"label": "ID",
			"container": "ForVariant",
			"param": "ID",
			"type": "string",
			"value": None
		},
		{
			"label": "QUAL",
			"container": "ForVariant",
			"param": "ID",
			"type": "numeric",
			"min": None,
			"max": None
		},
		{
			"label": "FILTER",
			"container": "ForVariant",
			"param": "FILTER",
			"type": "string",
			"value": None
		},
		{
			"label": "HETEROZIGOSITY",
			"container": "ForVariant",
			"param": "HETEROZIGOSITY",
			"type": "numeric",
			"min": None,
			"max": None
		},
		{
			"label": "dbSNP",
			"container": "ForVariant",
			"param": "dbSNP",
			"type": "string",
			"value": None
		},
		{
			"label": "sample",
			"container": "Genotype",
			"param": "sample",
			"type": "string",
			"value": None
		},
		{
			"label": "phased",
			"container": "SupportedBy",
			"param": "phased",
			"type": "boolean",
			"value": None
		},
		{
			"label": "state",
			"container": "SupportedBy",
			"param": "state",
			"type": "string",
			"value": None
		},
		
	]
}