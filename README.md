# HGEN 47000: Human Genetics I: eQTL Workshop

## Installation Instructions
### Download htslib & bcftools
`wget http://sourceforge.net/projects/samtools/files/samtools/1.2/htslib-1.2.1.tar.bz2` \
`wget http://sourceforge.net/projects/samtools/files/samtools/1.2/bcftools-1.2.tar.bz2`

### Clone the eQTL_workshop directory
`git clone https://github.com/ankeetashah/eQTL_workshop.git`

### Unpack tabix and bgzip
`tar xvjf htslib-1.2.1.tar.bz2` \
`cd htslib-1.2.1` \
`make`

### Move tabix and bgzip into eQTL_workshop/bin directory
Of note, you will have to use `pwd` to determine where you downloaded the `eQTL_workshop` on your laptop. For example, I have the directory on my Desktop: \
`mv tabix /Users/ankeetashah/Desktop/eQTL_workshop/bin/.` \
`mv bgzip /Users/ankeetashah/Desktop/eQTL_workshop/bin/.` 

### I will demo running FastQTL (Ongen et al., Bioinformatics, 2016) on a Linux server. Unfortunately, most of you will run into issues installing FastQTL on Mac and Windows systems (though you are welcome to try!)
Download Page: http://fastqtl.sourceforge.net/

