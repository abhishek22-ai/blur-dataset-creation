"""
Plugin Discovery

Automatic discovery of plugins from multiple sources including
file system, installed packages, and remote repositories.
"""

import glob
import importlib.util
import json
import os
import pkgutil
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional


@dataclass
class DiscoverySource:
    """Information about a plugin discovery source."""

    name: str
    source_type: str  # 'filesystem', 'package', 'remote'
    path: str
    enabled: bool = True
    priority: int = 0
    metadata: Dict[str, Any] = None


class PluginDiscovery:
    """
    Advanced plugin discovery system.

    Discovers plugins from multiple sources including:
    - File system directories
    - Installed Python packages
    - Remote repositories
    - Configuration files
    """

    def __init__(self, search_paths: Optional[List[str]] = None):
        """
        Initialize plugin discovery.

        Args:
            search_paths: List of directories to search for plugins
        """
        self.search_paths = search_paths or []
        self.discovery_sources: List[DiscoverySource] = []

        # Plugin file patterns
        self.plugin_patterns = ["*.py", "*_plugin.py", "plugin_*.py", "*blur*.py"]

        # Excluded directories
        self.exclude_dirs = {
            "__pycache__",
            ".git",
            ".svn",
            "node_modules",
            ".venv",
            "venv",
            "env",
        }

        # Plugin indicators in code
        self.plugin_indicators = [
            "PluginBase",
            "class.*Plugin",
            "blur_type",
            "BlurType",
            "_apply_blur",
            "plugin_name",
        ]

    def add_search_path(self, path: str, priority: int = 0):
        """
        Add a search path for plugin discovery.

        Args:
            path: Directory path to search
            priority: Search priority (higher = searched first)
        """
        source = DiscoverySource(
            name=f"filesystem_{len(self.discovery_sources)}",
            source_type="filesystem",
            path=path,
            priority=priority,
        )
        self.discovery_sources.append(source)

    def add_package_source(self, package_name: str, priority: int = 0):
        """
        Add an installed package as a plugin source.

        Args:
            package_name: Name of the Python package
            priority: Search priority
        """
        source = DiscoverySource(
            name=f"package_{package_name}",
            source_type="package",
            path=package_name,
            priority=priority,
        )
        self.discovery_sources.append(source)

    def discover_plugin_files(
        self, search_paths: Optional[List[str]] = None
    ) -> List[str]:
        """
        Discover plugin files in specified paths.

        Args:
            search_paths: Paths to search (uses instance paths if None)

        Returns:
            List of discovered plugin file paths
        """
        plugin_files = set()
        paths_to_search = search_paths or self.search_paths

        # Discover from file system
        for path in paths_to_search:
            if os.path.exists(path):
                files = self._discover_filesystem_plugins(path)
                plugin_files.update(files)

        # Discover from installed packages
        package_files = self._discover_package_plugins()
        plugin_files.update(package_files)

        return sorted(list(plugin_files))

    def _discover_filesystem_plugins(self, root_path: str) -> List[str]:
        """Discover plugins in file system."""
        plugin_files = []

        try:
            for pattern in self.plugin_patterns:
                search_pattern = os.path.join(root_path, "**", pattern)
                for file_path in glob.glob(search_pattern, recursive=True):
                    # Skip excluded directories
                    if self._is_excluded_path(file_path):
                        continue

                    # Validate that this is actually a plugin file
                    if self._is_plugin_file(file_path):
                        plugin_files.append(file_path)

        except Exception as e:
            print(f"Error discovering plugins in {root_path}: {e}")

        return plugin_files

    def _discover_package_plugins(self) -> List[str]:
        """Discover plugins in installed packages."""
        plugin_files = []

        try:
            # Get all installed packages
            for importer, modname, ispkg in pkgutil.iter_modules():
                if ispkg:
                    try:
                        # Check if package contains plugin indicators
                        module = importlib.import_module(modname)

                        # Look for plugin files in the package
                        if hasattr(module, "__file__") and module.__file__:
                            package_path = os.path.dirname(module.__file__)
                            files = self._discover_filesystem_plugins(package_path)
                            plugin_files.extend(files)

                    except Exception:
                        # Skip packages that can't be imported
                        continue

        except Exception as e:
            print(f"Error discovering package plugins: {e}")

        return plugin_files

    def _is_excluded_path(self, file_path: str) -> bool:
        """Check if path should be excluded from discovery."""
        path_parts = Path(file_path).parts

        for part in path_parts:
            if part in self.exclude_dirs:
                return True

        return False

    def _is_plugin_file(self, file_path: str) -> bool:
        """Check if file is likely a plugin file."""
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Check for plugin indicators
            indicators_found = 0
            for indicator in self.plugin_indicators:
                if indicator in content:
                    indicators_found += 1

            # Require at least 2 indicators to consider it a plugin
            return indicators_found >= 2

        except Exception:
            return False

    def discover_plugins_with_metadata(self) -> Dict[str, Dict[str, Any]]:
        """
        Discover plugins and extract metadata.

        Returns:
            Dictionary mapping file paths to plugin metadata
        """
        plugin_files = self.discover_plugin_files()
        plugins_metadata = {}

        for file_path in plugin_files:
            try:
                metadata = self._extract_plugin_metadata(file_path)
                if metadata:
                    plugins_metadata[file_path] = metadata

            except Exception as e:
                print(f"Error extracting metadata from {file_path}: {e}")

        return plugins_metadata

    def _extract_plugin_metadata(self, file_path: str) -> Optional[Dict[str, Any]]:
        """Extract metadata from plugin file."""
        try:
            # Load module to inspect
            module_name = self._generate_module_name(file_path)
            spec = importlib.util.spec_from_file_location(module_name, file_path)

            if not spec or not spec.loader:
                return None

            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

            # Find plugin class
            plugin_class = self._find_plugin_class_in_module(module)
            if not plugin_class:
                return None

            # Extract metadata
            metadata = {
                "file_path": file_path,
                "class_name": plugin_class.__name__,
                "module_name": module_name,
                "plugin_name": getattr(
                    plugin_class, "plugin_name", plugin_class.__name__
                ),
                "version": getattr(plugin_class, "plugin_version", "1.0.0"),
                "author": getattr(plugin_class, "plugin_author", "Unknown"),
                "description": getattr(plugin_class, "plugin_description", ""),
                "dependencies": getattr(plugin_class, "plugin_dependencies", []),
                "tags": getattr(plugin_class, "plugin_tags", []),
            }

            return metadata

        except Exception:
            return None

    def _generate_module_name(self, file_path: str) -> str:
        """Generate unique module name for plugin file."""
        import hashlib

        path_hash = hashlib.md5(file_path.encode()).hexdigest()[:8]
        base_name = Path(file_path).stem
        return f"plugin_{base_name}_{path_hash}"

    def _find_plugin_class_in_module(self, module) -> Optional[type]:
        """Find plugin class in loaded module."""
        import inspect

        for name, obj in inspect.getmembers(module):
            if (
                inspect.isclass(obj)
                and hasattr(obj, "__bases__")
                and any("PluginBase" in str(base) for base in obj.__bases__)
            ):
                return obj

        return None

    def scan_for_plugin_repositories(self) -> List[Dict[str, Any]]:
        """
        Scan for plugin repositories and remote sources.

        Returns:
            List of discovered repository information
        """
        repositories = []

        # Common plugin repository patterns

        # This is a simplified implementation
        # In practice, you might want to:
        # 1. Check configuration files for known repositories
        # 2. Query package indexes
        # 3. Check for plugin registry APIs

        return repositories

    def discover_plugins_from_repositories(self, repo_urls: List[str]) -> List[str]:
        """
        Discover plugins from remote repositories.

        Args:
            repo_urls: List of repository URLs

        Returns:
            List of discovered plugin files
        """
        plugin_files = []

        for repo_url in repo_urls:
            try:
                # This would implement repository scanning
                # For now, return empty list
                pass

            except Exception as e:
                print(f"Error discovering plugins from {repo_url}: {e}")

        return plugin_files

    def create_plugin_index(self, output_file: str):
        """
        Create an index of all discovered plugins.

        Args:
            output_file: Path to output index file
        """
        plugins_metadata = self.discover_plugins_with_metadata()

        index_data = {
            "created_at": time.time(),
            "total_plugins": len(plugins_metadata),
            "search_paths": self.search_paths,
            "plugins": plugins_metadata,
        }

        with open(output_file, "w") as f:
            json.dump(index_data, f, indent=2)

    def search_plugins(
        self, query: str, search_fields: Optional[List[str]] = None
    ) -> List[str]:
        """
        Search for plugins matching a query.

        Args:
            query: Search query
            search_fields: Fields to search in (name, description, tags, etc.)

        Returns:
            List of matching plugin file paths
        """
        if not search_fields:
            search_fields = ["name", "description", "tags", "author"]

        matching_files = []
        plugins_metadata = self.discover_plugins_with_metadata()

        query_lower = query.lower()

        for file_path, metadata in plugins_metadata.items():
            for field in search_fields:
                if field in metadata:
                    value = metadata[field]
                    if isinstance(value, str):
                        if query_lower in value.lower():
                            matching_files.append(file_path)
                            break
                    elif isinstance(value, list):
                        if any(query_lower in str(item).lower() for item in value):
                            matching_files.append(file_path)
                            break

        return matching_files

    def get_discovery_stats(self) -> Dict[str, Any]:
        """Get discovery statistics."""
        plugin_files = self.discover_plugin_files()

        stats = {
            "total_files_found": len(plugin_files),
            "search_paths": len(self.search_paths),
            "discovery_sources": len(self.discovery_sources),
            "plugin_patterns": self.plugin_patterns,
        }

        # Analyze file types
        file_types = {}
        for file_path in plugin_files:
            ext = Path(file_path).suffix
            file_types[ext] = file_types.get(ext, 0) + 1

        stats["file_types"] = file_types

        return stats


# Import time here to avoid circular imports
import time
