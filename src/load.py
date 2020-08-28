import shutil

from src.util import get_schema, send_to_neo4j, empty_dir, get_driver, find_nullable_relations, list_based_columns
from sys import platform
import subprocess
import os


def get_match(db_dict, object_name,nullable):
    match = ''
    cols = db_dict['OmniSeqKnowledgebase2'][object_name]['col_order']
    for col in cols:
        if col not in nullable:
            col_description = db_dict['OmniSeqKnowledgebase2'][object_name][col]
            dataType = col_description[6]
            if len(col_description[4])==0:
                type_name = col[:-9]
            else:
                type_name = col_description[4][0][:-9]
            if dataType == 'id' and type_name != '':
                if match != '':
                    match += '\n'
                if col.endswith('_graph_id'):
                    col = col[:-9]
                    col = col[0].lower() + col[1:]

                tag = get_tag_name(col,type_name)
                match += 'MATCH(' + tag + ':' + type_name + ') WHERE ' + tag + '.id=' + col
    if match != '':
        match = '\n' + match
    return match


def get_tag_name(col,type_name):
    if col.endswith('_graph_id'):
        col = col[:-9]
    tag = col.lower() + '_' + type_name.lower() + '_tag'
    return tag

def get_create_links(db_dict, object_name,object_tag,nullable):
    links = ''
    cols = db_dict['OmniSeqKnowledgebase2'][object_name]['col_order']
    for col in cols:
        if col not in nullable:
            col_description = db_dict['OmniSeqKnowledgebase2'][object_name][col]
            relation = col_description[5]
            dataType = col_description[6]
            if len(col_description[4])==0:
                if col.endswith('_graph_id'):
                    type_name = col[:-9]
                    type_name = type_name[0].lower() + type_name[1:]
            else:
                type_name = col_description[4][0][:-9]
            if dataType== 'id' and relation != '':
                if links != '':
                    links += '\n'
                tag = get_tag_name(col,type_name)
                links += 'CREATE (' + object_tag + ')-[:' + relation + ']->(' + tag + ')'

    if links != '':
        links = '\n' + links
    return links


def get_params(db_dict, object_name):
    params = ''
    cols = db_dict['OmniSeqKnowledgebase2'][object_name]['col_order']
    for col in cols:
        col_description = db_dict['OmniSeqKnowledgebase2'][object_name][col]
        relation = col_description[5]
        if relation == '':
            if params != '':
                params += ', '
            if col == 'graph_id':
                col = 'id'
            params += col + ':' + col
    return params


def get_row_reader(db_dict, object_name,nullable):
    read_command = ''
    cols = db_dict['OmniSeqKnowledgebase2'][object_name]['col_order']
    for col in cols:
        if col not in nullable:
            col_description = db_dict['OmniSeqKnowledgebase2'][object_name][col]
            dataType = col_description[6]
            if dataType != 'List':
                col2 = col
                if col2 == 'graph_id':
                    col2 = 'id'
                if col2.endswith('_graph_id'):
                    col2 = col2[:-9]
                    col2 = col2[0].lower() + col2[1:]
                if read_command != '':
                    read_command += ', '
                if dataType == 'Boolean':
                    read_command += 'toBoolean(row.' + col + ') as ' + col2
                elif dataType == 'Int':
                    read_command += 'toInteger(row.'+ col + ') as ' + col2
                elif dataType == 'piped_list':
                    # split(row.stringList, "|")
                    read_command += 'split(row.' + col + ', "|") as ' + col2
                else:
                    read_command += 'row.' + col + ' as ' + col2
    return read_command


def get_interface(db_dict, object_name):
    interface = db_dict['OmniSeqKnowledgebase2'][object_name]['graph_id'][7]
    if interface != '':
        interface = ':' + interface
    return interface





