rmdir /s/q .\samples\
mkdir samples


python .\src\index_gen.py -i -v 1000

python .\src\convert_raw.py -l --srcdir=raw_data --dstdir=samples
python .\src\pc-analyzer.py --mode=weight_center --srcdir=samples -f