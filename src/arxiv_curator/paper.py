"""Pydantic model for arXiv article metadata."""

from datetime import datetime

import arxiv
from pydantic import BaseModel, Field, HttpUrl, field_validator


class ArxivArticle(BaseModel):
    """Complete arXiv article metadata model."""

    arxiv_id: str = Field(
        ...,
        description="Extracted arXiv ID from entry_id (e.g., '2301.12345')",
        min_length=1,
    )

    title: str = Field(..., description="The title of the article", min_length=1)

    authors: list[str] = Field(
        ..., description="List of author names as strings", min_length=1
    )

    summary: str = Field(..., description="The article abstract", min_length=1)

    published: int = Field(
        ..., description="Publication date as long integer (format: YYYYMMDDHHmm)"
    )

    updated: str | None = Field(None, description="Last update date in ISO format")

    categories: str = Field(
        ..., description="Comma-separated list of categories", min_length=1
    )

    pdf_url: HttpUrl = Field(..., description="Direct URL to the PDF")

    primary_category: str = Field(..., description="The primary arXiv category")

    ingestion_timestamp: str = Field(
        ..., description="Timestamp when the article was ingested (ISO format)"
    )

    processed: bool | None = Field(
        None, description="Processing status flag (set in Lecture 2.2)"
    )
    volume_path: str | None = Field(
        None, description="Path to volume storage (set in Lecture 2.2)"
    )
    model_config = {
        "str_strip_whitespace": True,  # Trim whitespace from strings
        "validate_assignment": True,  # Validate on attribute assignment
        "frozen": False,  # Allow field modification
        "use_enum_values": True,  # Use enum values instead of enum objects
    }

    @field_validator("published")
    @classmethod
    def validate_published_format(cls, v: int) -> int:
        """Validate that published is in YYYYMMDDHHmm format."""
        if len(str(v)) != 12:
            raise ValueError("Published must be in YYYYMMDDHHmm format (12 digits)")
        return v

    @classmethod
    def from_arxiv_result(cls, result: arxiv.Result) -> "ArxivArticle":
        """Convert an arxiv.Result object to ArxivArticle Pydantic model."""
        return cls(
            arxiv_id=result.entry_id.split("/")[-1],
            title=result.title,
            authors=[author.name for author in result.authors],
            summary=result.summary,
            published=int(result.published.strftime("%Y%m%d%H%M")),
            updated=result.updated.isoformat() if result.updated else None,
            categories=", ".join(result.categories),
            pdf_url=result.pdf_url,
            primary_category=result.primary_category,
            ingestion_timestamp=datetime.now().isoformat(),
        )

    def to_dict(self) -> dict:
        """Export to dictionary matching the original logic structure."""
        return self.model_dump()

    def to_json(self, indent: int = 2) -> str:
        """Export to JSON string."""
        return self.model_dump_json(indent=indent)
