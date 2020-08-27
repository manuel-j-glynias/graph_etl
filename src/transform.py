import csv

from src.util import empty_dir, get_list_of_files, copy_files, find_nullable_relations, get_schema


# "[""CAG3A"",""CTG3a"",""NBL"",""NUMB-R"",""NUMBLIKE"",""NUMBR"",""TNRC23""]"
def transform_string_list(transformed_dir):
    stringlist_file = transformed_dir + 'EditableStringList.csv'
    rows = []
    with open(stringlist_file) as csvfile:
        r = csv.DictReader(csvfile)
        for row in r:
            stringList = row['stringList']
            stringList = stringList.replace('"','').replace(',','|').replace('[','').replace(']','')
            new_row = [row['field'],stringList,row['editDate'],row['editorId'],row['references'],row['graph_id']]
            rows.append(new_row)
    with open(stringlist_file, 'w') as csvfile:
        csvwriter = csv.writer(csvfile)
        # "field","stringList","editDate","editorId","references","graph_id"
        csvwriter.writerow(["field","stringList","editDate","editorId","references","graph_id"])
        for row in rows:
            csvwriter.writerow(row)

def create_filtered_file(transformed_dir,file_name_fragment, filter_column):
    rows = []
    in_file = file_name_fragment + '.csv'
    m = filter_column.find('_')
    tag = filter_column[:m]
    out_file = file_name_fragment + '_' + tag + '.csv'
    with open(transformed_dir + in_file) as csvfile:
        r = csv.DictReader(csvfile)
        for row in r:
             if row[filter_column] != '':
                rows.append([row[filter_column], row['graph_id']])

    with open(transformed_dir + out_file, 'w') as csvfile:
        csvwriter = csv.writer(csvfile)
        csvwriter.writerow([filter_column, file_name_fragment+ '_graph_id'])
        for row in rows:
            csvwriter.writerow(row)


def do_transform(extracted_dir,transformed_dir, db_dict,data_types):
    empty_dir(transformed_dir)
    files_to_copy = get_list_of_files(extracted_dir)
    copy_files(files_to_copy, transformed_dir)
    transform_string_list(transformed_dir)
    for dt in data_types:
        nullable = find_nullable_relations(db_dict, dt)
        for n in nullable:
            create_filtered_file(transformed_dir,dt,n)


if __name__ == '__main__':
    extracted_dir = '/Users/mglynias/Documents/GitHub/graph_etl/extracted/'
    transformed_dir = '/Users/mglynias/Documents/GitHub/graph_etl/transformed/'
    db_dict = get_schema('../config/table_descriptions_03_11.csv')
    data_types = ['User','Author','Journal','InternetReference','LiteratureReference','EditableInt','EditableStatement','EditableStringList','JaxGene','MyGeneInfoGene','UniprotEntry','OmniGene']

    do_transform(extracted_dir,transformed_dir,db_dict,data_types)