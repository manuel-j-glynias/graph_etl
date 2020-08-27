import csv
from neo4j import GraphDatabase

from src.util import send_to_neo4j, copy_file_from_server, empty_dir, get_schema, get_driver


def extract_relations(dumpFilePath):
    # "_start","_end","_type"
    relations_dict = {}
    id_dict = {}
    with open(dumpFilePath) as csvfile:
        r = csv.DictReader(csvfile)
        counter = 0
        for row in r:
            counter += 1
            if row['_id'] != '' :
                if  row['id'] != '':
                    id_dict[row['_id']] = row['id']
                else:
                    print(row['_id'],'bad graphid')

            if row['_start'] != '' :
                if  row['_end'] == '' or row['_start'] not in id_dict or row['_end'] not in id_dict:
                    print('_start',row['_start'],row['_start'] in id_dict)
                    print('_end',  row['_end'], row['_end'] in id_dict)
                    print('crap')
                else:
                    object1 = id_dict[row['_start']]
                    object2 = id_dict[row['_end']]
                    relation = row['_type']
                    if not object1 in relations_dict:
                        relations_dict[object1] = {object2:relation}
                    else:
                        d = relations_dict[object1]
                        d[object2] = relation
            if counter % 100000==0:
                print(counter)
    return relations_dict


def get_files_dict(db_dict, load_dir):
    files_dict = {}
    for db_name in sorted(db_dict.keys()):
        for table_name in sorted(db_dict[db_name].keys()):
            # print(table_name)
            out_file = open(load_dir + table_name + '.csv', 'w', encoding='utf-8')
            header = db_dict[db_name][table_name]['col_order']
            writer = csv.writer(out_file, lineterminator='\n',quoting=csv.QUOTE_ALL)
            writer.writerow(header)
            files_dict[table_name] = writer
    return files_dict


def get_id_for_relation(d, relation):

    id = None
    for key, value in d.items():
        if value==relation:
            if id==None:
                id = key
            else:
                id = id + '|' + key
    return id


def get_data_type(data_types, db_dict):
    data_type = None
    for dt in data_types:
        if dt in db_dict['OmniSeqKnowledgebase2']:
            data_type = dt
            break
    return data_type


def write_dump_as_csvs(db_dict,relations_dict,load_dir,dumpFilePath):
    files_dict = get_files_dict(db_dict, load_dir)
    with open(dumpFilePath) as csvfile:
        r = csv.DictReader(csvfile)
        counter = 0
        for row in r:
            counter += 1
            data_types = row['_labels'].split(':')
            data_type = get_data_type(data_types,db_dict)
            if not data_type==None and data_type in files_dict:
                writer = files_dict[data_type]
                cols = db_dict['OmniSeqKnowledgebase2'][data_type]['col_order']
                new_row = []
                for col in cols:
                    if col=='graph_id':
                        col = 'id'
                    if col in row:
                        new_row.append( row[col])
                    else:
                        d = relations_dict[row['id']]
                        # get_id_for_relation(d,col)
                        relation = db_dict['OmniSeqKnowledgebase2'][data_type][col][5]
                        id_for_relation = get_id_for_relation(d, relation)
                        if id_for_relation != None and  id_for_relation.startswith('ref_'):
                            for ref in id_for_relation.split('|'):
                                if ref.startswith('ref_g'):
                                    key = data_type + '_InternetReference'
                                else:
                                    key = data_type + '_LiteratureReference'
                                ref_writer = files_dict[key]
                                ref_writer.writerow(['', row['id'], ref])

                        new_row.append(id_for_relation)
                writer.writerow(new_row)
            if counter % 100000==0:
                print(counter)


def do_extract(server, dump_file, dump_dir, extracted_dir, db_dict):
    empty_dir(dump_dir)
    empty_dir(extracted_dir)
    send_to_neo4j(get_driver(server), "CALL apoc.export.csv.all('" + dump_file + "', {})")
    copy_file_from_server(server, dump_file, dump_dir)
    dump_file_path = dump_dir + dump_file
    relations_dict = extract_relations(dump_file_path)
    write_dump_as_csvs(db_dict, relations_dict, extracted_dir, dump_file_path)

if __name__ == '__main__':
    server = '165.227.89.140'
    extracted_dir = '../extracted/'
    dump_dir = '../dump/'
    dump_file = 'dump.csv'
    transformed_dir = '../transformed'

    uri = 'bolt://' + server + ':7687'
    driver = GraphDatabase.driver(uri, auth=("neo4j", "omni"))
    db_dict = get_schema('../config/table_descriptions_03_11.csv')
    do_extract(server, dump_file, dump_dir, extracted_dir, db_dict)
