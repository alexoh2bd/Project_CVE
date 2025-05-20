import pandas as pd
from typing import Dict, Any
from loguru import logger
from tqdm import tqdm
import os
import ast
from concurrent.futures import ProcessPoolExecutor, as_completed
import functools
import itertools
from config import PROCESSED_DATA_DIR
import gc


def process_cve_data(cve_data: Dict[str, Any]) -> None:
    cve_entry = cve_data.get("cve", {})

    # 1. Main CVE DataFrame

    main_df = pd.DataFrame(
        [
            {
                "cve_id": cve_entry.get("id"),
                "source_identifier": cve_entry.get("sourceIdentifier"),
                "published_date": cve_entry.get("published"),
                "last_modified_date": cve_entry.get("lastModified"),
                "vuln_status": cve_entry.get("vulnStatus"),
            }
        ]
    )

    # 2. Descriptions DataFrame (for multiple languages)
    descriptions = []
    for desc in cve_entry.get("descriptions", []):
        descriptions.append(
            {
                "cve_id": cve_entry.get("id"),
                "lang": desc.get("lang"),
                "description": desc.get("value"),
            }
        )
    descriptions_df = pd.DataFrame(descriptions) if descriptions else pd.DataFrame()

    # 3. CVSS v3.1 Metrics DataFrame
    cvss_v3_metrics = []
    for metric in cve_entry.get("metrics", {}).get("cvssMetricV31", []):
        cvss_data = metric.get("cvssData", {})
        cvss_v3_metrics.append(
            {
                "cve_id": cve_entry.get("id"),
                "source": metric.get("source"),
                "type": metric.get("type"),
                "version": cvss_data.get("version"),
                "vector_string": cvss_data.get("vectorString"),
                "base_score": cvss_data.get("baseScore"),
                "base_severity": cvss_data.get("baseSeverity"),
                "attack_vector": cvss_data.get("attackVector"),
                "attack_complexity": cvss_data.get("attackComplexity"),
                "privileges_required": cvss_data.get("privilegesRequired"),
                "user_interaction": cvss_data.get("userInteraction"),
                "scope": cvss_data.get("scope"),
                "confidentiality_impact": cvss_data.get("confidentialityImpact"),
                "integrity_impact": cvss_data.get("integrityImpact"),
                "availability_impact": cvss_data.get("availabilityImpact"),
                "exploitability_score": metric.get("exploitabilityScore"),
                "impact_score": metric.get("impactScore"),
            }
        )
    cvss_v3_df = pd.DataFrame(cvss_v3_metrics) if cvss_v3_metrics else pd.DataFrame()

    # 4. CVSS v2 Metrics DataFrame
    cvss_v2_metrics = []
    for metric in cve_entry.get("metrics", {}).get("cvssMetricV2", []):
        cvss_data = metric.get("cvssData", {})
        cvss_v2_metrics.append(
            {
                "cve_id": cve_entry.get("id"),
                "source": metric.get("source"),
                "type": metric.get("type"),
                "version": cvss_data.get("version"),
                "vector_string": cvss_data.get("vectorString"),
                "base_score": cvss_data.get("baseScore"),
                "base_severity": metric.get("baseSeverity"),
                "access_vector": cvss_data.get("accessVector"),
                "access_complexity": cvss_data.get("accessComplexity"),
                "authentication": cvss_data.get("authentication"),
                "confidentiality_impact": cvss_data.get("confidentialityImpact"),
                "integrity_impact": cvss_data.get("integrityImpact"),
                "availability_impact": cvss_data.get("availabilityImpact"),
                "exploitability_score": metric.get("exploitabilityScore"),
                "impact_score": metric.get("impactScore"),
                "ac_insuf_info": metric.get("acInsufInfo"),
                "obtain_all_privilege": metric.get("obtainAllPrivilege"),
                "obtain_user_privilege": metric.get("obtainUserPrivilege"),
                "obtain_other_privilege": metric.get("obtainOtherPrivilege"),
                "user_interaction_required": metric.get("userInteractionRequired"),
            }
        )
    cvss_v2_df = pd.DataFrame(cvss_v2_metrics) if cvss_v2_metrics else pd.DataFrame()

    # 5. Weaknesses DataFrame
    weaknesses = []
    for weakness in cve_entry.get("weaknesses", []):
        for desc in weakness.get("description", []):
            weaknesses.append(
                {
                    "cve_id": cve_entry.get("id"),
                    "source": weakness.get("source"),
                    "type": weakness.get("type"),
                    "lang": desc.get("lang"),
                    "cwe_id": desc.get("value"),  # Often contains CWE ID
                }
            )
    weaknesses_df = pd.DataFrame(weaknesses) if weaknesses else pd.DataFrame()

    # 6. CPE (Affected Products) DataFrame
    affected_products = []
    for config in cve_entry.get("configurations", []):
        for node in config.get("nodes", []):
            for cpe_match in node.get("cpeMatch", []):
                affected_products.append(
                    {
                        "cve_id": cve_entry.get("id"),
                        "vulnerable": cpe_match.get("vulnerable"),
                        "criteria": cpe_match.get("criteria"),
                        "version_end_including": cpe_match.get("versionEndIncluding"),
                        "match_criteria_id": cpe_match.get("matchCriteriaId"),
                    }
                )
    cpe_df = pd.DataFrame(affected_products) if affected_products else pd.DataFrame()

    # 7. References DataFrame
    references = []
    for ref in cve_entry.get("references", []):
        references.append(
            {
                "cve_id": cve_entry.get("id"),
                "url": ref.get("url"),
                "source": ref.get("source"),
                "tags": ", ".join(
                    ref.get("tags", [])
                ),  # Combine tags into a single string
            }
        )
    references_df = pd.DataFrame(references) if references else pd.DataFrame()
    result = {
        "main": main_df,
        "descriptions": descriptions_df,
        "cvss_v3": cvss_v3_df,
        "cvss_v2": cvss_v2_df,
        "weaknesses": weaknesses_df,
        "affected_products": cpe_df,
        "references": references_df,
    }

    # Return all DataFrames in a dictionary
    return result