def auto_load(driver, object_name, db_dict, server, transformed_dir, export_dir):
    index_command = 'CREATE INDEX ON :' + object_name + '(id)'
    send_to_neo4j(driver,index_command)
    shutil.copy(os.path.realpath(transformed_dir + object_name + '.csv'), os.path.realpath(export_dir + object_name + '.csv'))
    nullable = find_nullable_relations(db_dict, object_name)
    num_files = split_big_files(object_name, export_dir)
    for file_counter in range(0, num_files):
        file_name = object_name + str(file_counter) + '.csv'
        sync_to_server(server, export_dir, file_name)
        read_command = f"LOAD CSV WITH HEADERS FROM 'file:///{file_name}' AS row" + '\nWITH '
        read_command += get_row_reader(db_dict, object_name,nullable)
        read_command += get_match(db_dict, object_name,nullable)
        interface = get_interface(db_dict, object_name)
        tag = object_name.lower()
        read_command += '\nCREATE (' + tag + ':' + object_name + interface + ' {'
        params = get_params(db_dict, object_name)
        read_command += params + '})'
        read_command += get_create_links(db_dict, object_name,tag,nullable)
        send_to_neo4j(driver, read_command)
    for col in list_based_columns(db_dict, object_name):
        col_description = db_dict['OmniSeqKnowledgebase2'][object_name][col]
        relation = col_description[5]
        for xObject_name in col_description[4]:
            xObject_name = xObject_name.replace('.', '_')
            xObject_name_short = xObject_name[:-9]
            yObject_name = object_name + '_graph_id'
            write_XFile_command(driver, export_dir, object_name, relation, server, transformed_dir, xObject_name, xObject_name_short, yObject_name)
    for n in nullable:
        col_description = db_dict['OmniSeqKnowledgebase2'][object_name][n]
        relation = col_description[5]
        for xObject_name in col_description[4]:
            xObject_name = xObject_name.replace('.','_')
            xObject_name_short = xObject_name[:-9]
            yObject_name = object_name + '_graph_id'
            write_XFile_command(driver, export_dir, object_name, relation, server, transformed_dir, xObject_name, xObject_name_short, yObject_name)


def write_XFile_command(driver, export_dir, object_name, relation, server, transformed_dir, xObject_name, xObject_name_short, yObject_name):
    file_name = object_name + '_' + xObject_name_short + '.csv'
    shutil.copy(os.path.realpath(transformed_dir + file_name), os.path.realpath(export_dir + file_name))
    sync_to_server(server, export_dir, file_name)
    read_command = f"LOAD CSV WITH HEADERS FROM 'file:///{file_name}' AS row" + f'\nWITH row.{xObject_name} as x, row.{yObject_name} as y' + '\n'
    read_command += f'MATCH(xx:{xObject_name_short}) WHERE xx.id=x' + '\n'
    read_command += f'MATCH(yy:{object_name}) WHERE yy.id=y' + '\n'
    read_command += f'CREATE (yy)-[:{relation}]->(xx)' + '\n'
    send_to_neo4j(driver, read_command)


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

def sync_to_server(server,export_dir,file_name):
    load_path = export_dir + file_name
    if server=='localhost':
        subprocess.call(["rsync", "-avz", load_path, get_import_path()])
    else:
        import_path = 'root@' + server + ':/root/neo4j/import'
        subprocess.call(["rsync", "-avze", 'ssh', load_path, import_path])

def split_big_files(file_name,export_dir):
    in_file = file_name + '.csv'
    lines_per_file = 20000
    smallfile = None
    file_num = 0
    header = None
    with open(export_dir + in_file) as bigfile:
        for lineno, line in enumerate(bigfile):
            if lineno==0:
                header = line
            if lineno % lines_per_file == 0:
                if smallfile:
                    smallfile.close()
                small_filename = file_name + str(file_num) + '.csv'
                file_num += 1
                smallfile = open(export_dir + small_filename, "w")
                if lineno != 0:
                    smallfile.write(header)
            smallfile.write(line)
        if smallfile:
            smallfile.close()
    os.remove(export_dir + in_file)
    return file_num

def do_load(server,transformed_dir,export_dir,db_dict,data_types,schema_path):
    with open(schema_path, 'r') as file:
        idl_as_string = file.read()
    driver = get_driver(server)
    send_to_neo4j(driver, "match(a) detach delete(a)")
    send_to_neo4j(driver, "call graphql.idl('" + idl_as_string + "')")
    empty_dir(export_dir)
    for dt in data_types:
        auto_load(driver, dt, db_dict, server, transformed_dir, export_dir)


if __name__ == '__main__':
    server = 'localhost'
    db_dict = get_schema('../config/table_descriptions_03_11.csv')
    transformed_dir = '../transformed/'
    export_dir = '../export/'
    data_types = ['User','Author','Journal','InternetReference','LiteratureReference','EditableInt','EditableStatement','EditableStringList','JaxGene','MyGeneInfoGene','UniprotEntry','OmniGene']
    schema_path = '../config/schema_03_11.graphql'
    do_load(server,transformed_dir,export_dir,db_dict,data_types,schema_path)


