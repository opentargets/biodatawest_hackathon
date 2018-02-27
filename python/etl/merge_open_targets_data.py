import sys
import os
import pandas as pd
import numpy as np
import logging
import csv
import requests
from contextlib import closing
from settings import Config

__copyright__ = "Copyright 2014-2018, Open Targets"
__credits__ = ["Gautier Koscielny"]
__license__ = "Apache 2.0"
__version__ = "1.0"
__maintainer__ = "Gautier Koscielny"
__email__ = "gautier.x.koscielny@gsk.com"
__status__ = "Production"


def read_from_url(url):

    with closing(requests.get(url, stream=True)) as r:
        # decoded_content = download.content.decode('utf-8')

        reader = csv.reader(r.iter_lines(), delimiter='\t', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        c = 0
        for row in reader:
            c += 1
            if c > 1:
                print(row)
            if c > 100:
                break

def merge_gene_annotations():

    hgnc_df = pd.read_csv(Config.GENE_ANNOTATION_FILES['hgnc_mappings'], sep='\t')
    hgnc_df['entrez_id'].astype(str)
    hgnc_df['uniprot_id'].astype(str)
    hgnc_df['locus_type'].astype(str)
    hgnc_df['locus_group'].astype(str)
    #print(hgnc_df[:5])

    goa_df = pd.read_csv(Config.GENE_ANNOTATION_FILES['go_annotations'], sep='\t')
    goa_df['entrez_id'].astype(str)
    goa_df['uniprot_id'].astype(str)
    #print(goa_df[:5])
    print("---------------")
    merge1 = pd.merge(hgnc_df, goa_df, how='left', on=['ensembl_gene_id', 'entrez_id', 'uniprot_id'])
    merge1['entrez_id'].astype(str)
    merge1['uniprot_id'].astype(str)
    merge1['go_id'].astype(str)
    merge1['go_label'].astype(str)
    merge1['evidence_type'].astype(str)

    '''
    merge protein classes when they exist
    '''
    protein_classes_df = pd.read_csv(Config.GENE_ANNOTATION_FILES['protein_classes'], sep='\t')
    protein_classes_df['entrez_id'].astype(str)
    protein_classes_df['uniprot_id'].astype(str)
    print(protein_classes_df[:5])
    print("---------------")

    df = pd.merge(merge1, protein_classes_df, how='left', on=['ensembl_gene_id', 'entrez_id', 'uniprot_id'])
    df['entrez_id'].astype(str)
    df['uniprot_id'].astype(str)
    df['go_id'].astype(str)
    df['go_label'].astype(str)
    df['evidence_type'].astype(str)
    df['protein_class'].astype(str)

    print(df.loc[df['symbol'] == 'NOD2'])
    print(len(df))

    '''
       write dataframe to csv
    '''
    df.to_csv(Config.GENE_ANNOTATION_FILES['output_gene_info'])


def merge_tissue_expression_location():

    gtex_df = pd.read_csv(Config.GENE_TISSUE_EXPRESSION['gtex'], sep='\t')
    # EntrezID	ENSEMBL_ID	Symbol	EFO	Label (OTv8_or_earlier)	Tissue	Max Fold Change
    gtex_df = gtex_df.rename(columns={'EntrezID': 'entrez_id',
                                      'ENSEMBL_ID': 'ensembl_gene_id',
                                      'Symbol': 'symbol',
                                      'EFO': 'disease_id',
                                      'Label (OTv8_or_earlier)': 'disease_label',
                                      'Max Fold Change': 'max_fold_change'})
    gtex_df['entrez_id'].astype(str)
    gtex_df['ensembl_gene_id'].astype(str)
    gtex_df['symbol'].astype(str)
    newdf = gtex_df.assign(source="GTExv6", tissue_label=gtex_df['Tissue'].apply(lambda x: x.split('_')[0]))
    newdf.tissue_label.str.replace("_GTExv6", "")
    newdf = newdf.drop('Tissue', 1)
    cols = newdf.columns.tolist()
    cols = cols[:5] + ['tissue_label', 'source'] + ['max_fold_change']
    print(cols)
    df = newdf[cols]
    print(df.loc[df['symbol'] == 'NOD2'])
    df.to_csv(Config.GENE_TISSUE_EXPRESSION['output_tissue_expression'])

def clean_disease_location():
    '''
    Read disease location and simplify
    '''
    df = pd.read_csv(Config.GENE_TISSUE_EXPRESSION['disease_location'], sep='\t')
    df = df.assign(disease_id=df['disease_iri'].apply(lambda x: x.split('/')[-1]), disease_location_id=df['disease_location_iri'].apply(lambda x: x.split('/')[-1]))
    df = df[['disease_id', 'disease_location_id', 'disease_location_label']]
    print(df[:10])
    df.to_csv(Config.GENE_TISSUE_EXPRESSION['output_disease_location'])

def parse_scoring_matrices():

    hgnc_df = pd.read_csv(Config.GENE_ANNOTATION_FILES['hgnc_mappings'], sep='\t')
    hgnc_df['entrez_id'].astype(str)
    hgnc_df['uniprot_id'].astype(str)
    entrez_df = hgnc_df[['ensembl_gene_id', 'entrez_id']]


    df = pd.read_csv(Config.SCORE_FILE_URLS['datasource_scores'])
    '''
    rename columns
    EnsemblId	Symbol	OntologyId	Label	Is direct	overall	expression_atlas	uniprot	gwas_catalog	phewas_catalog	eva	uniprot_literature	genomics_england	gene2phenotype	reactome	slapenrich	phenodigm	cancer_gene_census	eva_somatic	uniprot_somatic	intogen	chembl	europepmc
    '''
    df = df.rename(columns={
                            'EnsemblId': 'ensembl_gene_id',
                            'Symbol': 'symbol',
                            'OntologyId': 'disease_id',
                            'Label': 'disease_label',
                            'Is direct': 'direct_association',
                            'overall': 'overall_score'})

    df = pd.merge(df, entrez_df, how='left', on=['ensembl_gene_id'])
    cols = df.columns.tolist()
    print(cols)
    cols = cols[-1:] + cols[0:-1]
    print(cols)
    df = df[cols]
    hgnc_df['entrez_id'].astype(str)
    df.to_csv(Config.SCORE_FILE_URLS['output_datasource_scores'])
    # remove drug info from ChEMBL and overall score
    df = df.drop('chembl', 1)
    df = df.drop('overall_score', 1)
    df.to_csv(Config.SCORE_FILE_URLS['output_datasource_scores_nodrugs'])

    df = pd.read_csv(Config.SCORE_FILE_URLS['datatype_scores'])
    cols = df.columns.tolist()
    print(cols)

    '''
    "EnsemblId","Symbol","OntologyId","Label","Is direct","overall","genetic_association","somatic_mutation","known_drug","rna_expression","affected_pathway","animal_model","literature"
    '''
    df = df.rename(columns={
        'EnsemblId': 'ensembl_gene_id',
        'Symbol': 'symbol',
        'OntologyId': 'disease_id',
        'Label': 'disease_label',
        'Is direct': 'direct_association',
        'overall': 'overall_score'})

    df = pd.merge(df, entrez_df, how='left', on=['ensembl_gene_id'])
    cols = df.columns.tolist()
    print(cols)
    cols = cols[-1:] + cols[0:-1]
    print(cols)
    df = df[cols]
    hgnc_df['entrez_id'].astype(str)
    df.to_csv(Config.SCORE_FILE_URLS['output_datatype_scores'])
    df = df.drop('known_drug', 1)
    df = df.drop('overall_score', 1)
    df.to_csv(Config.SCORE_FILE_URLS['output_datatype_scores_nodrugs'])

def parse_pharmaprojects():
    df = pd.read_csv(Config.PHARMAPROJECTS['original_file'])
    df = df.drop('Target_Indication', 1)
    df = df.rename(columns={
        'Ensembl_ID': 'ensembl_gene_id',
        'EntrezGeneID': 'entrez_id',
        'EFO_ID': 'disease_id'})
    print(df[:10])
    df.to_csv(Config.PHARMAPROJECTS['output_pharmaprojects'])

def main():

    logging.basicConfig(format='%(levelname)s:%(message)s', level=logging.INFO)

    #merge_gene_annotations()
    #merge_tissue_expression_location()
    #clean_disease_location()
    #parse_scoring_matrices()
    parse_pharmaprojects()
    


if __name__ == "__main__":
    main()