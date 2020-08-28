import csv
import os
import shutil
import subprocess
from sys import platform

from neo4j import GraphDatabase


def empty_dir(path):
    filelist = [f for f in os.listdir(path) if f.endswith(".csv")]
    for f in filelist:
        os.remove(os.path.join(path, f))

def get_list_of_files(path: str) -> list:
    json_files = []
    for entry in os.scandir(path):
        if entry.is_file():
            json_files.append(entry.path)
    return json_files


def copy_files(files_to_copy,destination):
    for file in files_to_copy:
        shutil.copy(os.path.realpath(file), os.path.realpath(destination))


def get_schema(descriptions_csv_path):
    db_dict = {}  # {db_name:{table_name:{col:[type,key,allow_null,ref_col_list],'col_order':[cols in order]}}}

    init_file = open(descriptions_csv_path, 'r')
    reader = csv.reader(init_file, quotechar='\"')
    for line in reader:
        #print(line)
        db_name = line[0]
        if (db_name == 'Database'):
            continue
        if (db_name not in db_dict.keys()):
            db_dict[db_name] = {}
        table_name = line[1]
        col = line[2]
        col_type = line[3]
        col_key = line[4]
        allow_null = line[5]
        auto_incr = line[6]
        ref_col_list = line[7].split('|') # we will ignore this for now during development
        if len(line) > 10:
            relation = line[9]
            data_type = line[10]
            interface = line[11]
        else:
            relation = ''
            data_type = ''
            interface = ''

        try:
            ref_col_list.remove('')
        except:
            pass

        try:
            db_dict[db_name][table_name][col] = [col_type, col_key, allow_null, auto_incr, ref_col_list,relation,data_type,interface]
            db_dict[db_name][table_name]['col_order'].append(col)
        except:
            db_dict[db_name][table_name] = {col: [col_type, col_key, allow_null, auto_incr, ref_col_list,relation,data_type,interface]}
            db_dict[db_name][table_name] = {col: [col_type, col_key, allow_null, auto_incr, ref_col_list,relation,data_type,interface], 'col_order': [col]}
    init_file.close()
    #pprint(db_dict)
    return db_dict


def get_import_path():
    linux_import_path = ''
    mac_import_path = '/Users/mglynias/Library/Application Support/Neo4j Desktop/Application/neo4jDatabases/database-15244089-f960-43fd-9463-ac733d18daaa/installation-3.5.14/import/'
    windows_import_path = ''
    path = ''
    if platform == "linux" or platform == "linux2":
        path = linux_import_path
    elif platform == "darwin":
        path = mac_import_path
    elif platform == "win32":
        path = windows_import_path
    return path


def copy_file_from_server(server,file,dir):
    if server=='localhost':
        source = get_import_path() + file
        subprocess.call(["rsync", "-avz", source, dir ])
    else:
        import_path = 'root@' + server + ':/root/neo4j/import/' + file
        subprocess.call(["rsync", "-avze", 'ssh', import_path, dir])


def send_to_neo4j(driver, payload):
    print(payload)
    with driver.session() as session:
        tx = session.begin_transaction()
        result = tx.run(payload)
        print(result)
        tx.commit()


def get_driver(server):
    uri = 'bolt://' + server + ':7687'
    driver = GraphDatabase.driver(uri, auth=("neo4j", "omni"))
    return driver


def find_nullable_relations(db_dict,object_name):
    nullable = []
    cols = db_dict['OmniSeqKnowledgebase2'][object_name]['col_order']
    for col in cols:
        col_description = db_dict['OmniSeqKnowledgebase2'][object_name][col]
        allow_null = col_description[2]
        relation = col_description[5]
        dataType = col_description[6]
        if relation!='' and dataType != 'List' and allow_null=='Y':
            nullable.append(col)
    return nullable

def list_based_columns(db_dict, object_name):
    list_based = []
    cols = db_dict['OmniSeqKnowledgebase2'][object_name]['col_order']
    for col in cols:
        col_description = db_dict['OmniSeqKnowledgebase2'][object_name][col]
        dataType = col_description[6]
        if dataType == 'List':
            list_based.append(col)
    return list_based