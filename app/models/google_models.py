"""
Google Assistant-specific models and data structures.
"""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class GoogleUser(BaseModel):
    """Google Assistant user model."""

    model_config = {"populate_by_name": True}

    user_id: str = Field(alias="userId")
    locale: Optional[str] = None
    user_verification: Optional[str] = Field(default=None, alias="userVerification")


class GoogleDevice(BaseModel):
    """Google Assistant device model."""

    location: Optional[Dict[str, Any]] = None


class GoogleSurface(BaseModel):
    """Google Assistant surface model."""

    capabilities: List[Dict[str, Any]] = []


class GoogleInput(BaseModel):
    """Google Assistant input model."""

    model_config = {"populate_by_name": True}

    raw_inputs: List[Dict[str, Any]] = Field(alias="rawInputs")
    intent: str
    arguments: Optional[List[Dict[str, Any]]] = None


class GoogleConversation(BaseModel):
    """Google Assistant conversation model."""

    model_config = {"populate_by_name": True}

    conversation_id: str = Field(alias="conversationId")
    type: str
    conversation_token: Optional[str] = Field(default=None, alias="conversationToken")


class GoogleRequest(BaseModel):
    """Google Assistant request model."""

    user: GoogleUser
    device: GoogleDevice
    surface: GoogleSurface
    conversation: GoogleConversation
    inputs: List[GoogleInput]
    is_health_check: Optional[bool] = False


class GoogleSimpleResponse(BaseModel):
    """Google Assistant simple response model."""

    text_to_speech: Optional[str] = None
    ssml: Optional[str] = None
    display_text: Optional[str] = None


class GoogleBasicCard(BaseModel):
    """Google Assistant basic card model."""

    title: Optional[str] = None
    subtitle: Optional[str] = None
    formatted_text: Optional[str] = None
    image: Optional[Dict[str, Any]] = None
    buttons: Optional[List[Dict[str, Any]]] = None


class GoogleSuggestion(BaseModel):
    """Google Assistant suggestion model."""

    title: str


class GoogleLinkOutSuggestion(BaseModel):
    """Google Assistant link out suggestion model."""

    destination_name: str
    url: str


class GoogleRichResponse(BaseModel):
    """Google Assistant rich response model."""

    items: List[Dict[str, Any]] = []
    suggestions: Optional[List[GoogleSuggestion]] = None
    link_out_suggestion: Optional[GoogleLinkOutSuggestion] = None


class GoogleExpectedInput(BaseModel):
    """Google Assistant expected input model."""

    input_prompt: Dict[str, Any]
    possible_intents: List[Dict[str, Any]]


class GoogleFinalResponse(BaseModel):
    """Google Assistant final response model."""

    rich_response: GoogleRichResponse


class GoogleResponse(BaseModel):
    """Google Assistant response model."""

    conversation_token: Optional[str] = None
    expect_user_response: bool = True
    expected_inputs: Optional[List[GoogleExpectedInput]] = None
    final_response: Optional[GoogleFinalResponse] = None
    rich_response: Optional[GoogleRichResponse] = None
    user_storage: Optional[str] = None


class GoogleDialogflowResponse(BaseModel):
    """Google Assistant Dialogflow response wrapper."""

    model_config = {"populate_by_name": True}

    fulfillment_text: Optional[str] = Field(default=None, alias="fulfillmentText")
    fulfillment_messages: Optional[List[Dict[str, Any]]] = Field(
        default=None, alias="fulfillmentMessages"
    )
    source: Optional[str] = None
    payload: Optional[GoogleResponse] = None
