import pip
import pdb

def import_or_install(package):
    try:
        __import__(package)
    except ImportError:
        pip.main(['install', package])


import_or_install('pandas')
import pandas as pd
import_or_install('glob')
import glob
import_or_install('argparse')
import argparse
import_or_install('striprtf')
from striprtf.striprtf import rtf_to_text

def process_file(text, f):
    header_names, reports = text.split('Report Text')[:2]
    header_names = [t.replace(' ','').lower() for t in header_names.split(';') if len(t)>0]
    header_names = [t for t in header_names if len(t)>0]
    header_len = len(header_names)
    reports = [r for r in reports.split('<REPORT_END>') if '<REPORT_START>' in r]
    headers = []
    processed_reports = []
    for r in reports:
        header, report = process_report(r, header_len,f)
        headers += [header]
        processed_reports += [report]
    merged_header = merge_header(header_names, headers)
    merged_reports = merge_report(header_names, headers, processed_reports)
    return merged_header, merged_reports

def merge_header(header_names, headers):
    df = pd.DataFrame(headers)
    df.columns = header_names
    return df

def merge_report(header_names, headers, processed_reports):
    header = [{header_names[i]:h[i] for i in range(len(h))} for h in headers]
    for i in range(len(processed_reports)):
        header[i].update(processed_reports[i])
    df = pd.DataFrame(header)
    return df

def process_report(text, header_len,f):
    header, report  =  text.split('<REPORT_START>')[:2]
    header = [h for h in header.replace('\n','').replace('\t','').split(';') if len(h)>0]
    if len(header) != header_len:
        header = header[:header_len]
    processed_report = process_text(report,f)
    return header, processed_report

def check_key_occ(dic,key):
    ind = 0
    for k in dic.keys():
        if key in k:
            ind += 1
    return ind

def process_text(text,f ):
    lines = text.split('\n')
    dic = {}
    prefix = 'Init'
    dic['filename'] = f.split('/')[-1]
    for l in range(len(lines)):
        if ":" in lines[l] and lines[l].split(":")[1].__len__() > 0:
            left,right = lines[l].split(":")[0],lines[l].split(":")[1]
            ind = str(check_key_occ(dic,prefix.replace(" ",'') + "_"+left))
            if len(prefix) == 0:
                dic[left.replace(" ","").replace("\"","")] = right
            else:
                dic[prefix + "_"+left.replace(" ","").replace("\"","")] = right
        elif "\t" not in lines[l] and lines[l] != "":
            prefix = lines[l].replace('"\t',"").replace('\t','').replace(' ','')
        elif "\t" in lines[l] and lines[l] != '\t':
            if not prefix in dic.keys():
                dic[prefix] = ""
            dic[prefix] += lines[l].replace('"\t',"").replace('\t','').replace('\"','').replace('  ','')
        elif lines[l] == "":
            if (l+1 != len(lines)) and lines[l+1] == '':
                prefix = ''
    return dic

def process_files(file_dir,name):
    files = sorted(glob.glob('{}/*.rtf'.format(file_dir)))

    l_headers = []
    l_reports = []
    for f in files:
        if '\n' in rtf_to_text(open(f).read()):
            a = process_file(rtf_to_text(open(f).read()),f)
        else:
            a = process_file(rtf_to_text(open(f).read()),f)
        l_headers += [a[0]]
        l_reports += [a[1]]
    pd.concat(l_reports).to_csv('{}/full.csv'.format(name))
    pd.concat(l_headers).to_csv('{}/headers.csv'.format(name))

if __name__ == '__main__':
	parser = argparse.ArgumentParser(description='Process some integers.')
	parser.add_argument('--report_dir', type=str, default='',
	                    help='path to reports')
	parser.add_argument('--target_dir', type=str, default='',
	                    help='path to store entries')

	args = parser.parse_args()

	process_files(args.report_dir,args.target_dir)
