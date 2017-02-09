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