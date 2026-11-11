from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator


class OrganizationCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    slug: str = Field(pattern=r"^[a-z0-9]+(?:-[a-z0-9]+)*$", min_length=1, max_length=100)


class OrganizationPatchRequest(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    settings: dict[str, object] | None = None

    @model_validator(mode="after")
    def require_patch_field(self) -> OrganizationPatchRequest:
        if not self.model_fields_set:
            raise ValueError("At least one organization field must be provided")
        return self

ErrorResponse = 'ApiErrorResponse'


class OrganizationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    slug: str
    role: str | None = None
    settings: dict[str, object] | None = None
    created_at: datetime
    updated_at: datetime | None = None


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    email: str
    display_name: str | None = None
    created_at: datetime
    updated_at: datetime | None = None


class MembershipResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    organization_id: str
    user_id: str
    role: str
    invited_by: str | None = None
    created_at: datetime


class OrganizationMembershipResponse(MembershipResponse):
    organization: OrganizationResponse


class CurrentUserResponse(BaseModel):
    user: UserResponse
    memberships: list[OrganizationMembershipResponse]


class DevelopmentTokenRequest(BaseModel):
    email: str = Field(min_length=3, max_length=320)


class DevelopmentTokenResponse(BaseModel):
    access_token: str
    user_id: str
    email: str
    display_name: str | None
    organization_id: str
    organization_name: str
    role: str


class OrganizationMemberResponse(MembershipResponse):
    email: str
    display_name: str | None = None
