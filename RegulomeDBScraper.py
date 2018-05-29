# -*- coding: utf-8 -*-
"""
Created on Mon Nov 14 15:58:11 2016

@author: moizba

This script is designed to analyze large sets of variants by subjecting them to interpretation via
RegulomeDB, which is unable to handle such massive sets on its own. It appears to only take in about
1000/session. This script will open a new file (regulome_IDs.txt), then open the input file. It 
loops through the input file and appends each line into a list of strings called "lines". Once there
are 101 variants in each chunk, it submits them to regulomeDB using the requests module. This will
return the text contents of a 'bed' file (chosen for its simplicity to parse). These 'bed' contents
are then appended to 'File_compiler". Once this has been completed, the script will then loop
through each chunk in file compiler and using regex, write them in the correct format to our output file.

This specific script has been designed for ZeroCoords input, although support for other forms 
can be added in the future. 

"""
from optparse import OptionParser
import requests, re

def submit_regulome(lines):
    """ Formates the set of SNP data (lines) into a format suitable for RegulomeDB.
        Sends a query to regulomeDB and returns the input using the results ID
    """
    d_format = 'bed' #options are 'full', 'gff', or 'bed', bed used due to easiness of parsing
    query = {'data': lines}
  
    r = requests.post('http://www.regulomedb.org/results', query)
    # Need to get sid which is associated with output
    sid = re.findall('name="sid" value="(.*?)"', r.text)

    download_file = {'format':d_format,'sid':sid}
    z = requests.post('http://www.regulomedb.org/download', download_file)
    print (z.text)
    return (z.text)

def annotate_variants(input_file, outputfile):
    
    """ This will take in the big list of SNPs, break them into subsets of <= 100 lines
        and pass them into the "submit_regulome" function for annotation. This is due to the inability
        of regulomeDB to take in querys larger than 100 lines. It will then append the annotations together
        into a new file.
        Sends a query to regulomeDB and returns the input using the results ID
    """

    file_compiler = []
    lines = ''
    
    #open file and set up the headers
    with open(outputfile, "w") as code:
        code.write("ID" + "\t" + "Regulome Score" +"\t" + "dbSNP" + "\n")
    
        with open(input_file, "r") as data_file:
            for line in data_file:
                # keep concatenating lines until we reach 101 lines (max before error)
                lines = lines + line
                if len(str.splitlines(lines)) > 100:
                    # get the annotations and append to file compiler, which is a list of strings
                    # each string in file compiler has scores for the files we input
                    file_compiler.append(submit_regulome(lines))
                    lines = ''
            if (len(str.splitlines(lines[1:]))>0): 
                file_compiler.append(submit_regulome(lines))
    
        for chunk in file_compiler:
            for e in str.splitlines(chunk):
           # this grabs the chromosome        
                chrom = (re.search('(.+?)\t',e)).group(1)
                if 'n/a' in e: #some variants do not have an associate DBSNP ID
                    score =  re.search('\tn/a;(.+?$)',e)
                    # this will get the position coordinates
                    position = (re.search('\t(.+?)\tn/a',e)).group(1).replace('\t','-')
                    name = chrom + ':' + position
                    code.write(name + "\t" + score.group(1) +"\n")
            
                else: #if variant does have a dbSNP ID 
                    SNPnum = re.search('\\trs(.+?);',e)
                    SNP = "rs"+SNPnum.group(1)
                    score = re.search(SNP+";(.+?$)",e)
                    position = (re.search('\t(.+?)\trs',e)).group(1).replace('\t','-')            
                    name = chrom + ':' + position
                    code.write(name + "\t" + score.group(1) +"\t"+ SNP +"\n")

def extract_Options():
    """ Prompts users to define file locations"""
    
    parser = OptionParser()
    parser.add_option("--I", dest = "input", 
                      help = "Input file location. Please make sure it is a list of variants in 0-based format", 
                      metavar="FILE", 
                      type = "string", 
                      default = r"...\RegulomeDB\Input\zero_coords_target_chr6.txt")
    parser.add_option("--O", dest = "output", help = "Outfile destination",
                      metavar = "FILE", 
                      type = "string", 
                      default = r"....\RegulomeDB\Output\Regulome_Scored_Variants.txt")
    # Format is currently non functional
    parser.add_option("--F", dest = "input_format", 
                      help = "Input file format (dbSNP, 0-based, etc.)", 
                      type = "string", 
                      default = "zero")
    (options, args) = parser.parse_args()
    return options
    
def main():
    options = extract_Options()
    annotate_variants(options.input, options.output)
    
main()
    

    
                    


