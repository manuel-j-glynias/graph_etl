from src.extract import do_extract
from src.load import do_load
from src.transform import do_transform
from src.util import get_schema


def main():
    # server = 'localhost'
    read_server = '165.227.89.140'
    write_server = 'localhost'
    extracted_dir = '../extracted/'
    dump_dir = '../dump/'
    dump_file = 'dump.csv'
    transformed_dir = '/Users/mglynias/Documents/GitHub/graph_etl/transformed/'
    export_dir = '../export/'
    db_dict = get_schema('config/table_descriptions_03_11.csv')
    data_types = ['User','Author','Journal','InternetReference','LiteratureReference','EditableInt','EditableStatement','EditableStringList','JaxGene','MyGeneInfoGene','UniprotEntry','OmniGene']


    do_extract(read_server, dump_file, dump_dir, extracted_dir, db_dict)
    do_transform(extracted_dir,transformed_dir, db_dict)
    do_load(write_server, transformed_dir, export_dir, db_dict, data_types)

if __name__ == '__main__':
    main()


