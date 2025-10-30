# models.py — stdlib version (no pydantic)

from dataclasses import dataclass, field
from typing import List, Optional, Literal, Dict, Any
import re

SchemaType = Literal[
    "WidgetCreateRequest",
    "WidgetDeleteRequest",
    "WidgetUpdateRequest",
]

OWNER_RE = re.compile(r"[A-Za-z ]+$")

@dataclass
class OtherAttribute:
    name: str
    value: str

@dataclass
class WidgetRequest:
    type: SchemaType
    requestId: str
    widgetId: str
    owner: str
    label: Optional[str] = None
    description: Optional[str] = None
    otherAttributes: Optional[List[OtherAttribute]] = field(default_factory=list)

    def __post_init__(self) -> None:
        # Validate type
        if self.type not in (
            "WidgetCreateRequest",
            "WidgetDeleteRequest",
            "WidgetUpdateRequest",
        ):
            raise ValueError("type must be one of the schema values")

        # Validate required strings
        for k in ("requestId", "widgetId", "owner"):
            v = getattr(self, k, None)
            if not isinstance(v, str) or not v:
                raise ValueError(f"{k} must be a non-empty string")

        # Validate owner pattern
        if not OWNER_RE.fullmatch(self.owner):
            raise ValueError("owner must contain only letters and spaces")

        # Normalize/validate otherAttributes
        fixed: List[OtherAttribute] = []
        for oa in (self.otherAttributes or []):
            if isinstance(oa, dict):
                name = oa.get("name")
                value = oa.get("value")
                if not isinstance(name, str) or not isinstance(value, str):
                    raise ValueError("each otherAttributes item must have string name and value")
                fixed.append(OtherAttribute(name=name, value=value))
            elif isinstance(oa, OtherAttribute):
                fixed.append(oa)
            else:
                raise ValueError("otherAttributes items must be dicts or OtherAttribute objects")
        self.otherAttributes = fixed

def owner_slug(owner: str) -> str:
    return owner.lower().replace(" ", "-")

def to_flat_widget_dict(req: WidgetRequest) -> Dict[str, Any]:
    d: Dict[str, Any] = {
        "widgetId": req.widgetId,
        "owner": req.owner,
        "label": req.label,
        "description": req.description,
    }
    for oa in req.otherAttributes or []:
        d[oa.name] = oa.value
    return {k: v for k, v in d.items() if v is not None}
