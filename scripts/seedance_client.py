#!/usr/bin/env python3
"""
Seedance API Client

Core client class for interacting with the Volcengine/BytePlus Seedance API.
Provides video generation task creation, query, list, and cancellation functionality.
"""

import os
import time
import json
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from enum import Enum

try:
    import requests
    from dotenv import load_dotenv
except ImportError as e:
    raise ImportError(
        f"Missing required dependency: {e.name}. "
        "Install with: pip install requests python-dotenv"
    )


class TaskStatus(Enum):
    """Task status enumeration"""
    QUEUED = "queued"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
    EXPIRED = "expired"
    CANCELLED = "cancelled"


class SeedanceError(Exception):
    """Base Seedance API exception"""
    pass


class AuthenticationError(SeedanceError):
    """Authentication error"""
    pass


class MissingAPIKeyError(AuthenticationError):
    """Missing API Key error"""
    pass


class APIError(SeedanceError):
    """API request error"""
    def __init__(self, message: str, status_code: Optional[int] = None, response: Optional[Dict] = None):
        super().__init__(message)
        self.status_code = status_code
        self.response = response


class InvalidRequestError(APIError):
    """Invalid request error"""
    pass


class RateLimitError(APIError):
    """Rate limit error"""
    pass


class TaskNotFoundError(SeedanceError):
    """Task not found error"""
    pass


class NetworkError(SeedanceError):
    """Network error"""
    pass


class TimeoutError(SeedanceError):
    """Timeout error"""
    pass


@dataclass
class TaskInfo:
    """Task information"""
    id: str
    status: TaskStatus
    model: str
    created_at: str
    video_url: Optional[str] = None
    last_frame_url: Optional[str] = None
    resolution: Optional[str] = None
    ratio: Optional[str] = None
    duration: Optional[int] = None
    error_message: Optional[str] = None
    usage: Optional[Dict[str, Any]] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TaskInfo":
        """Create TaskInfo from dictionary"""
        try:
            status = TaskStatus(data.get("status", "queued"))
        except ValueError:
            status = TaskStatus.QUEUED

        content = data.get("content", {})
        usage = data.get("usage", {})

        return cls(
            id=data.get("id", ""),
            status=status,
            model=data.get("model", ""),
            created_at=data.get("created_at", ""),
            video_url=content.get("video_url"),
            last_frame_url=content.get("last_frame_url"),
            resolution=data.get("resolution"),
            ratio=data.get("ratio"),
            duration=data.get("duration"),
            error_message=data.get("error_message"),
            usage=usage
        )


