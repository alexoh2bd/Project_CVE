import pandas as pd
import aiohttp
import asyncio
import time
from tqdm.auto import tqdm
import logging
from typing import List, Dict, Any, Callable, Optional
import backoff


class PublicAPIBatchProcessor:
    """
    Process large batches of public API calls efficiently.
    """

    def __init__(
        self,
        base_url: str,
        max_concurrent_requests: int = 10,
        rate_limit_per_minute: int = 60,
        timeout: int = 30,
        retries: int = 3,
    ):
        """
        Initialize the batch processor.

        Args:
            base_url: Base URL for API calls
            max_concurrent_requests: Maximum number of concurrent requests
            rate_limit_per_minute: Maximum requests per minute
            timeout: Timeout for each request in seconds
            retries: Number of retries for failed requests
        """
        self.base_url = base_url
        self.max_concurrent_requests = max_concurrent_requests
        self.rate_limit_per_minute = rate_limit_per_minute
        self.timeout = timeout
        self.retries = retries
        self.request_interval = 60 / rate_limit_per_minute
        self.last_request_time = 0

        # Configure logging
        logging.basicConfig(
            level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
        )
        self.logger = logging.getLogger(__name__)

    async def _make_request(
        self,
        session: aiohttp.ClientSession,
        endpoint: str,
        item_value: Any,
        param_name: str,
        additional_params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Make a single API request with exponential backoff for retries.

        Args:
            session: aiohttp client session
            endpoint: API endpoint
            item_value: Value to query for
            param_name: Name of the parameter to use in the API call
            additional_params: Additional query parameters

        Returns:
            API response as dictionary
        """
        url = f"{self.base_url}/{endpoint}"

        params = {param_name: item_value}
        if additional_params:
            params.update(additional_params)

        # Implement rate limiting
        current_time = time.time()
        time_since_last_request = current_time - self.last_request_time
        if time_since_last_request < self.request_interval:
            await asyncio.sleep(self.request_interval - time_since_last_request)

        self.last_request_time = time.time()

        @backoff.on_exception(
            backoff.expo,
            (aiohttp.ClientError, asyncio.TimeoutError),
            max_tries=self.retries + 1,
            max_time=self.timeout * (self.retries + 1),
        )
        async def _request_with_retry():
            async with session.get(
                url, params=params, timeout=aiohttp.ClientTimeout(total=self.timeout)
            ) as response:
                response.raise_for_status()
                result = await response.json()
                # Include the original item value in the result for mapping back
                return {"item_value": item_value, "response": result}

        try:
            return await _request_with_retry()
        except Exception as e:
            self.logger.error(f"Failed to process item {item_value}: {str(e)}")
            return {"item_value": item_value, "error": str(e)}

    async def _process_batch(
        self,
        items: List[Any],
        endpoint: str,
        param_name: str,
        additional_params: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Process a batch of items concurrently.

        Args:
            items: List of values to query for
            endpoint: API endpoint
            param_name: Name of the parameter to use in the API call
            additional_params: Additional query parameters

        Returns:
            List of API responses
        """
        connector = aiohttp.TCPConnector(limit=self.max_concurrent_requests)
        async with aiohttp.ClientSession(connector=connector) as session:
            tasks = []
            for item in items:
                task = self._make_request(
                    session, endpoint, item, param_name, additional_params
                )
                tasks.append(task)

            # Process requests with tqdm progress bar
            results = []
            for future in tqdm(
                asyncio.as_completed(tasks),
                total=len(tasks),
                desc="Processing API calls",
            ):
                result = await future
                results.append(result)

            return results

    def process_dataframe(
        self,
        df: pd.DataFrame,
        column_name: str,
        endpoint: str,
        param_name: str,
        batch_size: int = 100,
        additional_params: Optional[Dict[str, Any]] = None,
        result_handler: Optional[Callable[[List[Dict[str, Any]]], pd.DataFrame]] = None,
    ) -> pd.DataFrame:
        """
        Process a pandas DataFrame by making API calls for each value in the specified column.

        Args:
            df: Input DataFrame
            column_name: Column name containing values to query
            endpoint: API endpoint
            param_name: Name of the parameter to use in the API call
            batch_size: Size of each batch
            additional_params: Additional query parameters
            result_handler: Optional function to process API results into a DataFrame

        Returns:
            DataFrame with API results
        """
        if column_name not in df.columns:
            raise ValueError(f"Column '{column_name}' not found in DataFrame")

        # Extract unique values to query
        unique_values = df[column_name].unique().tolist()
        total_items = len(unique_values)
        self.logger.info(f"Processing {total_items} unique values")

        # Calculate optimal batch size based on rate limits and concurrency
        optimal_batch_size = min(batch_size, self.max_concurrent_requests * 2)

        # Process in batches
        all_results = []

        # Helper function to run async code safely
        def run_async_safely(coro):
            try:
                # Check if there's an existing event loop
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # If we're already in an event loop (like in Jupyter), create a new one
                    return asyncio.run_coroutine_threadsafe(coro, loop).result()
                else:
                    # If no loop is running, use the current one
                    return loop.run_until_complete(coro)
            except RuntimeError:
                # If no event loop exists yet, create a new one with asyncio.run()
                return asyncio.run(coro)

        for i in range(0, total_items, optimal_batch_size):
            batch = unique_values[i : i + optimal_batch_size]
            self.logger.info(
                f"Processing batch {i//optimal_batch_size + 1}/{(total_items-1)//optimal_batch_size + 1} ({len(batch)} items)"
            )

            # Run batch processing using asyncio
            results = run_async_safely(
                self._process_batch(batch, endpoint, param_name, additional_params)
            )
            all_results.extend(results)

        # Process results into a DataFrame
        if result_handler:
            results_df = result_handler(all_results)
        else:
            # Default processing: Extract useful data from response
            processed_data = []
            for item in all_results:
                if "error" in item:
                    processed_data.append(
                        {
                            "query_value": item["item_value"],
                            "status": "error",
                            "error": item["error"],
                        }
                    )
                else:
                    result_dict = {
                        "query_value": item["item_value"],
                        "status": "success",
                    }
                    # If response is a dict, flatten top-level keys
                    if isinstance(item["response"], dict):
                        for key, value in item["response"].items():
                            # Don't include nested objects/arrays as separate columns
                            if not isinstance(value, (dict, list)):
                                result_dict[key] = value
                    else:
                        result_dict["result"] = item["response"]
                    processed_data.append(result_dict)

            results_df = pd.DataFrame(processed_data)

        # Merge with original DataFrame
        merged_df = df.merge(
            results_df, left_on=column_name, right_on="query_value", how="left"
        )
        print(merged_df.head())
        return merged_df
