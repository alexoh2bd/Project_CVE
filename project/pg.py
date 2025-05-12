import pandas as pd
from config import RAW_DATA_DIR

nvd = pd.read_csv(f"{RAW_DATA_DIR}/kev.csv")
kev = pd.read_csv(f"{RAW_DATA_DIR}/known_exploited_vulnerabilities.csv")
nvd["exploited"] = nvd["cveID"].isin(kev["cveID"]).astype(int)
df = pd.merge(nvd, kev, on="cveID", how="inner")
df.to_csv(f"{RAW_DATA_DIR}/kevCVE.csv")


# print(df.drop("Unnamed: 0"))
features = [
    "product",
    "timestamp",
    "version",
    "format",
    "error",
    "startIndex",
    "totalResults",
    "resultsPerPage",
]

# df.drop(features, axis=1, inplace=True)
print(df)
print(df.columns)
# print(
#     f"{nvd["vulnerabilityName"][0]} {nvd["shortDescription"][0]} {nvd['requiredAction'][0]}"
# )
