import wget
import fnmatch
import os
import gzip
import boto3
import sys
import shutil
from zipfile import ZipFile

# define variáveis e cria diretorios de trabalho
zipdir = "zips"
outdir = "microdados"
unrarexec = "/home/ec2-user/SageMaker/sagemaker/rar/unrar"
list_arq = [
    "microdados_enem2012",
    "microdados_enem2013",
    # "microdados_enem2014",
    # "microdados_enem2015",
    # "microdados_enem2016",
    # "microdados_enem2017",
    # "microdados_enem2018",
    # "microdados_enem_2019",
]
bucket = "data-bucket"
folder = "data"

print(list_arq)
os.mkdir(zipdir)
os.mkdir(outdir)


# status do download wget
def bar_custom(current, total, width=80):
    progress_message = "Downloading: %d%% [%d / %d] bytes" % (
        current / total * 100,
        current,
        total,
    )
    sys.stdout.write("\r" + progress_message)


# converte pra utf8 e comprime
def convert_compress_file(csvfile):
    year = csvfile[-8:-4]
    filenameout = "microdados/MICRODADOS_ENEM_" + year + ".csv.gz"
    print(
        "Convertendo "
        + csvfile
        + " para utf-8 e compactando para "
        + filenameout
        + "..."
    )

    # converte, compacta e remove aspas se for o caso
    with open(csvfile, encoding="cp1252") as filein, gzip.open(
        filenameout, "wt", encoding="utf8"
    ) as fileout:
        for line in filein:
            fileout.write(line.replace('"', ""))
    os.remove(csvfile)
    return filenameout


# carrega dados no bucket
def upload_s3(upfile, bucket, folder):
    year = upfile[-11:-7]
    s3 = boto3.resource("s3")
    data = open(upfile, "rb")
    key = folder + "/enem_microdados_" + year + "/" + os.path.basename(upfile)
    print("Carregando " + key + " para o bucket " + bucket)
    s3.Bucket(bucket).put_object(Key=key, Body=data)


# transformação e upload do arquivo csv
def microdados_transform(microfile):
    pattern1 = "*/DADOS_*.csv"
    pattern2 = "*/[Mm][Ii][Cc][Rr][Oo]*.csv"

    with ZipFile(microfile, "r") as zipObj:
        listOfiles = zipObj.namelist()
        # Se for arquivo rar
        if fnmatch.filter(listOfiles, "*.rar"):
            rarfile = fnmatch.filter(listOfiles, "*.rar")[0]
            print("Arquivo rar " + rarfile)
            zipObj.extractall()
            unrarlb = unrarexec + " lb " + rarfile + " | grep MICRO | grep csv"
            extractfile = os.popen(unrarlb).readline().rstrip("\r\n")
            print("Extraindo arquivo " + extractfile)
            print(unrarexec + " e " + rarfile + " " + extractfile)
            os.system(unrarexec + " e " + rarfile + " " + extractfile)
            print("Movendo arquivo para pasta microdados")
            finalfile = "microdados/" + os.path.basename(extractfile)
            os.rename(os.path.basename(extractfile), finalfile)
            os.remove(rarfile)
        else:
            for extractfile in fnmatch.filter(listOfiles, "*.csv"):
                if fnmatch.fnmatch(extractfile, pattern1) or fnmatch.fnmatch(
                    extractfile, pattern2
                ):
                    print("Arquivo zip " + microfile)
                    print("Extraindo arquivo " + extractfile)
                    zipObj.extract(extractfile)
                    print("Movendo arquivo para pasta microdados")
                    finalfile = "microdados/" + os.path.basename(extractfile)
                    os.rename(extractfile, finalfile)
                    basepath = extractfile.split("/")[0]
                    print("Removendo " + basepath)
                    shutil.rmtree(basepath)
    return finalfile


# Download dos arquivos (com base em list_arq)
for item in list_arq:
    year = item[-4:]
    if os.path.isfile("zips/" + item + ".zip"):
        print("arquivo " + item + ".zip já existe")
    else:
        print("carregando arquivo " + item + "...")
        url = "http://download.inep.gov.br/microdados/" + item + ".zip"
        wget.download(url, bar=bar_custom, out="zips")
        print(" ok")

print("fim dos downloads")


# loop completo
for filename in sorted(os.listdir("zips")):
    print(">>Processando zips/" + filename)
    # extraindo arquivo csv
    result_tr = microdados_transform("zips/" + filename)

    # convertendo e comprimindo
    result_conv = convert_compress_file(result_tr)

    # enviando para o bucket s3
    upload_s3(result_conv, bucket, folder)
