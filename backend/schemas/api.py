from pydantic import BaseModel, ConfigDict

class CustomerRequestModel(BaseModel):
    model_config = ConfigDict(extra="forbid")
class ScanRequest(CustomerRequestModel):
    target: str
    user_id: int | None = None
class UserRequest(CustomerRequestModel):
    name: str
    email: str
class CompanyProfileRequest(CustomerRequestModel):
    company_name: str
    company_domain: str
    intended_use: str
class TrustedReviewContext(BaseModel):
    actor_id: str
    actor_role: str
    source: str = "trusted-admin"
class TargetRequest(CustomerRequestModel):
    domain: str
    user_id: int | None = None
class ActivationRequest(CustomerRequestModel):
    activation_code: str
