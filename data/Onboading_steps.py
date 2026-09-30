import polars as pL
import matplotlib.pyplot as plt
import pyarrow.parquet as pq


pd = pL.read_parquet("C:\\Users\\Administrator\\fs-5-software-intro-projects\\data\\software-data.parquet")

pd.fill_null(strategy="forward")

print(pd)