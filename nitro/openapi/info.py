"""OpenAPI metadata configuration."""
from __future__ import annotations

from pydantic import BaseModel


class OpenAPIInfo(BaseModel):
    """API metadata for the OpenAPI spec."""

    title: str = "Nitro API"
    version: str = "1.0.0"
    description: str = ""
    terms_of_service: str = ""
    contact_name: str = ""
    contact_email: str = ""
    contact_url: str = ""
    license_name: str = ""
    license_url: str = ""

    def to_openapi(self) -> dict:
        """Convert to OpenAPI info object."""
        info: dict = {"title": self.title, "version": self.version}
        if self.description:
            info["description"] = self.description
        if self.terms_of_service:
            info["termsOfService"] = self.terms_of_service
        contact = {}
        if self.contact_name:
            contact["name"] = self.contact_name
        if self.contact_email:
            contact["email"] = self.contact_email
        if self.contact_url:
            contact["url"] = self.contact_url
        if contact:
            info["contact"] = contact
        license_obj = {}
        if self.license_name:
            license_obj["name"] = self.license_name
        if self.license_url:
            license_obj["url"] = self.license_url
        if license_obj:
            info["license"] = license_obj
        return info
