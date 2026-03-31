#!/usr/bin/env python3
"""
OpenAPI/Swagger Specification to Skill Converter

Converts OpenAPI 2.0 (Swagger) and OpenAPI 3.0/3.1 specifications into AI-ready skills.
Supports both YAML and JSON spec formats, and can load specs from local files or remote URLs.

Extracts:
- API info (title, description, version, contact, license)
- Servers / host / basePath
- All paths with their operations (GET, POST, PUT, DELETE, PATCH, etc.)
- Parameters (path, query, header, cookie, body)
- Request bodies and response schemas
- Component schemas / definitions with properties, types, enums
- Security schemes (apiKey, http, oauth2, openIdConnect)
- Tags for endpoint grouping

Usage:
    skill-seekers openapi --spec petstore.yaml --name petstore-api
    skill-seekers openapi --spec-url https://petstore3.swagger.io/api/v3/openapi.json --name petstore
    skill-seekers openapi --from-json petstore_extracted.json
    python3 -m skill_seekers.cli.openapi_scraper --spec spec.yaml --name my-api
"""

import argparse
import copy
import json
import logging
import os
import re
import sys
from pathlib import Path
from typing import Any

# Optional dependency guard
try:
    import yaml

    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False

logger = logging.getLogger(__name__)

# HTTP methods recognized in OpenAPI path items
HTTP_METHODS = {"get", "post", "put", "delete", "patch", "head", "options", "trace"}

# OpenAPI version detection patterns
_OPENAPI_3_RE = re.compile(r"^3\.\d+\.\d+$")
_SWAGGER_2_RE = re.compile(r"^2\.\d+$")


def _check_yaml_deps():
    """Raise RuntimeError if pyyaml is not installed."""
    if not YAML_AVAILABLE:
        raise RuntimeError(
            "pyyaml is required for OpenAPI/Swagger YAML spec support.\n"
            'Install with: pip install "skill-seekers[openapi]"\n'
            "Or: pip install pyyaml"
        )


def infer_description_from_spec(info: dict | None = None, name: str = "") -> str:
    """Infer skill description from OpenAPI info object.

    Tries to build a meaningful "Use when..." description from the spec metadata.

    Args:
        info: OpenAPI info object with title, description, etc.
        name: Skill name for fallback

    Returns:
        Description string suitable for "Use when..." format
    """
    if info:
        # Try the spec description first
        desc = info.get("description", "")
        if desc and len(desc) > 20:
            # Take first sentence or first 150 chars
            first_sentence = desc.split(". ")[0]
            if len(first_sentence) > 150:
                first_sentence = first_sentence[:147] + "..."
            return f"Use when working with {first_sentence.lower()}"

        # Fall back to title
        title = info.get("title", "")
        if title and len(title) > 5:
            return f"Use when working with the {title} API"

    return f"Use when working with the {name} API" if name else "Use when working with this API"