class SeedanceClient:
    """Seedance API client"""

    DEFAULT_BASE_URL = "https://ark.ap-southeast.bytepluses.com/api/v3"
    DEFAULT_TIMEOUT = 60
    MAX_RETRIES = 3
    RETRY_DELAYS = [1, 2, 4]  # seconds

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout: int = DEFAULT_TIMEOUT
    ):
        """
        Initialize client

        Args:
            api_key: API Key, if None will read from environment variable or .env file
            base_url: API base URL, defaults to official URL
            timeout: Request timeout in seconds
        """
        self.api_key = api_key or self._get_api_key()
        self.base_url = (base_url or self.DEFAULT_BASE_URL).rstrip("/")
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        })

    def _get_api_key(self) -> str:
        """
        Get API Key

        Priority:
        1. ARK_API_KEY environment variable
        2. ARK_API_KEY in current directory .env file
        3. Interactive prompt
        """
        # Try environment variable
        api_key = os.environ.get("ARK_API_KEY")
        if api_key:
            return api_key

        # Try .env file
        load_dotenv()
        api_key = os.environ.get("ARK_API_KEY")
        if api_key:
            return api_key

        raise MissingAPIKeyError(
            "API Key not found. Set ARK_API_KEY environment variable, "
            "add it to .env file, or pass --api-key parameter."
        )

    def _make_request(
        self,
        method: str,
        endpoint: str,
        data: Optional[Dict] = None,
        params: Optional[Dict] = None,
        retry_count: int = 0
    ) -> Dict[str, Any]:
        """
        Send HTTP request (with retry)

        Args:
            method: HTTP method
            endpoint: API endpoint
            data: Request body data
            params: URL query parameters
            retry_count: Current retry count

        Returns:
            Response JSON data

        Raises:
            SeedanceError: Request failed
        """
        url = f"{self.base_url}{endpoint}"

        try:
            response = self.session.request(
                method=method,
                url=url,
                json=data,
                params=params,
                timeout=self.timeout
            )

            # Handle response
            return self._handle_response(response)

        except requests.exceptions.Timeout:
            if retry_count < self.MAX_RETRIES:
                delay = self.RETRY_DELAYS[min(retry_count, len(self.RETRY_DELAYS) - 1)]
                time.sleep(delay)
                return self._make_request(method, endpoint, data, params, retry_count + 1)
            raise TimeoutError(f"Request timeout after {self.timeout}s")

        except requests.exceptions.ConnectionError as e:
            raise NetworkError(f"Connection error: {e}")

        except requests.exceptions.RequestException as e:
            raise NetworkError(f"Request error: {e}")

    def _handle_response(self, response: requests.Response) -> Dict[str, Any]:
        """
        Handle API response

        Args:
            response: requests Response object

        Returns:
            Response JSON data

        Raises:
            APIError: API returned error
        """
        try:
            data = response.json()
        except json.JSONDecodeError:
            data = {}

        # Success response
        if response.status_code == 200:
            return data

        # Authentication error
        if response.status_code == 401:
            raise AuthenticationError("Invalid API Key or authentication failed")

        # Task not found
        if response.status_code == 404:
            raise TaskNotFoundError("Task not found")

        # Rate limit error
        if response.status_code == 429:
            raise RateLimitError("Rate limit exceeded. Please wait and retry.")

        # Other 4xx errors
        if 400 <= response.status_code < 500:
            error_msg = data.get("error", {}).get("message", "Invalid request")
            raise InvalidRequestError(
                error_msg,
                status_code=response.status_code,
                response=data
            )

        # 5xx errors - can retry
        if response.status_code >= 500:
            raise APIError(
                f"Server error: {response.status_code}",
                status_code=response.status_code,
                response=data
            )

        raise APIError(
            f"Unexpected status code: {response.status_code}",
            status_code=response.status_code,
            response=data
        )

    def create_task(self, payload: Dict[str, Any]) -> TaskInfo:
        """
        Create video generation task

        Args:
            payload: Task creation parameters

        Returns:
            TaskInfo object

        Raises:
            APIError: Creation failed
        """
        endpoint = "/contents/generations/tasks"

        # Models that do NOT support service_tier parameter
        models_without_service_tier = [
            "seedance-2-0-260128",
            "seedance-2-0",
        ]

        model = payload.get("model", "")
        if any(model.startswith(m) for m in models_without_service_tier):
            payload = {k: v for k, v in payload.items() if k != "service_tier"}

        data = self._make_request("POST", endpoint, data=payload)

        # Return task status, as create endpoint may return task_id or full task info
        if "id" in data:
            return TaskInfo.from_dict(data)
        elif "task_id" in data:
            # Case where task_id is returned, need to query for full info
            task_id = data["task_id"]
            return self.get_task(task_id)
        else:
            raise APIError("Unexpected response format: missing task id")

    def get_task(self, task_id: str) -> TaskInfo:
        """
        Query single task status

        Args:
            task_id: Task ID

        Returns:
            TaskInfo object

        Raises:
            TaskNotFoundError: Task does not exist
        """
        endpoint = f"/contents/generations/tasks/{task_id}"
        data = self._make_request("GET", endpoint)
        return TaskInfo.from_dict(data)

    def list_tasks(
        self,
        page_num: int = 1,
        page_size: int = 10,
        status: Optional[str] = None,
        model: Optional[str] = None,
        task_ids: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        List tasks (with filtering and pagination)

        Args:
            page_num: Page number (starting from 1)
            page_size: Items per page (max 500)
            status: Filter by status
            model: Filter by model
            task_ids: Specific task ID list

        Returns:
            Response data containing tasks list and pagination info
        """
        endpoint = "/contents/generations/tasks"

        params = {
            "page_num": page_num,
            "page_size": min(page_size, 500)
        }

        # Add filter parameters
        filters = {}
        if status:
            filters["status"] = status
        if model:
            filters["model"] = model
        if task_ids:
            filters["task_ids"] = ",".join(task_ids)

        if filters:
            params["filter"] = json.dumps(filters)

        return self._make_request("GET", endpoint, params=params)

    def cancel_task(self, task_id: str) -> Dict[str, Any]:
        """
        Cancel or delete task

        Cancels queued task, or deletes completed/failed task record

        Args:
            task_id: Task ID

        Returns:
            Response data
        """
        endpoint = f"/contents/generations/tasks/{task_id}"
        return self._make_request("DELETE", endpoint)

    def wait_for_completion(
        self,
        task_id: str,
        poll_interval: int = 5,
        timeout: int = 600,
        callback: Optional[callable] = None
    ) -> TaskInfo:
        """
        Wait for task completion

        Args:
            task_id: Task ID
            poll_interval: Poll interval in seconds
            timeout: Timeout in seconds
            callback: Callback function, parameter is TaskInfo

        Returns:
            Completed TaskInfo object

        Raises:
            TimeoutError: Timeout
        """
        start_time = time.time()

        while True:
            task = self.get_task(task_id)

            # Call callback
            if callback:
                callback(task)

            # Check if completed
            if task.status in (TaskStatus.SUCCEEDED, TaskStatus.FAILED,
                               TaskStatus.EXPIRED, TaskStatus.CANCELLED):
                return task

            # Check timeout
            elapsed = time.time() - start_time
            if elapsed >= timeout:
                raise TimeoutError(f"Task did not complete within {timeout}s")

            # Wait
            time.sleep(poll_interval)
