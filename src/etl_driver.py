import os

from src.extract import do_extract
from src.load import do_load
from src.transform import do_transform
from src.util import get_schema, empty_dir


def create_if_not_exist(dir_path):
    if not os.path.exists(dir_path):
        os.makedirs(dir_path)



def main():

    read_server = '165.227.89.140'
    write_server = 'localhost'
    dump_file = 'dump.csv'
    dump_dir = '/Users/mglynias/Documents/GitHub/graph_etl/dump/'
    extracted_dir = '/Users/mglynias/Documents/GitHub/graph_etl/extracted/'
    transformed_dir = '/Users/mglynias/Documents/GitHub/graph_etl/transformed/'
    export_dir = '/Users/mglynias/Documents/GitHub/graph_etl/export/'
    config_dir = '/Users/mglynias/Documents/GitHub/graph_etl/config/'

    create_if_not_exist(dump_dir)
    create_if_not_exist(extracted_dir)
    create_if_not_exist(transformed_dir)
    create_if_not_exist(export_dir)

    read_db_dict = get_schema(config_dir + 'table_descriptions_03_11.csv')
    write_db_dict = get_schema(config_dir + 'table_descriptions_03_11.csv')
    schema_path = config_dir + 'schema_03_11.graphql'

    data_types = ['User','Author','Journal','InternetReference','LiteratureReference',
                  'EditableInt','EditableStatement','EditableStringList','JaxGene','MyGeneInfoGene','UniprotEntry','OmniGene',
                  'EditableBoolean','EditableFloat','EditableCopyChange','EditableProteinEffect','EditableOmniGeneReference','JaxVariant','ClinVarVariant','HotSpotVariant','GOVariant',
                  'VariantSNVIndel','VariantRegion','VariantCNV','VariantFusion','GenomicVariantMarker',
                  'EditableOmniGeneList','EditableAssayComparator','EditableRNASeqResultType','EditableImmunePhenotype','EditableImmuneFunction','EditableImmuneCycleRole','EditableOmniConjunction','EditableTMBInterpretation',
                    'MSIMarker','TMBMarker','IHCAssay','RNASeqAssay','ProteinExpressionMarker','EditableMarkerComponentList','MarkerProfile',
    # OncoTreeOccurrence
                  ]


    do_extract(read_server, dump_file, dump_dir, extracted_dir, read_db_dict)
    do_transform(extracted_dir,transformed_dir, write_db_dict,data_types)
    do_load(write_server, transformed_dir, export_dir, write_db_dict, data_types,schema_path)

if __name__ == '__main__':
    main()


