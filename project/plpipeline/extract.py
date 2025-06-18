import polars as pl
import pandas as pd
import aiohttp
import asyncio
import time
from tqdm.auto import tqdm
import logging
from typing import List, Dict, Any, Callable, Optional, Union, Tuple

from dataclasses import dataclass
from datetime import date

import calendar


@dataclass
class APIResponse:
    """Data class to standardize API responses"""

    success: bool
    data: Any
    error: Optional[str] = None
    query_params: Optional[Dict[str, Any]] = None
    status_code: Optional[int] = None


class ExtractCVE:
    def __init__(
        self,
        base_url: str,
        max_concurrent_requests: int = 10,
        rate_limit_per_minute: int = 60,
        timeout: int = 30,
        retries: int = 30,
    ):
        self.BASE_URL = base_url
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

    # extract date-time strings for each month within date range
    def _get_Params(self, start_year, end_year):
        months = []
        for year in range(start_year, end_year + 1):
            for month in range(1, 13):
                for i in range(0, 6000, 2000):
                    _, last_date = calendar.monthrange(year, month)
                    start_date = date(year, month, 1)
                    end_date = date(year, month, last_date)
                    dict = {
                        "pubStartDate": f"{year}-{start_date.strftime("%m")}-01T00:00:00.000",
                        "pubEndDate": f"{year}-{end_date.strftime("%m")}-{last_date}T23:59:59.999",
                        "startIndex": i,
                    }
                    months.append(dict)
        return months

    async def _make_request(
        self, session, url: str, params: Dict[str, Any], headers: Dict[str, Any]
    ) -> APIResponse:
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

    async def _fetch_data(
        self,
        session: aiohttp.ClientSession,
        endpoint: str,
        batch_params: List[Dict],
        API_KEY: Optional[str] = None,
    ) -> List[APIResponse]:

        url = f"{self.BASE_URL}/{endpoint}"
        headers = {"apiKey": API_KEY} if API_KEY else {}
        tasks = []
        for params in batch_params:
            task = self._make_request(session, url, params, headers)
            tasks.append(task)
        return await asyncio.gather(*tasks)

    async def _process_batch(
        self,
        batch_params,
        endpoint,
        API_KEY,
    ):
        connector = aiohttp.TCPConnector(limit=self.max_concurrent_requests)
        timeout = aiohttp.ClientTimeout(total=self.timeout)

        try:
            async with aiohttp.ClientSession(
                connector=connector, timeout=timeout
            ) as session:
                return await self._fetch_data(session, endpoint, batch_params, API_KEY)
        except Exception as e:
            self.logger.error(f"Batch Processing Error: {e}")

    def extract(
        self,
        dates: List[int],
        endpoint: str,
        batch_size: int = 10,
        API_KEY: Optional[str] = None,
    ):
        params = self._get_Params(dates[0], dates[1])
        total_items = len(params)
        results = []
        for i in range(0, total_items, batch_size):
            batch_params = params[i : i + batch_size]
            self.logger.info(
                f"Processing batch {i // batch_size+1} / {(total_items -1)// batch_size+1}: {len(batch_params)} items"
            )

            try:
                batch_results = asyncio.run(
                    self._process_batch(
                        batch_params,
                        endpoint,
                        API_KEY,
                    )
                )
                results.extend(batch_results)
            except Exception as e:
                self.logger.error(f"Batch Processing Error: {e}")
            if i + batch_size < total_items:
                time.sleep(1)
        return self._result_handler(results)

    def _result_handler(self, results):
        processed_data = []
        param_names = ["pubStartDate", "pubEndDate", "startIndex"]
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

        return pl.DataFrame(processed_data)


"""
Make_request
    Make an Individual request
Fetch Data
    Make a batch of API requests 
Process DF:
    Input DF
    column names
    endpoint
    param names
    batch size: 
    additional params: (Query)
    api key: Optional
    result handler: Optional Function

Result handler:
    ARGS:
        Results: list of API Responses
        Param Names: used in API Calll
    Returns:
        DF w processed results
"""
