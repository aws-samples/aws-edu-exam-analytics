import boto3
import awswrangler as wr
import pandas as pd

# setup vars
boto3.setup_default_session(region_name="us-east-1")
bucket = "martinig-inep-data"  # your bucket name
raw_database = "inep_data_db"  # your Glue database name

# reading raw data
print("downloading dataframes...")
query = """
(select     nu_inscricao, nu_ano, uf_insc as uf_residencia, case tp_sexo when 0 then 'M' when 1 then 'F' end as tp_sexo, idade, nu_nota_redacao,
        nu_nt_cn as nu_nota_cn, nu_nt_ch as nu_nota_ch, nu_nt_lc as nu_nota_lc, nu_nt_mt as nu_nota_mt
from enem_microdados_2012 limit 10)
UNION
(select     nu_inscricao, nu_ano, uf_residencia, tp_sexo, idade, nu_nota_redacao,
        nota_cn as nu_nota_cn, nota_ch as nu_nota_ch, nota_lc as nu_nota_lc, nota_mt as nu_nota_mt
from enem_microdados_2013 limit 10)
"""

df_summary = wr.athena.read_sql_query(query, database=raw_database)

# storing data
print("storing data...")
wr.s3.to_parquet(
    df=df_summary,
    dataset=True,
    path=f"s3://{bucket}/data/enem_microdados_summary/"
)

print("parquet stored...")