class OpenAPIToSkillConverter:
    """Convert OpenAPI/Swagger specifications to AI-ready skills.

    Supports OpenAPI 2.0 (Swagger), 3.0, and 3.1 specifications in both
    YAML and JSON formats. Can load specs from local files or remote URLs.

    The converter extracts endpoints, schemas, security schemes, and metadata,
    then generates structured markdown reference files suitable for LLM consumption.

    Attributes:
        config: Configuration dictionary with name, spec_path, spec_url, description.
        name: Skill name used for output directory and filenames.
        spec_path: Local file path to the OpenAPI spec (mutually exclusive with spec_url).
        spec_url: Remote URL to fetch the OpenAPI spec from.
        description: Skill description for SKILL.md frontmatter.
        skill_dir: Output directory for the generated skill.
        data_file: Path to the extracted JSON data file.
        spec_data: Raw parsed spec dictionary.
        extracted_data: Structured extraction result with endpoints, schemas, etc.
    """

    def __init__(self, config: dict) -> None:
        """Initialize the converter with configuration.

        Args:
            config: Dictionary with keys:
                - name (str): Skill name (required)
                - spec_path (str): Local file path to spec (optional)
                - spec_url (str): Remote URL to fetch spec (optional)
                - description (str): Skill description (optional)

        Raises:
            ValueError: If neither spec_path nor spec_url is provided and
                        no from_json workflow is intended.
        """
        self.config = config
        self.name = config["name"]
        self.spec_path: str = config.get("spec_path", "")
        self.spec_url: str = config.get("spec_url", "")
        self.description: str = config.get(
            "description", f"Use when working with the {self.name} API"
        )

        # Output paths
        self.skill_dir = f"output/{self.name}"
        self.data_file = f"output/{self.name}_extracted.json"

        # Internal state
        self.spec_data: dict[str, Any] = {}
        self.extracted_data: dict[str, Any] = {}
        self.openapi_version: str = ""

    # ──────────────────────────────────────────────────────────────────────
    # Spec loading
    # ──────────────────────────────────────────────────────────────────────

    def extract_spec(self) -> bool:
        """Read and parse the OpenAPI specification from file or URL.

        Determines the source (local file or remote URL), loads the raw content,
        parses it as YAML or JSON, detects the OpenAPI version, and delegates
        to the appropriate version-specific parser.

        Returns:
            True if extraction succeeded, False otherwise.

        Raises:
            RuntimeError: If the spec cannot be loaded or parsed.
            ValueError: If the spec version is unsupported.
        """
        _check_yaml_deps()
        logger.info("\n  Extracting OpenAPI specification...")

        # Load raw spec data
        if self.spec_path:
            self.spec_data = self._load_from_file(self.spec_path)
        elif self.spec_url:
            self.spec_data = self._load_from_url(self.spec_url)
        else:
            raise RuntimeError(
                "No spec source provided. Use spec_path (local file) or spec_url (remote URL)."
            )

        # Detect version
        self.openapi_version = self._detect_version(self.spec_data)
        logger.info("  Detected OpenAPI version: %s", self.openapi_version)

        # Parse according to version
        if _SWAGGER_2_RE.match(self.openapi_version):
            self.extracted_data = self._parse_swagger_2(self.spec_data)
        elif _OPENAPI_3_RE.match(self.openapi_version):
            self.extracted_data = self._parse_openapi_3(self.spec_data)
        else:
            raise ValueError(
                f"Unsupported OpenAPI version: {self.openapi_version}. "
                "Supported versions: 2.0 (Swagger), 3.0.x, 3.1.x"
            )

        # Update description from spec info if not explicitly set in config
        if "description" not in self.config:
            info = self.extracted_data.get("info", {})
            self.description = infer_description_from_spec(info, self.name)

        # Persist extracted data
        os.makedirs("output", exist_ok=True)
        with open(self.data_file, "w", encoding="utf-8") as f:
            json.dump(self.extracted_data, f, indent=2, ensure_ascii=False)
        logger.info("  Saved extracted data to: %s", self.data_file)

        # Log summary
        endpoints = self.extracted_data.get("endpoints", [])
        schemas = self.extracted_data.get("schemas", {})
        security = self.extracted_data.get("security_schemes", {})
        logger.info(
            "  Extracted %d endpoints, %d schemas, %d security schemes",
            len(endpoints),
            len(schemas),
            len(security),
        )

        return True

    def _load_from_file(self, path: str) -> dict[str, Any]:
        """Load and parse a spec from a local file.

        Supports both YAML (.yaml, .yml) and JSON (.json) files.

        Args:
            path: Path to the local spec file.

        Returns:
            Parsed spec as a dictionary.

        Raises:
            RuntimeError: If the file cannot be read or parsed.
        """
        logger.info("  Loading spec from file: %s", path)

        if not os.path.exists(path):
            raise RuntimeError(f"Spec file not found: {path}")

        try:
            with open(path, encoding="utf-8") as f:
                content = f.read()
        except OSError as e:
            raise RuntimeError(f"Failed to read spec file {path}: {e}") from e

        return self._parse_content(content, path)

    def _load_from_url(self, url: str) -> dict[str, Any]:
        """Fetch and parse a spec from a remote URL.

        Args:
            url: URL to fetch the spec from.

        Returns:
            Parsed spec as a dictionary.

        Raises:
            RuntimeError: If the URL cannot be fetched or the content parsed.
        """
        logger.info("  Fetching spec from URL: %s", url)

        try:
            import requests
        except ImportError as exc:
            raise RuntimeError(
                "requests library is required for fetching remote specs.\n"
                "Install with: pip install requests"
            ) from exc

        try:
            response = requests.get(
                url,
                timeout=30,
                headers={
                    "User-Agent": "SkillSeekers/OpenAPI-Scraper",
                    "Accept": "application/json, application/yaml, text/yaml, */*",
                },
            )
            response.raise_for_status()
        except Exception as e:
            raise RuntimeError(f"Failed to fetch spec from {url}: {e}") from e

        return self._parse_content(response.text, url)

    def _parse_content(self, content: str, source: str) -> dict[str, Any]:
        """Parse raw content as YAML or JSON.

        Tries JSON first (faster), falls back to YAML. YAML is a superset
        of JSON, so YAML parsing handles both formats.

        Args:
            content: Raw text content.
            source: Source path or URL (for error messages and format detection).

        Returns:
            Parsed dictionary.

        Raises:
            RuntimeError: If content cannot be parsed.
        """
        # Try JSON first if source looks like JSON
        if source.endswith(".json") or content.lstrip().startswith("{"):
            try:
                return json.loads(content)
            except json.JSONDecodeError:
                pass  # Fall through to YAML

        # Try YAML (handles both YAML and JSON)
        try:
            data = yaml.safe_load(content)
            if isinstance(data, dict):
                return data
            raise RuntimeError(
                f"Spec from {source} parsed but is not a mapping (got {type(data).__name__})"
            )
        except yaml.YAMLError as e:
            raise RuntimeError(f"Failed to parse spec from {source}: {e}") from e

    def _detect_version(self, spec: dict[str, Any]) -> str:
        """Detect the OpenAPI/Swagger version from the spec.

        Args:
            spec: Parsed spec dictionary.

        Returns:
            Version string (e.g. "2.0", "3.0.3", "3.1.0").

        Raises:
            ValueError: If no version field is found.
        """
        # OpenAPI 3.x uses "openapi" field
        if "openapi" in spec:
            return str(spec["openapi"])

        # Swagger 2.0 uses "swagger" field
        if "swagger" in spec:
            return str(spec["swagger"])

        raise ValueError(
            "Cannot determine spec version. Expected 'openapi' or 'swagger' field "
            "at the root of the specification."
        )

    # ──────────────────────────────────────────────────────────────────────
    # Data loading (from previously extracted JSON)
    # ──────────────────────────────────────────────────────────────────────

    def load_extracted_data(self, json_path: str | None = None) -> bool:
        """Load previously extracted data from a JSON file.

        Args:
            json_path: Path to the JSON file. Defaults to self.data_file.

        Returns:
            True if loading succeeded.

        Raises:
            FileNotFoundError: If the JSON file does not exist.
        """
        path = json_path or self.data_file
        logger.info("  Loading extracted data from: %s", path)

        if not os.path.exists(path):
            raise FileNotFoundError(f"Extracted data file not found: {path}")

        with open(path, encoding="utf-8") as f:
            self.extracted_data = json.load(f)

        endpoints = self.extracted_data.get("endpoints", [])
        schemas = self.extracted_data.get("schemas", {})
        logger.info("  Loaded %d endpoints, %d schemas", len(endpoints), len(schemas))
        return True

    # ──────────────────────────────────────────────────────────────────────
    # Version-specific parsers
    # ──────────────────────────────────────────────────────────────────────

    def _parse_openapi_3(self, spec: dict[str, Any]) -> dict[str, Any]:
        """Parse an OpenAPI 3.0/3.1 specification.

        Extracts info, servers, endpoints, component schemas, and security schemes
        following the OpenAPI 3.x structure.

        Args:
            spec: Parsed OpenAPI 3.x spec dictionary.

        Returns:
            Structured extraction dictionary.
        """
        logger.info("  Parsing OpenAPI 3.x specification...")

        result: dict[str, Any] = {
            "openapi_version": str(spec.get("openapi", "3.0.0")),
            "info": self._extract_info(spec),
            "servers": [],
            "endpoints": [],
            "schemas": {},
            "security_schemes": {},
            "tags": [],
            "external_docs": spec.get("externalDocs", {}),
        }

        # Extract servers
        for server in spec.get("servers", []):
            result["servers"].append(
                {
                    "url": server.get("url", ""),
                    "description": server.get("description", ""),
                    "variables": server.get("variables", {}),
                }
            )

        # Extract tags
        for tag in spec.get("tags", []):
            result["tags"].append(
                {
                    "name": tag.get("name", ""),
                    "description": tag.get("description", ""),
                    "external_docs": tag.get("externalDocs", {}),
                }
            )

        # Extract endpoints from paths
        result["endpoints"] = self._extract_endpoints(spec, version=3)

        # Extract component schemas
        components = spec.get("components", {})
        result["schemas"] = self._extract_schemas(components.get("schemas", {}), spec)

        # Extract security schemes
        result["security_schemes"] = self._extract_security(
            components.get("securitySchemes", {}), version=3
        )

        # Global security requirements
        result["global_security"] = spec.get("security", [])

        return result

    def _parse_swagger_2(self, spec: dict[str, Any]) -> dict[str, Any]:
        """Parse a Swagger 2.0 specification.

        Extracts info, host/basePath, endpoints, definitions, and security
        following the Swagger 2.0 structure.

        Args:
            spec: Parsed Swagger 2.0 spec dictionary.

        Returns:
            Structured extraction dictionary.
        """
        logger.info("  Parsing Swagger 2.0 specification...")

        result: dict[str, Any] = {
            "openapi_version": str(spec.get("swagger", "2.0")),
            "info": self._extract_info(spec),
            "servers": [],
            "endpoints": [],
            "schemas": {},
            "security_schemes": {},
            "tags": [],
            "external_docs": spec.get("externalDocs", {}),
        }

        # Convert host/basePath/schemes to pseudo-servers for consistency
        host = spec.get("host", "")
        base_path = spec.get("basePath", "/")
        schemes = spec.get("schemes", ["https"])
        if host:
            for scheme in schemes:
                result["servers"].append(
                    {
                        "url": f"{scheme}://{host}{base_path}",
                        "description": f"Swagger 2.0 server ({scheme})",
                        "variables": {},
                    }
                )

        # Extract tags
        for tag in spec.get("tags", []):
            result["tags"].append(
                {
                    "name": tag.get("name", ""),
                    "description": tag.get("description", ""),
                    "external_docs": tag.get("externalDocs", {}),
                }
            )

        # Extract endpoints from paths
        result["endpoints"] = self._extract_endpoints(spec, version=2)

        # Extract definitions (Swagger 2.0 equivalent of component schemas)
        result["schemas"] = self._extract_schemas(spec.get("definitions", {}), spec)

        # Extract security definitions
        result["security_schemes"] = self._extract_security(
            spec.get("securityDefinitions", {}), version=2
        )

        # Global security requirements
        result["global_security"] = spec.get("security", [])

        # Swagger 2.0 global consumes/produces
        result["consumes"] = spec.get("consumes", [])
        result["produces"] = spec.get("produces", [])

        return result

    # ──────────────────────────────────────────────────────────────────────
    # Shared extraction helpers
    # ──────────────────────────────────────────────────────────────────────

    def _extract_info(self, spec: dict[str, Any]) -> dict[str, Any]:
        """Extract the info object from a spec.

        Args:
            spec: The full spec dictionary.

        Returns:
            Normalized info dictionary.
        """
        info = spec.get("info", {})
        contact = info.get("contact", {})
        license_info = info.get("license", {})

        return {
            "title": info.get("title", "Untitled API"),
            "description": info.get("description", ""),
            "version": info.get("version", ""),
            "terms_of_service": info.get("termsOfService", ""),
            "contact": {
                "name": contact.get("name", ""),
                "url": contact.get("url", ""),
                "email": contact.get("email", ""),
            },
            "license": {
                "name": license_info.get("name", ""),
                "url": license_info.get("url", ""),
            },
        }

    def _extract_endpoints(self, spec: dict[str, Any], version: int) -> list[dict[str, Any]]:
        """Extract all API endpoints from the spec paths.

        Iterates over every path and HTTP method, extracting operation metadata,
        parameters, request body, responses, tags, and security requirements.

        Args:
            spec: The full spec dictionary.
            version: OpenAPI major version (2 or 3).

        Returns:
            List of endpoint dictionaries.
        """
        endpoints: list[dict[str, Any]] = []
        paths = spec.get("paths", {})

        for path, path_item in paths.items():
            if not isinstance(path_item, dict):
                continue

            # Path-level parameters apply to all operations
            path_level_params = path_item.get("parameters", [])

            for method in HTTP_METHODS:
                operation = path_item.get(method)
                if not operation or not isinstance(operation, dict):
                    continue

                endpoint: dict[str, Any] = {
                    "path": path,
                    "method": method.upper(),
                    "operation_id": operation.get("operationId", ""),
                    "summary": operation.get("summary", ""),
                    "description": operation.get("description", ""),
                    "tags": operation.get("tags", []),
                    "deprecated": operation.get("deprecated", False),
                    "security": operation.get("security", []),
                    "parameters": [],
                    "request_body": {},
                    "responses": {},
                }

                # Merge path-level and operation-level parameters
                all_params = list(path_level_params) + operation.get("parameters", [])
                for param in all_params:
                    resolved = self._resolve_ref(param, spec)
                    endpoint["parameters"].append(
                        self._normalize_parameter(resolved, version, spec)
                    )

                # Request body (OpenAPI 3.x) or body parameter (Swagger 2.0)
                if version >= 3:
                    req_body = operation.get("requestBody", {})
                    if req_body:
                        resolved_body = self._resolve_ref(req_body, spec)
                        endpoint["request_body"] = self._normalize_request_body_v3(
                            resolved_body, spec
                        )
                else:
                    # Swagger 2.0: body parameter is extracted alongside other params
                    body_params = [p for p in endpoint["parameters"] if p.get("location") == "body"]
                    if body_params:
                        endpoint["request_body"] = {
                            "description": body_params[0].get("description", ""),
                            "required": body_params[0].get("required", False),
                            "content": {
                                "application/json": {"schema": body_params[0].get("schema", {})}
                            },
                        }

                # Responses
                for status_code, response_obj in operation.get("responses", {}).items():
                    resolved_resp = self._resolve_ref(response_obj, spec)
                    endpoint["responses"][str(status_code)] = self._normalize_response(
                        resolved_resp, version, spec
                    )

                endpoints.append(endpoint)

        return endpoints

    def _normalize_parameter(
        self, param: dict[str, Any], version: int, spec: dict[str, Any]
    ) -> dict[str, Any]:
        """Normalize a parameter object across OpenAPI versions.

        Args:
            param: Raw parameter object (already resolved).
            version: OpenAPI major version (2 or 3).
            spec: Full spec for nested $ref resolution.

        Returns:
            Normalized parameter dictionary.
        """
        location = param.get("in", "query")
        schema = param.get("schema", {})

        # Swagger 2.0 has type/format directly on the parameter
        if version == 2 and not schema and location != "body":
            schema = {
                "type": param.get("type", "string"),
                "format": param.get("format", ""),
                "enum": param.get("enum", []),
                "default": param.get("default"),
                "items": param.get("items", {}),
            }
            # Remove empty values
            schema = {k: v for k, v in schema.items() if v is not None and v != "" and v != []}

        # Swagger 2.0 body parameter
        if version == 2 and location == "body":
            body_schema = param.get("schema", {})
            body_schema = self._resolve_ref(body_schema, spec)
            schema = self._flatten_schema(body_schema, spec)

        # OpenAPI 3.x parameter schema
        if version >= 3 and schema:
            schema = self._resolve_ref(schema, spec)
            schema = self._flatten_schema(schema, spec)

        return {
            "name": param.get("name", ""),
            "location": location,
            "description": param.get("description", ""),
            "required": param.get("required", location == "path"),
            "deprecated": param.get("deprecated", False),
            "schema": schema,
            "example": param.get("example", param.get("x-example")),
        }

    def _normalize_request_body_v3(
        self, body: dict[str, Any], spec: dict[str, Any]
    ) -> dict[str, Any]:
        """Normalize an OpenAPI 3.x request body object.

        Args:
            body: Raw requestBody object (already resolved).
            spec: Full spec for nested $ref resolution.

        Returns:
            Normalized request body dictionary.
        """
        content_map: dict[str, Any] = {}
        for media_type, media_obj in body.get("content", {}).items():
            schema = media_obj.get("schema", {})
            schema = self._resolve_ref(schema, spec)
            schema = self._flatten_schema(schema, spec)
            content_map[media_type] = {
                "schema": schema,
                "example": media_obj.get("example"),
                "examples": media_obj.get("examples", {}),
            }

        return {
            "description": body.get("description", ""),
            "required": body.get("required", False),
            "content": content_map,
        }

    def _normalize_response(
        self,
        response: dict[str, Any],
        version: int,
        spec: dict[str, Any],
    ) -> dict[str, Any]:
        """Normalize a response object across OpenAPI versions.

        Args:
            response: Raw response object (already resolved).
            version: OpenAPI major version (2 or 3).
            spec: Full spec for nested $ref resolution.

        Returns:
            Normalized response dictionary.
        """
        result: dict[str, Any] = {
            "description": response.get("description", ""),
            "content": {},
            "headers": {},
        }

        if version >= 3:
            # OpenAPI 3.x: content with media types
            for media_type, media_obj in response.get("content", {}).items():
                schema = media_obj.get("schema", {})
                schema = self._resolve_ref(schema, spec)
                schema = self._flatten_schema(schema, spec)
                result["content"][media_type] = {"schema": schema}
        else:
            # Swagger 2.0: schema directly on the response
            schema = response.get("schema", {})
            if schema:
                schema = self._resolve_ref(schema, spec)
                schema = self._flatten_schema(schema, spec)
                result["content"]["application/json"] = {"schema": schema}

        # Headers
        for header_name, header_obj in response.get("headers", {}).items():
            resolved_header = self._resolve_ref(header_obj, spec)
            result["headers"][header_name] = {
                "description": resolved_header.get("description", ""),
                "schema": resolved_header.get(
                    "schema",
                    {
                        "type": resolved_header.get("type", "string"),
                    },
                ),
            }

        return result

    def _extract_schemas(
        self, schemas_dict: dict[str, Any], spec: dict[str, Any]
    ) -> dict[str, Any]:
        """Extract and normalize component schemas or definitions.

        Args:
            schemas_dict: The schemas/definitions mapping from the spec.
            spec: Full spec for $ref resolution.

        Returns:
            Dictionary of schema name to flattened schema object.
        """
        result: dict[str, Any] = {}

        for schema_name, schema_obj in schemas_dict.items():
            resolved = self._resolve_ref(schema_obj, spec)
            flattened = self._flatten_schema(resolved, spec, depth=0)
            result[schema_name] = flattened

        logger.info("  Extracted %d schemas", len(result))
        return result

    def _flatten_schema(
        self,
        schema: dict[str, Any],
        spec: dict[str, Any],
        depth: int = 0,
    ) -> dict[str, Any]:
        """Flatten a schema by resolving references and simplifying structure.

        Handles $ref, allOf, oneOf, anyOf composition. Limits recursion depth
        to prevent infinite loops in circular references.

        Args:
            schema: Schema object to flatten.
            spec: Full spec for $ref resolution.
            depth: Current recursion depth (max 10).

        Returns:
            Flattened schema dictionary.
        """
        if not schema or not isinstance(schema, dict) or depth > 10:
            return schema if isinstance(schema, dict) else {}

        # Resolve top-level $ref
        if "$ref" in schema:
            ref_name = schema["$ref"].split("/")[-1]
            resolved = self._resolve_ref(schema, spec)
            if resolved is schema:
                # Could not resolve — return stub
                return {"type": "object", "$ref": schema["$ref"], "_ref_name": ref_name}
            result = self._flatten_schema(resolved, spec, depth + 1)
            result["_ref_name"] = ref_name
            return result

        result = dict(schema)

        # Handle allOf composition
        if "allOf" in result:
            merged: dict[str, Any] = {}
            merged_properties: dict[str, Any] = {}
            merged_required: list[str] = []
            for sub_schema in result["allOf"]:
                flat = self._flatten_schema(sub_schema, spec, depth + 1)
                merged_properties.update(flat.get("properties", {}))
                merged_required.extend(flat.get("required", []))
                # Merge other fields (description, type, etc.)
                for k, v in flat.items():
                    if k not in ("properties", "required"):
                        merged[k] = v
            merged["properties"] = merged_properties
            if merged_required:
                merged["required"] = list(dict.fromkeys(merged_required))
            if "type" not in merged and merged_properties:
                merged["type"] = "object"
            del result["allOf"]
            result.update(merged)

        # Handle oneOf / anyOf — keep as list of flattened schemas
        for combinator in ("oneOf", "anyOf"):
            if combinator in result:
                result[combinator] = [
                    self._flatten_schema(s, spec, depth + 1) for s in result[combinator]
                ]

        # Flatten nested properties
        if "properties" in result:
            flat_props: dict[str, Any] = {}
            for prop_name, prop_schema in result["properties"].items():
                flat_props[prop_name] = self._flatten_schema(prop_schema, spec, depth + 1)
            result["properties"] = flat_props

        # Flatten items (for array types)
        if "items" in result and isinstance(result["items"], dict):
            result["items"] = self._flatten_schema(result["items"], spec, depth + 1)

        # Flatten additionalProperties
        if "additionalProperties" in result and isinstance(result["additionalProperties"], dict):
            result["additionalProperties"] = self._flatten_schema(
                result["additionalProperties"], spec, depth + 1
            )

        return result

    def _extract_security(self, security_dict: dict[str, Any], version: int) -> dict[str, Any]:
        """Extract and normalize security scheme definitions.

        Args:
            security_dict: securitySchemes (v3) or securityDefinitions (v2) mapping.
            version: OpenAPI major version (2 or 3).

        Returns:
            Dictionary of scheme name to normalized security scheme.
        """
        result: dict[str, Any] = {}

        for scheme_name, scheme_obj in security_dict.items():
            scheme_type = scheme_obj.get("type", "")

            normalized: dict[str, Any] = {
                "type": scheme_type,
                "description": scheme_obj.get("description", ""),
            }

            if scheme_type == "apiKey":
                normalized["name"] = scheme_obj.get("name", "")
                normalized["location"] = scheme_obj.get("in", "header")

            elif scheme_type in ("http", "basic"):
                normalized["scheme"] = scheme_obj.get("scheme", "basic")
                normalized["bearer_format"] = scheme_obj.get("bearerFormat", "")

            elif scheme_type == "oauth2":
                if version >= 3:
                    normalized["flows"] = scheme_obj.get("flows", {})
                else:
                    # Swagger 2.0 OAuth2
                    normalized["flow"] = scheme_obj.get("flow", "")
                    normalized["authorization_url"] = scheme_obj.get("authorizationUrl", "")
                    normalized["token_url"] = scheme_obj.get("tokenUrl", "")
                    normalized["scopes"] = scheme_obj.get("scopes", {})

            elif scheme_type == "openIdConnect":
                normalized["openid_connect_url"] = scheme_obj.get("openIdConnectUrl", "")

            result[scheme_name] = normalized

        return result

    def _resolve_ref(self, obj: dict[str, Any], spec: dict[str, Any]) -> dict[str, Any]:
        """Resolve a $ref reference within the specification.

        Follows JSON Pointer syntax (e.g. "#/components/schemas/Pet") to find
        the referenced object. Returns the original object unchanged if it
        contains no $ref.

        Args:
            obj: Object that may contain a "$ref" key.
            spec: The full spec to resolve against.

        Returns:
            The resolved object, or the original if no $ref is present.
        """
        if not isinstance(obj, dict) or "$ref" not in obj:
            return obj

        ref_path = obj["$ref"]
        if not ref_path.startswith("#/"):
            # External references are not supported — return as-is
            logger.debug("  External $ref not supported: %s", ref_path)
            return obj

        parts = ref_path[2:].split("/")
        current: Any = spec
        for part in parts:
            # Handle JSON Pointer escaping
            part = part.replace("~1", "/").replace("~0", "~")
            if isinstance(current, dict):
                current = current.get(part)
            else:
                logger.warning("  Could not resolve $ref: %s", ref_path)
                return obj

            if current is None:
                logger.warning("  $ref target not found: %s", ref_path)
                return obj

        if isinstance(current, dict):
            # Return a copy to avoid mutation
            return copy.copy(current)
        return obj

    # ──────────────────────────────────────────────────────────────────────
    # Categorization
    # ──────────────────────────────────────────────────────────────────────

    def categorize_content(self) -> dict[str, list[dict[str, Any]]]:
        """Categorize endpoints by tags and path groups.

        Groups endpoints primarily by their tags. Endpoints without tags are
        grouped by the first significant path segment. A special "untagged"
        group is used for endpoints that cannot be categorized.

        Returns:
            Dictionary mapping category name to list of endpoint dicts.
        """
        logger.info("  Categorizing endpoints...")

        endpoints = self.extracted_data.get("endpoints", [])
        categories: dict[str, list[dict[str, Any]]] = {}

        for endpoint in endpoints:
            tags = endpoint.get("tags", [])

            if tags:
                # Use the first tag as primary category
                tag = tags[0]
                if tag not in categories:
                    categories[tag] = []
                categories[tag].append(endpoint)
            else:
                # Group by first path segment
                path = endpoint.get("path", "/")
                segments = [s for s in path.split("/") if s and not s.startswith("{")]
                group = segments[0] if segments else "root"
                if group not in categories:
                    categories[group] = []
                categories[group].append(endpoint)

        # Log summary
        for cat_name, cat_endpoints in categories.items():
            logger.info("    %s: %d endpoints", cat_name, len(cat_endpoints))

        return categories

    # ──────────────────────────────────────────────────────────────────────
    # Skill building
    # ──────────────────────────────────────────────────────────────────────

    def build_skill(self) -> None:
        """Build the complete skill structure from extracted data.

        Creates output directories, generates reference files for each endpoint
        category, an index file, and the main SKILL.md.
        """
        logger.info("\n  Building skill: %s", self.name)

        # Create directories
        os.makedirs(f"{self.skill_dir}/references", exist_ok=True)
        os.makedirs(f"{self.skill_dir}/scripts", exist_ok=True)
        os.makedirs(f"{self.skill_dir}/assets", exist_ok=True)

        # Categorize endpoints
        categories = self.categorize_content()

        # Generate reference files
        logger.info("  Generating reference files...")
        for cat_name, cat_endpoints in categories.items():
            self._generate_reference_file(cat_name, cat_endpoints)

        # Generate schemas reference
        schemas = self.extracted_data.get("schemas", {})
        if schemas:
            self._generate_schemas_reference(schemas)

        # Generate security reference
        security = self.extracted_data.get("security_schemes", {})
        if security:
            self._generate_security_reference(security)

        # Generate index
        self._generate_index(categories)

        # Generate SKILL.md
        self._generate_skill_md(categories)

        logger.info("\n  Skill built successfully: %s/", self.skill_dir)
        logger.info("  Next step: Package with: skill-seekers package %s/", self.skill_dir)

    def _generate_reference_file(self, cat_name: str, endpoints: list[dict[str, Any]]) -> None:
        """Generate a reference markdown file for a category of endpoints.

        Args:
            cat_name: Category name (tag or path group).
            endpoints: List of endpoint dicts belonging to this category.
        """
        safe_name = self._sanitize_filename(cat_name)
        filepath = f"{self.skill_dir}/references/{safe_name}.md"

        lines: list[str] = []
        lines.append(f"# {cat_name} Endpoints\n")

        # Tag description from spec tags
        tag_desc = self._get_tag_description(cat_name)
        if tag_desc:
            lines.append(f"{tag_desc}\n")

        lines.append(f"**Endpoints:** {len(endpoints)}\n")
        lines.append("---\n")

        for endpoint in endpoints:
            lines.append(self._format_endpoint_md(endpoint))
            lines.append("\n---\n")

        with open(filepath, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))

        logger.info("    Generated: %s", filepath)

    def _generate_schemas_reference(self, schemas: dict[str, Any]) -> None:
        """Generate a reference markdown file for all component schemas.

        Args:
            schemas: Dictionary mapping schema name to schema object.
        """
        filepath = f"{self.skill_dir}/references/schemas.md"

        lines: list[str] = []
        lines.append("# Data Models / Schemas\n")
        lines.append("Component schemas (data models) defined in the API specification.\n")
        lines.append(f"**Total schemas:** {len(schemas)}\n")
        lines.append("---\n")

        for schema_name in sorted(schemas.keys()):
            schema = schemas[schema_name]
            lines.append(self._format_schema_md(schema_name, schema))
            lines.append("\n---\n")

        with open(filepath, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))

        logger.info("    Generated: %s", filepath)

    def _generate_security_reference(self, security_schemes: dict[str, Any]) -> None:
        """Generate a reference markdown file for security schemes.

        Args:
            security_schemes: Dictionary mapping scheme name to scheme object.
        """
        filepath = f"{self.skill_dir}/references/security.md"

        lines: list[str] = []
        lines.append("# Security Schemes\n")
        lines.append("Authentication and authorization schemes defined in the API specification.\n")
        lines.append(f"**Total schemes:** {len(security_schemes)}\n")
        lines.append("---\n")

        for scheme_name, scheme in security_schemes.items():
            lines.append(f"## {scheme_name}\n")
            lines.append(f"**Type:** `{scheme.get('type', 'unknown')}`\n")

            if scheme.get("description"):
                lines.append(f"{scheme['description']}\n")

            scheme_type = scheme.get("type", "")

            if scheme_type == "apiKey":
                lines.append(f"- **Parameter name:** `{scheme.get('name', '')}`")
                lines.append(f"- **Location:** `{scheme.get('location', 'header')}`\n")

            elif scheme_type in ("http", "basic"):
                lines.append(f"- **Scheme:** `{scheme.get('scheme', 'basic')}`")
                if scheme.get("bearer_format"):
                    lines.append(f"- **Bearer format:** `{scheme['bearer_format']}`")
                lines.append("")

            elif scheme_type == "oauth2":
                if "flows" in scheme:
                    # OpenAPI 3.x flows
                    for flow_name, flow_obj in scheme["flows"].items():
                        lines.append(f"### Flow: {flow_name}\n")
                        if flow_obj.get("authorizationUrl"):
                            lines.append(
                                f"- **Authorization URL:** `{flow_obj['authorizationUrl']}`"
                            )
                        if flow_obj.get("tokenUrl"):
                            lines.append(f"- **Token URL:** `{flow_obj['tokenUrl']}`")
                        if flow_obj.get("refreshUrl"):
                            lines.append(f"- **Refresh URL:** `{flow_obj['refreshUrl']}`")
                        scopes = flow_obj.get("scopes", {})
                        if scopes:
                            lines.append("\n**Scopes:**\n")
                            for scope_name, scope_desc in scopes.items():
                                lines.append(f"- `{scope_name}`: {scope_desc}")
                        lines.append("")
                else:
                    # Swagger 2.0 OAuth2
                    if scheme.get("authorization_url"):
                        lines.append(f"- **Authorization URL:** `{scheme['authorization_url']}`")
                    if scheme.get("token_url"):
                        lines.append(f"- **Token URL:** `{scheme['token_url']}`")
                    if scheme.get("flow"):
                        lines.append(f"- **Flow:** `{scheme['flow']}`")
                    scopes = scheme.get("scopes", {})
                    if scopes:
                        lines.append("\n**Scopes:**\n")
                        for scope_name, scope_desc in scopes.items():
                            lines.append(f"- `{scope_name}`: {scope_desc}")
                    lines.append("")

            elif scheme_type == "openIdConnect":
                lines.append(
                    f"- **OpenID Connect URL:** `{scheme.get('openid_connect_url', '')}`\n"
                )

            lines.append("")

        with open(filepath, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))

        logger.info("    Generated: %s", filepath)

    def _generate_index(self, categories: dict[str, list[dict[str, Any]]]) -> None:
        """Generate the reference index file.

        Args:
            categories: Categorized endpoints mapping.
        """
        filepath = f"{self.skill_dir}/references/index.md"

        lines: list[str] = []
        lines.append(f"# {self.name.title()} API Reference Index\n")

        info = self.extracted_data.get("info", {})
        if info.get("version"):
            lines.append(f"**API Version:** {info['version']}\n")

        lines.append("## Endpoint Categories\n")
        total_endpoints = 0
        for cat_name, cat_endpoints in sorted(categories.items()):
            safe_name = self._sanitize_filename(cat_name)
            count = len(cat_endpoints)
            total_endpoints += count
            lines.append(f"- [{cat_name}]({safe_name}.md) ({count} endpoints)")

        lines.append(f"\n**Total endpoints:** {total_endpoints}\n")

        # Schemas and security links
        schemas = self.extracted_data.get("schemas", {})
        security = self.extracted_data.get("security_schemes", {})

        lines.append("## Additional References\n")
        if schemas:
            lines.append(f"- [Data Models / Schemas](schemas.md) ({len(schemas)} schemas)")
        if security:
            lines.append(f"- [Security Schemes](security.md) ({len(security)} schemes)")

        # Servers
        servers = self.extracted_data.get("servers", [])
        if servers:
            lines.append("\n## Servers\n")
            for server in servers:
                desc = server.get("description", "")
                url = server.get("url", "")
                if desc:
                    lines.append(f"- `{url}` - {desc}")
                else:
                    lines.append(f"- `{url}`")

        lines.append("")

        with open(filepath, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))

        logger.info("    Generated: %s", filepath)

    def _generate_skill_md(self, categories: dict[str, list[dict[str, Any]]]) -> None:
        """Generate the main SKILL.md file.

        Creates a comprehensive skill manifest with API overview, endpoint summary,
        authentication info, quick reference, and navigation links.

        Args:
            categories: Categorized endpoints mapping.
        """
        filepath = f"{self.skill_dir}/SKILL.md"

        info = self.extracted_data.get("info", {})
        api_title = info.get("title", self.name.title())
        api_version = info.get("version", "")
        api_description = info.get("description", "")

        # Skill name for frontmatter (lowercase, hyphens, max 64 chars)
        skill_name = self.name.lower().replace("_", "-").replace(" ", "-")[:64]

        # Truncate description
        desc = self.description[:1024] if len(self.description) > 1024 else self.description

        lines: list[str] = []

        # YAML frontmatter
        lines.append("---")
        lines.append(f"name: {skill_name}")
        lines.append(f"description: {desc}")
        lines.append("---\n")

        # Header
        lines.append(f"# {api_title}\n")
        lines.append(f"{self.description}\n")

        if api_version:
            lines.append(f"**API Version:** {api_version}\n")

        if api_description:
            # Truncate long descriptions for SKILL.md summary
            summary_desc = api_description
            if len(summary_desc) > 500:
                summary_desc = summary_desc[:497] + "..."
            lines.append(f"{summary_desc}\n")

        # When to use
        lines.append("## When to Use This Skill\n")
        lines.append("Use this skill when you need to:\n")
        lines.append(f"- Understand the {api_title} endpoints and operations")
        lines.append(f"- Look up request/response schemas for {api_title}")
        lines.append("- Find authentication and authorization requirements")
        lines.append("- Construct API requests with correct parameters")
        lines.append("- Review available data models and their properties")
        lines.append("- Check endpoint paths, methods, and status codes\n")

        # Servers
        servers = self.extracted_data.get("servers", [])
        if servers:
            lines.append("## Servers\n")
            for server in servers:
                url = server.get("url", "")
                server_desc = server.get("description", "")
                if server_desc:
                    lines.append(f"- `{url}` - {server_desc}")
                else:
                    lines.append(f"- `{url}`")
            lines.append("")

        # Authentication summary
        security_schemes = self.extracted_data.get("security_schemes", {})
        if security_schemes:
            lines.append("## Authentication\n")
            for scheme_name, scheme in security_schemes.items():
                scheme_type = scheme.get("type", "")
                if scheme_type == "apiKey":
                    location = scheme.get("location", "header")
                    param_name = scheme.get("name", "")
                    lines.append(
                        f"- **{scheme_name}**: API Key in `{location}` (parameter: `{param_name}`)"
                    )
                elif scheme_type in ("http", "basic"):
                    auth_scheme = scheme.get("scheme", "basic")
                    lines.append(f"- **{scheme_name}**: HTTP `{auth_scheme}`")
                elif scheme_type == "oauth2":
                    lines.append(f"- **{scheme_name}**: OAuth 2.0")
                elif scheme_type == "openIdConnect":
                    lines.append(f"- **{scheme_name}**: OpenID Connect")
                else:
                    lines.append(f"- **{scheme_name}**: `{scheme_type}`")
            lines.append("")

        # Endpoint overview by category
        lines.append("## API Endpoints Overview\n")
        total_endpoints = sum(len(eps) for eps in categories.values())
        lines.append(f"**Total endpoints:** {total_endpoints}\n")

        for cat_name in sorted(categories.keys()):
            cat_endpoints = categories[cat_name]
            tag_desc = self._get_tag_description(cat_name)
            header = f"### {cat_name}"
            if tag_desc:
                header += f" - {tag_desc}"
            lines.append(header + "\n")

            for ep in cat_endpoints:
                method = ep.get("method", "GET")
                path = ep.get("path", "/")
                summary = ep.get("summary", "")
                deprecated = " *(deprecated)*" if ep.get("deprecated") else ""
                line = f"- `{method} {path}`"
                if summary:
                    line += f" - {summary}"
                line += deprecated
                lines.append(line)
            lines.append("")

        # Data models summary
        schemas = self.extracted_data.get("schemas", {})
        if schemas:
            lines.append("## Data Models\n")
            lines.append(f"**Total schemas:** {len(schemas)}\n")
            for schema_name in sorted(schemas.keys()):
                schema = schemas[schema_name]
                schema_desc = schema.get("description", "")
                schema_type = schema.get("type", "object")
                line = f"- **{schema_name}** (`{schema_type}`)"
                if schema_desc:
                    short_desc = schema_desc
                    if len(short_desc) > 80:
                        short_desc = short_desc[:77] + "..."
                    line += f" - {short_desc}"
                lines.append(line)
            lines.append("")

        # Quick reference: most common endpoints
        lines.append("## Quick Reference\n")
        lines.append("### Common Operations\n")
        # Show first 15 endpoints grouped by method
        all_endpoints = self.extracted_data.get("endpoints", [])
        by_method: dict[str, list[dict[str, Any]]] = {}
        for ep in all_endpoints:
            method = ep.get("method", "GET")
            if method not in by_method:
                by_method[method] = []
            by_method[method].append(ep)

        method_order = ["GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"]
        for method in method_order:
            eps = by_method.get(method, [])
            if not eps:
                continue
            lines.append(f"**{method}:**\n")
            for ep in eps[:5]:
                path = ep.get("path", "/")
                summary = ep.get("summary", "")
                if summary:
                    lines.append(f"- `{path}` - {summary}")
                else:
                    lines.append(f"- `{path}`")
            if len(eps) > 5:
                lines.append(f"- *...and {len(eps) - 5} more*")
            lines.append("")

        # Reference file navigation
        lines.append("## Reference Files\n")
        lines.append("Detailed API documentation is organized in `references/`:\n")
        lines.append("- `references/index.md` - Complete reference index")
        for cat_name in sorted(categories.keys()):
            safe_name = self._sanitize_filename(cat_name)
            count = len(categories[cat_name])
            lines.append(f"- `references/{safe_name}.md` - {cat_name} ({count} endpoints)")
        if schemas:
            lines.append(f"- `references/schemas.md` - Data models ({len(schemas)} schemas)")
        if security_schemes:
            lines.append(
                f"- `references/security.md` - Security schemes ({len(security_schemes)} schemes)"
            )
        lines.append("")

        # Contact info
        contact = info.get("contact", {})
        license_info = info.get("license", {})
        if contact.get("url") or contact.get("email") or license_info.get("name"):
            lines.append("## API Info\n")
            if contact.get("name"):
                lines.append(f"- **Contact:** {contact['name']}")
            if contact.get("email"):
                lines.append(f"- **Email:** {contact['email']}")
            if contact.get("url"):
                lines.append(f"- **URL:** {contact['url']}")
            if license_info.get("name"):
                license_line = f"- **License:** {license_info['name']}"
                if license_info.get("url"):
                    license_line += f" ([link]({license_info['url']}))"
                lines.append(license_line)
            if info.get("terms_of_service"):
                lines.append(f"- **Terms of Service:** {info['terms_of_service']}")
            lines.append("")

        # Footer
        lines.append("---\n")
        lines.append("**Generated by Skill Seekers** | OpenAPI/Swagger Specification Scraper\n")

        with open(filepath, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))

        line_count = len(lines)
        logger.info("    Generated: %s (%d lines)", filepath, line_count)

    # ──────────────────────────────────────────────────────────────────────
    # Markdown formatting helpers
    # ──────────────────────────────────────────────────────────────────────

    def _format_endpoint_md(self, endpoint: dict[str, Any]) -> str:
        """Format a single endpoint as a markdown section.

        Generates a comprehensive markdown block including method, path, summary,
        description, parameters table, request body schema, and response schemas.

        Args:
            endpoint: Normalized endpoint dictionary.

        Returns:
            Markdown string for the endpoint.
        """
        lines: list[str] = []

        method = endpoint.get("method", "GET")
        path = endpoint.get("path", "/")
        summary = endpoint.get("summary", "")
        description = endpoint.get("description", "")
        operation_id = endpoint.get("operation_id", "")
        deprecated = endpoint.get("deprecated", False)

        # Header
        header = f"## `{method} {path}`"
        if deprecated:
            header += " *(DEPRECATED)*"
        lines.append(header + "\n")

        if summary:
            lines.append(f"**{summary}**\n")

        if description:
            lines.append(f"{description}\n")

        if operation_id:
            lines.append(f"**Operation ID:** `{operation_id}`\n")

        # Tags
        tags = endpoint.get("tags", [])
        if tags:
            lines.append(f"**Tags:** {', '.join(f'`{t}`' for t in tags)}\n")

        # Security requirements
        security = endpoint.get("security", [])
        if security:
            scheme_names = []
            for req in security:
                scheme_names.extend(req.keys())
            if scheme_names:
                lines.append(f"**Security:** {', '.join(f'`{s}`' for s in scheme_names)}\n")

        # Parameters
        params = endpoint.get("parameters", [])
        # Exclude body params (handled in request body section)
        non_body_params = [p for p in params if p.get("location") != "body"]

        if non_body_params:
            lines.append("### Parameters\n")
            lines.append("| Name | Location | Type | Required | Description |")
            lines.append("|------|----------|------|----------|-------------|")

            for param in non_body_params:
                name = param.get("name", "")
                location = param.get("location", "query")
                schema = param.get("schema", {})
                param_type = self._schema_type_string(schema)
                required = "Yes" if param.get("required") else "No"
                desc = param.get("description", "").replace("\n", " ")
                if len(desc) > 100:
                    desc = desc[:97] + "..."

                deprecated_mark = " *(deprecated)*" if param.get("deprecated") else ""
                lines.append(
                    f"| `{name}`{deprecated_mark} | {location} "
                    f"| `{param_type}` | {required} | {desc} |"
                )
            lines.append("")

        # Request body
        request_body = endpoint.get("request_body", {})
        if request_body and request_body.get("content"):
            lines.append("### Request Body\n")
            if request_body.get("description"):
                lines.append(f"{request_body['description']}\n")
            required = "Required" if request_body.get("required") else "Optional"
            lines.append(f"**{required}**\n")

            for media_type, media_obj in request_body["content"].items():
                lines.append(f"**Content-Type:** `{media_type}`\n")
                schema = media_obj.get("schema", {})
                if schema:
                    lines.append(self._render_schema_block(schema, indent=0))
                    lines.append("")

        # Responses
        responses = endpoint.get("responses", {})
        if responses:
            lines.append("### Responses\n")

            for status_code in sorted(responses.keys()):
                resp = responses[status_code]
                resp_desc = resp.get("description", "")
                lines.append(f"**`{status_code}`** - {resp_desc}\n")

                for media_type, media_obj in resp.get("content", {}).items():
                    lines.append(f"Content-Type: `{media_type}`\n")
                    schema = media_obj.get("schema", {})
                    if schema:
                        lines.append(self._render_schema_block(schema, indent=0))
                        lines.append("")

                # Response headers
                headers = resp.get("headers", {})
                if headers:
                    lines.append("**Headers:**\n")
                    for hdr_name, hdr_obj in headers.items():
                        hdr_desc = hdr_obj.get("description", "")
                        hdr_schema = hdr_obj.get("schema", {})
                        hdr_type = self._schema_type_string(hdr_schema)
                        lines.append(f"- `{hdr_name}` (`{hdr_type}`): {hdr_desc}")
                    lines.append("")

        return "\n".join(lines)

    def _format_schema_md(self, schema_name: str, schema: dict[str, Any]) -> str:
        """Format a component schema as a markdown section.

        Renders the schema name, type, description, properties table, enum values,
        and composition (allOf/oneOf/anyOf).

        Args:
            schema_name: Name of the schema.
            schema: Flattened schema dictionary.

        Returns:
            Markdown string for the schema.
        """
        lines: list[str] = []

        schema_type = schema.get("type", "object")
        lines.append(f"## {schema_name}\n")
        lines.append(f"**Type:** `{schema_type}`\n")

        if schema.get("description"):
            lines.append(f"{schema['description']}\n")

        # Enum values
        enum_values = schema.get("enum", [])
        if enum_values:
            lines.append("**Enum values:**\n")
            for val in enum_values:
                lines.append(f"- `{val}`")
            lines.append("")

        # Properties (for object types)
        properties = schema.get("properties", {})
        required_fields = schema.get("required", [])

        if properties:
            lines.append("### Properties\n")
            lines.append("| Property | Type | Required | Description |")
            lines.append("|----------|------|----------|-------------|")

            for prop_name in sorted(properties.keys()):
                prop = properties[prop_name]
                prop_type = self._schema_type_string(prop)
                is_required = "Yes" if prop_name in required_fields else "No"
                prop_desc = prop.get("description", "").replace("\n", " ")
                if len(prop_desc) > 100:
                    prop_desc = prop_desc[:97] + "..."

                # Add enum info inline
                prop_enum = prop.get("enum", [])
                if prop_enum:
                    enum_str = ", ".join(f"`{v}`" for v in prop_enum[:5])
                    if len(prop_enum) > 5:
                        enum_str += f", +{len(prop_enum) - 5} more"
                    prop_desc += f" Enum: [{enum_str}]"

                lines.append(f"| `{prop_name}` | `{prop_type}` | {is_required} | {prop_desc} |")
            lines.append("")

        # Array items
        if schema_type == "array" and "items" in schema:
            items = schema["items"]
            items_type = self._schema_type_string(items)
            lines.append(f"**Items type:** `{items_type}`\n")
            if items.get("properties"):
                lines.append(self._render_schema_block(items, indent=0))
                lines.append("")

        # Composition types
        for combinator in ("oneOf", "anyOf"):
            variants = schema.get(combinator, [])
            if variants:
                lines.append(f"### {combinator}\n")
                for i, variant in enumerate(variants, 1):
                    variant_type = self._schema_type_string(variant)
                    ref_name = variant.get("_ref_name", "")
                    if ref_name:
                        lines.append(f"{i}. `{ref_name}` ({variant_type})")
                    else:
                        lines.append(f"{i}. `{variant_type}`")
                lines.append("")

        # Additional properties
        addl = schema.get("additionalProperties")
        if isinstance(addl, dict) and addl:
            addl_type = self._schema_type_string(addl)
            lines.append(f"**Additional properties:** `{addl_type}`\n")

        return "\n".join(lines)

    def _render_schema_block(self, schema: dict[str, Any], indent: int = 0) -> str:
        """Render a schema as an indented property listing.

        Used for inline schema rendering in endpoint request/response sections.

        Args:
            schema: Schema dictionary.
            indent: Indentation level.

        Returns:
            Formatted schema string.
        """
        lines: list[str] = []
        prefix = "  " * indent

        schema_type = schema.get("type", "object")
        ref_name = schema.get("_ref_name", "")

        if ref_name:
            lines.append(f"{prefix}Schema: `{ref_name}` ({schema_type})")
        else:
            lines.append(f"{prefix}Schema: `{schema_type}`")

        # Show properties for objects
        properties = schema.get("properties", {})
        required_fields = schema.get("required", [])

        if properties:
            for prop_name in sorted(properties.keys()):
                prop = properties[prop_name]
                prop_type = self._schema_type_string(prop)
                req_marker = " *(required)*" if prop_name in required_fields else ""
                prop_desc = prop.get("description", "")
                if prop_desc:
                    if len(prop_desc) > 60:
                        prop_desc = prop_desc[:57] + "..."
                    lines.append(
                        f"{prefix}- `{prop_name}`: `{prop_type}`{req_marker} - {prop_desc}"
                    )
                else:
                    lines.append(f"{prefix}- `{prop_name}`: `{prop_type}`{req_marker}")

        # Show enum values
        enum_values = schema.get("enum", [])
        if enum_values:
            enum_str = ", ".join(f"`{v}`" for v in enum_values[:8])
            if len(enum_values) > 8:
                enum_str += f", +{len(enum_values) - 8} more"
            lines.append(f"{prefix}Enum: [{enum_str}]")

        # Show array items type
        if schema_type == "array" and "items" in schema:
            items_type = self._schema_type_string(schema["items"])
            lines.append(f"{prefix}Items: `{items_type}`")

        return "\n".join(lines)

    def _schema_type_string(self, schema: dict[str, Any]) -> str:
        """Generate a human-readable type string for a schema.

        Handles primitive types, arrays, objects, refs, enums, and formats.

        Args:
            schema: Schema dictionary.

        Returns:
            Type string like "string", "integer(int64)", "array[Pet]", etc.
        """
        if not schema or not isinstance(schema, dict):
            return "any"

        ref_name = schema.get("_ref_name", "")
        schema_type = schema.get("type", "")
        schema_format = schema.get("format", "")

        # Referenced type
        if ref_name and not schema_type:
            return ref_name

        # Array type
        if schema_type == "array":
            items = schema.get("items", {})
            items_type = self._schema_type_string(items)
            return f"array[{items_type}]"

        # Object with ref name
        if ref_name:
            return ref_name

        # Primitive with format
        if schema_format:
            return f"{schema_type}({schema_format})"

        # Enum
        if schema.get("enum") and not schema_type:
            return "enum"

        # Composition types
        for combinator in ("oneOf", "anyOf"):
            variants = schema.get(combinator, [])
            if variants:
                type_strs = [self._schema_type_string(v) for v in variants[:3]]
                result = " | ".join(type_strs)
                if len(variants) > 3:
                    result += " | ..."
                return result

        return schema_type or "object"

    def _get_tag_description(self, tag_name: str) -> str:
        """Look up a tag description from the spec tags list.

        Args:
            tag_name: Tag name to search for.

        Returns:
            Tag description string, or empty string if not found.
        """
        for tag in self.extracted_data.get("tags", []):
            if tag.get("name") == tag_name:
                return tag.get("description", "")
        return ""

    def _sanitize_filename(self, name: str) -> str:
        """Convert a string to a safe filename.

        Removes special characters, replaces spaces and hyphens with underscores,
        and lowercases the result.

        Args:
            name: Input string.

        Returns:
            Sanitized filename string.
        """
        safe = re.sub(r"[^\w\s-]", "", name.lower())
        safe = re.sub(r"[-\s]+", "_", safe)
        return safe


