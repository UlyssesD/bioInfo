from __future__ import unicode_literals

# Create your models here.
from neomodel import StructuredNode, StructuredRel, StringProperty, IntegerProperty, ArrayProperty, BooleanProperty, FloatProperty, JSONProperty
from neomodel.relationship_manager import RelationshipTo, RelationshipFrom


# ----  Definizione delle relazioni

class SupportedByRel(StructuredRel):

	# ---- attributi
	info_id = StringProperty(UniqueIndex=True, Required=True)
	sample = StringProperty(UniqueIndex=True, Required=True)
	phased = BooleanProperty()
	state = IntegerProperty()
	attributes = JSONProperty()


class ForVariantRel(StructuredRel):

	# ---- attributi
	variant_id = StringProperty(UniqueIndex=True, Required=True)
	info_id = StringProperty(UniqueIndex=True, Required=True)
	#START = IntegerProperty()
	END = IntegerProperty()
	ID = StringProperty()
	QUAL = FloatProperty()
	FILTER = StringProperty()
	FORMAT = StringProperty()
	HETEROZIGOSITY = FloatProperty()
	dbSNP = StringProperty()


# ---- Definizione dei nodi

class User(StructuredNode):

	# ---- attributi
	username = StringProperty(UniqueIndex=True, Required=True)

	# ---- relazioni
	created = RelationshipTo('Experiment', 'Created')


class Experiment(StructuredNode):

	# ---- attributi
	name = StringProperty(Required=True)

	# ---- relazioni
	created = RelationshipFrom('User', 'Created')
	forSpecies = RelationshipTo('Species', 'For_Species')
	composedBy = RelationshipTo('File', 'Composed_By')


class Species(StructuredNode):

	# ---- attributi
	species = StringProperty(UniqueIndex=True, Required=True)

	# ---- relazioni
	forSpecies = RelationshipFrom('Experiment', 'For_Species')
	ofSpecies = RelationshipFrom('Genotype', 'Of_Species')


class File(StructuredNode):
	
	# ---- attributi
	name = StringProperty(UniqueIndex=True, Required=True)
	extension = StringProperty()
	statistics = JSONProperty()

	# ---- relazioni
	composedBy = RelationshipFrom('Experiment', 'Composed_By')
	contains = RelationshipTo('Info', 'Contains')


class Info(StructuredNode):

	# ---- attributi
	info_id = StringProperty(UniqueIndex=True, Required=True)
	attributes = JSONProperty()

	# ---- relazioni
	contains = RelationshipFrom('File', 'Contains')
	supportedBy = RelationshipTo('Genotype', 'Supported_By', model=SupportedByRel)
	forVariant = RelationshipTo('Variant', 'For_Variant', model=ForVariantRel)


class Genotype(StructuredNode):

	# ---- attributi
	sample = StringProperty(UniqueIndex=True, Required=True)

	# ---- relazioni
	supportedBy = RelationshipFrom('Info', 'Supported_By', model=SupportedByRel)
	ofSpecies = RelationshipTo('Species', 'Of_Species')


class Variant(StructuredNode):

	# ---- attributi
	variant_id = StringProperty(UniqueIndex=True, Required=True)
	CHROM = StringProperty(Required=True)
	POS = IntegerProperty()
	REF = StringProperty()
	ALT = StringProperty()
	MUTATION = StringProperty()

	# ---- relazioni
	forVariant = RelationshipFrom('Info', 'For_Variant', model=ForVariantRel)
	hasVariant = RelationshipFrom('Chromosome', 'Has_Variant')
	inVariant = RelationshipFrom('Gene', 'In_Variant')


class Chromosome(StructuredNode):

	# ---- attributi
	chromosome = StringProperty(UniqueIndex=True, Required=True)

	# ---- relazioni 
	inChromosomome = RelationshipFrom('Gene', 'In_Chromosome')
	hasVariant = RelationshipTo('Variant', 'Has_Variant')


class Gene(StructuredNode):

	# ---- attributi
	gene_id = StringProperty(UniqueIndex=True, Required=True)

	# ---- relazioni
	inVariant = RelationshipTo('Variant', 'In_Variant')
	inChromosomome = RelationshipTo('Chromosome', 'In_Chromosome')

