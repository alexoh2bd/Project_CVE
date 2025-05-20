import pandas as pd
import aiohttp
import asyncio
import time
from tqdm.auto import tqdm
import logging
from typing import List, Dict, Any, Callable, Optional, Union, Tuple
import backoff
import concurrent.futures
from dataclasses import dataclass


@dataclass
class APIResponse:
    """Data class to standardize API responses"""

    success: bool
    data: Any
    error: Optional[str] = None
    query_params: Optional[Dict[str, Any]] = None
    status_code: Optional[int] = None


class PublicAPIBatchProcessor:
    """
    Process large batches of public API calls efficiently with rate limiting and backoff handling.
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
        self.timeout = aiohttp.ClientTimeout(total=timeout)
        self.retries = retries
        self.request_interval = 60 / rate_limit_per_minute
        self.last_request_time = 0

        # Configure logging
        logging.basicConfig(
            level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
        )
        self.logger = logging.getLogger(__name__)

    @backoff.on_exception(
        backoff.expo,
        (aiohttp.ClientError, asyncio.TimeoutError),
        max_tries=3,
        jitter=backoff.full_jitter,
    )
    async def _make_request(
        self,
        session: aiohttp.ClientSession,
        url: str,
        params: Dict[str, Any],
        headers: Dict[str, Any],
    ) -> APIResponse:
        """
        Make an API request with backoff handling.

        Args:
            session: aiohttp client session
            url: Complete API URL
            params: Query parameters
            headers: Request headers

        Returns:
            Standardized API response
        """
        try:
            # Apply rate limiting
            current_time = time.time()
            time_since_last_request = current_time - self.last_request_time
            if time_since_last_request < self.request_interval:
                await asyncio.sleep(self.request_interval - time_since_last_request)

            self.last_request_time = time.time()

            async with session.get(url, params=params, headers=headers) as response:
                status = response.status

                if status >= 200 and status < 300:
                    data = await response.json()
                    return APIResponse(
                        success=True, data=data, query_params=params, status_code=status
                    )
                else:
                    error_text = await response.text()
                    return APIResponse(
                        success=False,
                        data=None,
                        error=f"HTTP Error {status}: {error_text}",
                        query_params=params,
                        status_code=status,
                    )

        except asyncio.TimeoutError:
            return APIResponse(
                success=False, data=None, error="Request timed out", query_params=params
            )
        except aiohttp.ClientError as e:
            return APIResponse(
                success=False,
                data=None,
                error=f"Client error: {str(e)}",
                query_params=params,
            )
        except Exception as e:
            return APIResponse(
                success=False,
                data=None,
                error=f"Unexpected error: {str(e)}",
                query_params=params,
            )

    async def fetch_data(
        self,
        session: aiohttp.ClientSession,
        endpoint: str,
        param_values: List[Tuple[Any, ...]],
        param_names: List[str],
        additional_params: Optional[Dict[str, Any]] = None,
        api_key: Optional[str] = None,
    ) -> List[APIResponse]:
        """
        Make API requests for a batch of parameter values.

        Args:
            session: aiohttp client session
            endpoint: API endpoint
            param_values: List of parameter value tuples
            param_names: Names of the parameters to use in the API call
            additional_params: Additional query parameters
            api_key: Optional API key

        Returns:
            List of API responses
        """
        url = f"{self.base_url}/{endpoint}"
        headers = {"apiKey": api_key} if api_key else {}
        tasks = []

        for values in param_values:
            # Create parameter dictionary
            params = {param_names[i]: values[i] for i in range(len(values))}

            # Add additional parameters
            if additional_params:
                params.update(additional_params)

            # Create task for this parameter set
            task = self._make_request(session, url, params, headers)
            tasks.append(task)

        # Execute all tasks concurrently
        return await asyncio.gather(*tasks)

    async def _process_batch(
        self,
        param_values: List[Tuple[Any, ...]],
        endpoint: str,
        param_names: List[str],
        additional_params: Optional[Dict[str, Any]] = None,
        api_key: Optional[str] = None,
    ) -> List[APIResponse]:
        """
        Process a batch of parameter values concurrently.

        Args:
            param_values: List of parameter value tuples
            endpoint: API endpoint
            param_names: Names of the parameters to use in the API call
            additional_params: Additional query parameters
            api_key: Optional API key

        Returns:
            List of API responses
        """
        # Configure connection pool
        connector = aiohttp.TCPConnector(limit=self.max_concurrent_requests)
        timeout = aiohttp.ClientTimeout(total=self.timeout.total)

        async with aiohttp.ClientSession(
            connector=connector, timeout=timeout
        ) as session:
            # Fetch data for all parameter values in this batch
            return await self.fetch_data(
                session, endpoint, param_values, param_names, additional_params, api_key
            )

    def process_dataframe(
        self,
        df: pd.DataFrame,
        column_names: List[str],
        endpoint: str,
        param_names: List[str],
        batch_size: int = 100,
        additional_params: Optional[Dict[str, Any]] = None,
        api_key: Optional[str] = None,
        result_handler: Optional[Callable[[List[APIResponse]], pd.DataFrame]] = None,
    ) -> pd.DataFrame:
        """
        Process a pandas DataFrame by making API calls for each row using specified columns.

        Args:
            df: Input DataFrame
            column_names: Column names containing values to query
            endpoint: API endpoint
            param_names: Names of the parameters to use in the API call
            batch_size: Size of each batch
            additional_params: Additional query parameters
            api_key: Optional API key
            result_handler: Optional function to process API results into a DataFrame

        Returns:
            DataFrame with API results
        """
        # Validate columns exist
        for name in column_names:
            if name not in df.columns:
                raise ValueError(f"Column '{name}' not found in DataFrame")

        # Extract values to query as tuples
        param_values = df[column_names].drop_duplicates().values.tolist()
        total_items = len(param_values)

        self.logger.info(f"Processing {total_items} unique parameter combinations")

        # Calculate optimal batch size based on rate limits and concurrency
        optimal_batch_size = min(batch_size, self.max_concurrent_requests * 2)

        # Process in batches
        all_results = []

        # Create batches and process them
        for i in range(0, total_items, optimal_batch_size):
            batch_values = param_values[i : i + optimal_batch_size]
            self.logger.info(
                f"Processing batch {i//optimal_batch_size + 1}/{(total_items-1)//optimal_batch_size + 1} "
                f"({len(batch_values)} items)"
            )

            # Run batch processing using asyncio
            batch_results = asyncio.run(
                self._process_batch(
                    batch_values, endpoint, param_names, additional_params, api_key
                )
            )

            all_results.extend(batch_results)

            # Add a small delay between batches to avoid API rate limits
            if i + optimal_batch_size < total_items:
                time.sleep(1)

        # Process results into a DataFrame
        if result_handler:
            return result_handler(all_results)
        else:
            # Default processing: convert responses to DataFrame
            return self._default_result_handler(all_results, param_names)

    def _default_result_handler(
        self, results: List[APIResponse], param_names: List[str]
    ) -> pd.DataFrame:
        """
        Default handler to convert API responses to a DataFrame.

        Args:
            results: List of API responses
            param_names: Names of the parameters used in the API call

        Returns:
            DataFrame with processed results
        """
        processed_data = []

        for response in results:
            result_dict = {}

            # Add query parameters
            if response.query_params:
                for name in param_names:
                    if name in response.query_params:
                        result_dict[f"query_{name}"] = response.query_params[name]

            # Add status information
            result_dict["success"] = response.success
            result_dict["status_code"] = response.status_code

            if response.success:
                # If response data is a dict, flatten top-level keys
                if isinstance(response.data, dict):
                    for key, value in response.data.items():
                        # Don't include nested objects/arrays as separate columns
                        if not isinstance(value, (dict, list)):
                            result_dict[key] = value
                        else:
                            # Store complex data as is
                            result_dict[key] = value
                else:
                    result_dict["data"] = response.data
            else:
                result_dict["error"] = response.error

            processed_data.append(result_dict)

        return pd.DataFrame(processed_data)
