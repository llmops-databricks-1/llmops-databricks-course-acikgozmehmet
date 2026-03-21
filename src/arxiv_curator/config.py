"""Configuration management for Arxiv Curator."""


from pathlib import Path

from loguru import logger
import yaml
from pydantic import BaseModel, Field
from pyspark.dbutils import DBUtils
from pyspark.sql import SparkSession


class ProjectConfig(BaseModel):
    """Project configuration model."""

    catalog: str = Field(..., description="Unity Catalog name")
    db_schema: str = Field(..., description="Schema name", alias="schema")
    volume: str = Field(..., description="Volume name")
    llm_endpoint: str = Field(..., description="LLM endpoint name")
    embedding_endpoint: str = Field(..., description="Embedding endpoint name")
    warehouse_id: str = Field(..., description="Warehouse ID")
    vector_search_endpoint: str = Field(..., description="Vector search endpoint name")
    genie_space_id: str | None = Field(None, description="Genie space ID for MCP integration")
    system_prompt: str = Field(
        default="You are a helpful AI assistant that helps users find and understand research papers.",
        description="System prompt for the agent"
    )
    
    model_config = {"populate_by_name": True}

    @classmethod
    def from_yaml(cls, config_path: str, env: str = "dev") -> "ProjectConfig":
        """Load configuration from YAML file.

        Args:
            config_path: Path to the YAML configuration file
            env: Environment name (dev, acc, prd)

        Returns:
            ProjectConfig instance
        """
        if env not in ["prd", "acc", "dev"]:
            raise ValueError(f"Invalid environment: {env}. Expected 'prd', 'acc', or 'dev'")

        logger.info(f"Loading configuration for environment: {env}")
        try:
            with open(config_path) as f:
                config_data = yaml.safe_load(f)
        except FileNotFoundError:
            logger.error(f"Configuration file not found: {config_path}")
            raise
        except yaml.YAMLError as e:
            logger.error(f"Error parsing YAML file: {config_path}. Error: {e}")
            raise

        if env not in config_data:
            logger.error(f"Environment '{env}' not found in config file")
            raise ValueError(f"Environment '{env}' not found in config file")

        logger.info(f"Configuration loaded successfully for environment: {env}")
        return cls(**config_data[env])

    @property
    def schema(self) -> str:
        """Alias for db_schema for backward compatibility."""
        return self.db_schema
    
    @property
    def full_schema_name(self) -> str:
        """Get fully qualified schema name."""
        return f"{self.catalog}.{self.db_schema}"

    @property
    def full_volume_path(self) -> str:
        """Get fully qualified volume path."""
        return f"{self.catalog}.{self.schema}.{self.volume}"


class ModelConfig(BaseModel):
    """Model configuration."""

    temperature: float = Field(0.7, description="Model temperature")
    max_tokens: int = Field(2000, description="Maximum tokens")
    top_p: float = Field(0.95, description="Top-p sampling parameter")


class VectorSearchConfig(BaseModel):
    """Vector search configuration."""

    embedding_dimension: int = Field(1024, description="Embedding dimension")
    similarity_metric: str = Field("cosine", description="Similarity metric")
    num_results: int = Field(5, description="Number of results to return")


class ChunkingConfig(BaseModel):
    """Chunking configuration."""

    chunk_size: int = Field(512, description="Chunk size in tokens")
    chunk_overlap: int = Field(50, description="Overlap between chunks")
    separator: str = Field("\n\n", description="Separator for chunking")


def load_config(config_path: str = "project_config.yml", env: str = "dev") -> ProjectConfig:
    """Load project configuration.
    
    Args:
        config_path: Path to configuration file
        env: Environment name
        
    Returns:
        ProjectConfig instance
    """
    # Handle relative paths from notebooks
    if not Path(config_path).is_absolute():
        # Try to find config in parent directories
        current = Path.cwd()
        for _ in range(3):  # Search up to 3 levels
            candidate = current / config_path
            if candidate.exists():
                config_path = str(candidate)
                break
            current = current.parent
    
    logger.info(f"Attempting to load configuration from path: {config_path} for environment: {env}")
    try:
        config = ProjectConfig.from_yaml(config_path, env)
        logger.info("Configuration loaded successfully.")
        return config
    except Exception as e:
        logger.error(f"Failed to load configuration: {e}")
        raise


def get_env(spark: SparkSession) -> str:
    """Get current environment from dbutils widget, falling back to ENV variable or 'dev'.

    Returns:
        Environment name (dev, acc, or prd)
    """
    logger.info("Fetching environment from dbutils widget or environment variable.")
    try:
        dbutils = DBUtils(spark)
        env = dbutils.widgets.get("env")
        logger.info(f"Environment fetched successfully: {env}")
        return env
    except Exception as e:
        logger.warning(f"Failed to fetch environment from dbutils widget. Defaulting to 'dev'. Error: {e}")
        return "dev"