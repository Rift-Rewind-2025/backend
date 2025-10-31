# rds_service.py
from __future__ import annotations
import os
import time
import decimal
import contextlib
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple, Union

import boto3
from botocore.client import BaseClient
from botocore.exceptions import ClientError


Number = Union[int, float, decimal.Decimal]


class RdsDataService:
    """
    Thin, ergonomic wrapper around Aurora Serverless **RDS Data API**.

    Usage:
        rds = RdsDataService.from_env()  # reads DB_ARN, SECRET_ARN, DB_NAME, AWS_REGION
        rows = rds.query("SELECT now() AS ts")
        rds.exec("INSERT INTO app.table(col) VALUES(:v)", {"v": 123})
        with rds.transaction() as tx:
            rds.exec("UPDATE ... WHERE id=:id", {"id": 1}, tx)
            rds.exec("UPDATE ... WHERE id=:id", {"id": 2}, tx)
    """

    # ---- construction --------------------------------------------------------

    def __init__(
        self,
        resource_arn: str,
        secret_arn: str,
        database: str,
        region_name: Optional[str] = None,
        client: Optional[BaseClient] = None,
        default_retry: int = 2,
        default_backoff: float = 0.4,
    ) -> None:
        self.resource_arn = resource_arn
        self.secret_arn = secret_arn
        self.database = database
        self.region_name = region_name or os.getenv("AWS_REGION") or os.getenv("AWS_DEFAULT_REGION")
        self._client = client
        self.default_retry = default_retry
        self.default_backoff = default_backoff

    @classmethod
    def from_env(cls) -> "RdsDataService":
        return cls(
            resource_arn=os.environ["DB_ARN"],
            secret_arn=os.environ["SECRET_ARN"],
            database=os.environ["DB_NAME"],
            region_name=os.getenv("AWS_REGION") or os.getenv("AWS_DEFAULT_REGION"),
        )

    # ---- low-level -----------------------------------------------------------

    @property
    def client(self) -> BaseClient:
        if self._client is None:
            self._client = boto3.client("rds-data", region_name=self.region_name)
        return self._client

    # Data API value marshalling
    @staticmethod
    def _to_field(v: Any) -> Dict[str, Any]:
        if v is None:
            return {"isNull": True}
        if isinstance(v, bool):
            return {"booleanValue": v}
        if isinstance(v, int):
            return {"longValue": v}
        if isinstance(v, (float, decimal.Decimal)):
            return {"doubleValue": float(v)}
        if isinstance(v, (bytes, bytearray, memoryview)):
            return {"blobValue": bytes(v)}
        return {"stringValue": str(v)}

    @classmethod
    def _to_params(cls, params: Optional[Dict[str, Any]]) -> List[Dict[str, Any]]:
        if not params:
            return []
        return [{"name": k, "value": cls._to_field(v)} for k, v in params.items()]

    @staticmethod
    def _records_to_dicts(resp: Dict[str, Any]) -> List[Dict[str, Any]]:
        cols = [m["name"] for m in resp.get("columnMetadata", [])]
        rows = []
        for rec in resp.get("records", []):
            row: Dict[str, Any] = {}
            for name, cell in zip(cols, rec):
                if not cell:
                    row[name] = None
                    continue
                # pick the single value in the union
                if "isNull" in cell:
                    row[name] = None
                elif "stringValue" in cell:
                    row[name] = cell["stringValue"]
                elif "doubleValue" in cell:
                    row[name] = cell["doubleValue"]
                elif "longValue" in cell:
                    row[name] = cell["longValue"]
                elif "booleanValue" in cell:
                    row[name] = cell["booleanValue"]
                elif "blobValue" in cell:
                    row[name] = cell["blobValue"]
                else:
                    # fallback for other shapes
                    row[name] = next(iter(cell.values()))
            rows.append(row)
        return rows

    # ---- public API ----------------------------------------------------------

    def exec(
        self,
        sql: str,
        params: Optional[Dict[str, Any]] = None,
        transaction_id: Optional[str] = None,
        retries: Optional[int] = None,
        backoff: Optional[float] = None,
    ) -> Dict[str, Any]:
        """Run INSERT/UPDATE/DDL; returns raw response."""
        return self._call(
            "execute_statement",
            {
                "resourceArn": self.resource_arn,
                "secretArn": self.secret_arn,
                "database": self.database,
                "sql": sql,
                "parameters": self._to_params(params),
                **({"transactionId": transaction_id} if transaction_id else {}),
            },
            retries,
            backoff,
        )

    def query(
        self,
        sql: str,
        params: Optional[Dict[str, Any]] = None,
        transaction_id: Optional[str] = None,
        retries: Optional[int] = None,
        backoff: Optional[float] = None,
    ) -> List[Dict[str, Any]]:
        """Run SELECT; returns list of dict rows."""
        resp = self._call(
            "execute_statement",
            {
                "resourceArn": self.resource_arn,
                "secretArn": self.secret_arn,
                "database": self.database,
                "sql": sql,
                "parameters": self._to_params(params),
                "includeResultMetadata": True,
                **({"transactionId": transaction_id} if transaction_id else {}),
            },
            retries,
            backoff,
        )
        return self._records_to_dicts(resp)

    def query_one(
        self,
        sql: str,
        params: Optional[Dict[str, Any]] = None,
        transaction_id: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        rows = self.query(sql, params, transaction_id)
        return rows[0] if rows else None

    def batch_exec(
        self,
        sql: str,
        parameter_sets: Sequence[Dict[str, Any]],
        retries: Optional[int] = None,
        backoff: Optional[float] = None,
    ) -> Dict[str, Any]:
        """Batch execute with named params. Each dict in parameter_sets is one row of bindings."""
        sets = [self._to_params(p) for p in parameter_sets]
        return self._call(
            "batch_execute_statement",
            {
                "resourceArn": self.resource_arn,
                "secretArn": self.secret_arn,
                "database": self.database,
                "sql": sql,
                "parameterSets": sets,
            },
            retries,
            backoff,
        )

    # ---- transactions --------------------------------------------------------

    @contextlib.contextmanager
    def transaction(self) -> Iterable[str]:
        """Context manager returning transaction_id."""
        begin = self.client.begin_transaction(
            resourceArn=self.resource_arn,
            secretArn=self.secret_arn,
            database=self.database,
        )
        tx = begin["transactionId"]
        try:
            yield tx
            self.client.commit_transaction(
                resourceArn=self.resource_arn, secretArn=self.secret_arn, transactionId=tx
            )
        except Exception:
            self.client.rollback_transaction(
                resourceArn=self.resource_arn, secretArn=self.secret_arn, transactionId=tx
            )
            raise

    # ---- internal retry wrapper ---------------------------------------------

    def _call(
        self,
        method: str,
        kwargs: Dict[str, Any],
        retries: Optional[int],
        backoff: Optional[float],
    ) -> Dict[str, Any]:
        attempts = (self.default_retry if retries is None else retries) + 1
        delay = self.default_backoff if backoff is None else backoff
        last_exc: Optional[Exception] = None

        for i in range(attempts):
            try:
                return getattr(self.client, method)(**kwargs)
            except ClientError as e:
                code = e.response.get("Error", {}).get("Code", "")
                # retry transient-ish errors
                if code in {"ThrottlingException", "BadRequestException", "ServiceUnavailableError"} and i < attempts - 1:
                    time.sleep(delay * (2 ** i))
                    last_exc = e
                    continue
                raise
            except Exception as e:
                if i < attempts - 1:
                    time.sleep(delay * (2 ** i))
                    last_exc = e
                    continue
                raise
        # Shouldn't reach here
        assert last_exc  # for type checkers
        raise last_exc
