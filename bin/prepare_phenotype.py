import sys
import gzip
import numpy as np
import scipy as sc
import pickle

from optparse import OptionParser
    
from sklearn.decomposition import PCA
from sklearn import preprocessing
from sklearn import linear_model

from scipy.stats import rankdata
from scipy.stats import norm

def qqnorm(x):
    n=len(x)
    a=3.0/8.0 if n<=10 else 0.5
    return(norm.ppf( (rankdata(x)-a)/(n+1.0-2.0*a) ))

def stream_table(f, ss = ''):
    fc = '#'
    while fc[0] == "#":
        fc = f.readline().strip()
        head = fc.split(ss)

    for ln in f:
        ln = ln.strip().split(ss)
        attr = {}

        for i in range(len(head)):
            try: attr[head[i]] = ln[i]
            except: break
        yield attr

def main(ratio_file, pcs=50):
    
    dic_pop, fout = {}, {}
    try: open(ratio_file)
    except: 
        sys.stderr.write("Can't find %s..exiting\n"%(ratio_file))
        return

    sys.stderr.write("Starting...\n")
    for i in range(1,23):
        fout[i] = file(ratio_file+".phen_chr%d"%i,'w')
        fout_ave = file(ratio_file+".ave",'w')
    valRows, valRowsnn, geneRows = [], [], []
    finished = False
    header = open(ratio_file).readline().split()[1:]


    for i in fout:
        fout[i].write("\t".join(["#Chr","start", "end", "ID"]+header)+'\n')

    for dic in stream_table(open(ratio_file),' '):

        chrom = dic['chrom'].replace("chr",'')
        chr_ = chrom.split(":")[0]
        if chr_ in 'XY': continue
        NA_indices, valRow, aveReads = [], [], []
        tmpvalRow = []

        i = 0
        for sample in header:

            try: count = dic[sample]
            except: print chrom, len(dic)
            #num, denom = count.split('/')
            #if float(denom) < 1:
             #   count = "NA"
              #  tmpvalRow.append("NA")
               # NA_indices.append(i)
            #else:
                # add a 0.5 pseudocount
             #   count = (float(num)+0.5)/((float(denom))+0.5)
            tmpvalRow.append(count) 
            aveReads.append(count)
	    #print tmpvalRow
	    #print  aveReads


        # If ratio is missing for over 40% of the samples, skip
        if tmpvalRow.count("NA") > len(tmpvalRow)*0.4:
            continue

	tmpvalRow = [float(i) for i in tmpvalRow]
	aveReads = [float(i) for i in aveReads]


	#print np.mean(aveReads)
        ave = np.mean(aveReads)

        # Set missing values as the mean of all values
        for c in tmpvalRow:
            if c == "NA": valRow.append(ave)
            else: valRow.append(c)

        # If there is too little variation, skip (there is a bug in fastqtl which doesn't handle cases with no variation)
        if np.std(valRow) < 0.005: continue

	#print chrom
        chr_, s, e, gene, strand = chrom.split(":")#added strand info 
        #strand = clu.split("_")[1] #strand 
	#clu = clu.split("_")[0]
	#clu = clu.split("_")[0] + "_" + clu.split("_")[1]
	if len(valRow) > 0 and (chr_ !='M'):
	    
            chrom_int = int(chr_)
            fout[chrom_int].write("\t".join([chr_,s,e,chrom]+[str(x) for x in valRow])+'\n')
            fout_ave.write(" ".join(["%s"%chrom]+[str(min(aveReads)), str(max(aveReads)), str(np.mean(aveReads))])+'\n')

            # scale normalize
            valRowsnn.append(valRow)                
            valRow = preprocessing.scale(valRow)

            valRows.append(valRow)
            geneRows.append("\t".join([chr_,s,e,chrom]))
            if len(geneRows) % 1000 == 0:
                sys.stderr.write("Parsed %s introns...\n"%len(geneRows))
                
    for i in fout:
        fout[i].close()

    # qqnorms on the columns
    matrix = np.array(valRows)
    for i in xrange(len(matrix[0,:])):
        matrix[:,i] = qqnorm(matrix[:,i])
        
    # write the corrected tables
    fout = {}
    for i in range(1,23):
        fn="%s.qqnorm_chr%d"%(ratio_file,i)
        print("Outputting: " + fn)
        fout[i] = file(fn,'w')
        fout[i].write("\t".join(['#Chr','start','end','ID'] + header)+'\n')
    lst = []
    for i in xrange(len(matrix)):
        chrom, s = geneRows[i].split()[:2]
        
        lst.append((int(chrom.replace("chr","")), int(s), "\t".join([geneRows[i]] + [str(x) for x in  matrix[i]])+'\n'))

    lst.sort()
    for ln in lst:
        fout[ln[0]].write(ln[2])
        
    fout_run = file("%s_prepare.sh"%ratio_file,'w')

    for i in fout:
        fout[i].close()
        fout_run.write("bin/./bgzip -f %s.qqnorm_chr%d\n"%(ratio_file, i))
        fout_run.write("bin/./tabix -p bed %s.qqnorm_chr%d.gz\n"%(ratio_file, i))
    fout_run.close()

    sys.stdout.write("Use `sh %s_prepare.sh' to create index for fastQTL (requires tabix and bgzip).\n"%ratio_file)

    if pcs>0:
        #matrix = np.transpose(matrix) # important bug fix (removed as of Jan 1 2018)
        pcs = min([len(header), pcs])
        pca = PCA(n_components=pcs)                                                                                                                                                                            
        pca.fit(matrix)  
        pca_fn=ratio_file+".PCs"
        print("Outputting PCs: " + pca_fn)
        pcafile = file(pca_fn,'w')  
        pcafile.write("\t".join(['id']+header)+'\n')
        pcacomp = list(pca.components_)
    
        for i in range(len(pcacomp)):
            pcafile.write("\t".join([str(i+1)]+[str(x) for x in pcacomp[i]])+'\n')

        pcafile.close()

if __name__ == "__main__":

    parser = OptionParser(usage="usage: %prog [-p num_PCs] input_perind.counts.gz")
    parser.add_option("-p", "--pcs", dest="npcs", default = 50, help="number of PCs output")
    (options, args) = parser.parse_args()
    if len(args)==0:
        sys.stderr.write("Error: no ratio file provided... (e.g. python prepare_phenotype.py input_perind.counts.gz\n")
        exit(0)
    main(args[0], int(options.npcs) )
    