def process_batch(batch: Dict, output_path=PROCESSED_DATA_DIR, batch_idx=None):
    """
    Processes a batch of cve_data at once in increments
    Args:
        batch: list of CVE data dictionaries
        output_path: Optional path of output saved file
        batch_idx: Optional index of batch
    Returns:
        Dictionary of DataFrames or None if saving to File
    """

    batch_dfs = {}
    file_paths = []

    # try:
    # Process each CVE in the batch
    for cve_data in tqdm(batch):

        cve_dfs = process_cve_data(cve_data)
        # logger.info(f"cve_dfs {cve_dfs.items()}")

        for name, df in cve_dfs.items():
            # logger.info(f"name: {name} + df: {type(df)}")

            if name not in batch_dfs:
                batch_dfs[name] = pd.DataFrame(df)
            else:
                batch_dfs[name] = pd.concat(
                    [batch_dfs[name], pd.DataFrame(df)], ignore_index=True
                )

    for key, val in batch_dfs.items():
        file_path = os.path.join(output_path, f"{key}_batch{batch_idx}.csv")
        val.to_csv(file_path, index=False)
        file_paths.append(file_path)
        # logger.info(f"Saved {file_path} with {len(val)} rows")
    del batch_dfs
    # except Exception as e:
    #     logger.info(f"Error processing CVE: {str(e)}", exc_info=True)
    gc.collect()
    return file_paths


def process_cve_batches(
    df,
    column_name="vulnerabilities",
    batch_size=1000,
    output_path=None,
    n_workers=None,
    incremental_save=True,
):
    """
    Process CVE data from API Request in batches

    Args:
        df: Input DataFrame containing CVE data in string format
        column_name: "vulnerabilities
        batch_size: # of CVEs per batch
        n_workers: Number of worker Processes
        incremental_save: Whether to save Results incrementally

    Returns:
        Dict of combined DataFrames
    """

    # Extract CVEs through apply mehtod
    logger.info(f"Extracting CVE {column_name} column from Dataframe")

    # Extract Vulnerabilities Column dictionary
    cve_list = []
    for i in tqdm(range(len(df))):
        cve_list.extend(ast.literal_eval(df[column_name][i]))

    # Batch Extracted CVE entries from the DataFrame
    logger.info(f"Extracted {len(cve_list)} CVE entries from the DataFrame")
    logger.info(cve_list[0])
    batches = [
        cve_list[i : i + batch_size] for i in range(len(cve_list) // batch_size + 1)
    ]
    logger.info(f"Split CVEs into {len(batches)} batches of size {batch_size}")

    # Use concurrent.futures' Process Pool Executor to run processes in parallel
    if incremental_save and output_path:
        if n_workers and n_workers > 1:
            # Parallel Processing
            with ProcessPoolExecutor(max_workers=n_workers) as exec:
                process_fn = functools.partial(process_batch)
                futures = [
                    exec.submit(process_fn, batch, batch_idx=i)
                    for i, batch in tqdm(enumerate(batches))
                ]
                for future in as_completed(futures):
                    try:
                        file_paths = future.result()
                    except Exception as e:
                        logger.error(f"Batch Processsing error: {e}")
        else:
            logger.info("Processing Batches Sequentially")
            for i, batch in enumerate(tqdm(batches)):
                process_batch(batch, output_path, i)

        return
    else:
        logger.info("Not Processing Today")
        return


def merge_batch_results(input_path, output_path):
    """
    Merge batch CSV files in the output directory into combined files.

    Args:
        output_path: Directory containing batch CSV files
    """
    logger.info(f"Merging batch results in {input_path}")

    # Get all CSV files
    csv_files = [f for f in os.listdir(input_path) if f.endswith(".csv")]
    # logger.info(csv_files)
    # divide csv files into groups
    csv_groups = {}
    for file in csv_files:
        chunks = file.split("_batch")
        if chunks[0] not in csv_groups:
            csv_groups[chunks[0]] = [file]
        else:
            csv_groups[chunks[0]].append(file)

    for group, files in tqdm(csv_groups.items()):
        logger.info(f"Merging {len(files)} files for {group}")
        dfs = []

        for file in files:
            file_path = os.path.join(input_path, file)
            try:
                df = pd.read_csv(file_path)
                dfs.append(df)
            except Exception as e:
                logger.error(f"Error reading {file_path}: {e}")
        if dfs:
            combined_df = pd.concat(dfs, ignore_index=True)
            if "cve_id" in combined_df.columns:
                initial_len = len(combined_df)
                if group == "main":
                    combined_df = combined_df.drop_duplicates(subset=["cve_id"])

                else:
                    if "cve_id" in combined_df.columns:
                        combined_df = combined_df.drop_duplicates()

                if initial_len > len(combined_df):
                    logger.info(
                        f"Removed {initial_len} with  {len(combined_df)} rows. "
                    )

            combined_path = os.path.join(output_path, f"{group}_combined.csv")
            combined_df.to_csv(combined_path)
            logger.info(
                f"Saved combined file {combined_path} with {len(combined_df)} rows. "
            )
            del dfs, combined_df
    logger.info(f"Completed Merge of {len(csv_files)} Files.")