# ──────────────────────────────────────────────────────────────────────────────
# CLI entry point
# ──────────────────────────────────────────────────────────────────────────────


def main() -> int:
    """CLI entry point for the OpenAPI scraper.

    Supports three input modes:
    1. Local spec file: --spec path/to/spec.yaml
    2. Remote spec URL: --spec-url https://example.com/openapi.json
    3. Pre-extracted JSON: --from-json extracted.json

    Standard arguments (--name, --description, --verbose, --quiet, --dry-run)
    are provided by the shared argument system.
    """
    _check_yaml_deps()

    parser = argparse.ArgumentParser(
        description="Convert OpenAPI/Swagger specifications to AI-ready skills",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --spec petstore.yaml --name petstore-api
  %(prog)s --spec-url https://petstore3.swagger.io/api/v3/openapi.json --name petstore
  %(prog)s --from-json petstore_extracted.json
        """,
    )

    # Standard shared arguments
    from .arguments.common import add_all_standard_arguments

    add_all_standard_arguments(parser)

    # Override enhance-level default to 0 for OpenAPI
    for action in parser._actions:
        if hasattr(action, "dest") and action.dest == "enhance_level":
            action.default = 0
            action.help = (
                "AI enhancement level (auto-detects API vs LOCAL mode): "
                "0=disabled (default for OpenAPI), 1=SKILL.md only, "
                "2=+architecture/config, 3=full enhancement. "
                "Mode selection: uses API if ANTHROPIC_API_KEY is set, "
                "otherwise LOCAL (Claude Code, Kimi, etc.)"
            )

    # OpenAPI-specific arguments
    parser.add_argument(
        "--spec",
        type=str,
        help="Local path to OpenAPI/Swagger spec file (YAML or JSON)",
        metavar="PATH",
    )
    parser.add_argument(
        "--spec-url",
        type=str,
        help="Remote URL to fetch OpenAPI/Swagger spec from",
        metavar="URL",
    )
    parser.add_argument(
        "--from-json",
        type=str,
        help="Build skill from previously extracted JSON data",
        metavar="FILE",
    )

    args = parser.parse_args()

    # Setup logging
    if getattr(args, "quiet", False):
        logging.basicConfig(level=logging.WARNING, format="%(message)s")
    elif getattr(args, "verbose", False):
        logging.basicConfig(level=logging.DEBUG, format="%(levelname)s: %(message)s")
    else:
        logging.basicConfig(level=logging.INFO, format="%(message)s")

    # Handle --dry-run
    if getattr(args, "dry_run", False):
        source = args.spec or args.spec_url or args.from_json or "(none)"
        print(f"\n{'=' * 60}")
        print("DRY RUN: OpenAPI Specification Extraction")
        print(f"{'=' * 60}")
        print(f"Source:         {source}")
        print(f"Name:           {getattr(args, 'name', None) or '(auto-detect)'}")
        print(f"Enhance level:  {getattr(args, 'enhance_level', 0)}")
        print(f"\n  Dry run complete")
        return 0

    # Validate inputs
    if not (args.spec or args.spec_url or args.from_json):
        parser.error("Must specify --spec (file path), --spec-url (URL), or --from-json")

    # Build from pre-extracted JSON
    if args.from_json:
        name = args.name or Path(args.from_json).stem.replace("_extracted", "")
        config: dict[str, Any] = {
            "name": name,
            "description": (args.description or f"Use when working with the {name} API"),
        }
        converter = OpenAPIToSkillConverter(config)
        converter.load_extracted_data(args.from_json)
        converter.build_skill()
        return 0

    # Determine name
    if not args.name:
        if args.spec:
            name = Path(args.spec).stem
        elif args.spec_url:
            # Derive name from URL
            from urllib.parse import urlparse

            url_path = urlparse(args.spec_url).path
            name = Path(url_path).stem if url_path else "api"
        else:
            name = "api"
    else:
        name = args.name

    # Build config
    config = {
        "name": name,
        "spec_path": args.spec or "",
        "spec_url": args.spec_url or "",
    }
    if args.description:
        config["description"] = args.description

    # Create converter and run
    try:
        converter = OpenAPIToSkillConverter(config)

        if not converter.extract_spec():
            print("\n  OpenAPI extraction failed", file=sys.stderr)
            sys.exit(1)

        converter.build_skill()

        # Enhancement workflow integration
        if getattr(args, "enhance_level", 0) > 0:
            api_key = getattr(args, "api_key", None) or os.environ.get("ANTHROPIC_API_KEY")
            mode = "API" if api_key else "LOCAL"

            print(f"\n{'=' * 80}")
            print(f"  AI Enhancement ({mode} mode, level {args.enhance_level})")
            print("=" * 80)

            skill_dir = converter.skill_dir
            if api_key:
                try:
                    from skill_seekers.cli.enhance_skill import enhance_skill_md

                    enhance_skill_md(skill_dir, api_key)
                    print("  API enhancement complete!")
                except ImportError:
                    print("  API enhancement not available. Falling back to LOCAL mode...")
                    from skill_seekers.cli.enhance_skill_local import LocalSkillEnhancer

                    agent = getattr(args, "agent", None) if args else None
                    agent_cmd = getattr(args, "agent_cmd", None) if args else None
                    enhancer = LocalSkillEnhancer(Path(skill_dir), agent=agent, agent_cmd=agent_cmd)
                    enhancer.run(headless=True)
                    print("  Local enhancement complete!")
            else:
                from skill_seekers.cli.enhance_skill_local import LocalSkillEnhancer

                agent = getattr(args, "agent", None) if args else None
                agent_cmd = getattr(args, "agent_cmd", None) if args else None
                enhancer = LocalSkillEnhancer(Path(skill_dir), agent=agent, agent_cmd=agent_cmd)
                enhancer.run(headless=True)
                print("  Local enhancement complete!")

    except (ValueError, RuntimeError) as e:
        print(f"\n  Error: {e}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"\n  Unexpected error during OpenAPI processing: {e}", file=sys.stderr)
        import traceback

        traceback.print_exc()
        sys.exit(1)

    return 0


if __name__ == "__main__":
    sys.exit(main())
