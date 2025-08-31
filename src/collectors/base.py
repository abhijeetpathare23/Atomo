from __future__ import annotations
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

@dataclass
class Item:
    platform: str                   
    url: Optional[str]              
    title: str
    text: str                       
    author: Optional[str]
    ts: Optional[str]               
    metrics: Dict[str, float]       
    raw: Dict[str, Any]          

class BaseCollector:
    platform_name = "base"

    def __init__(self, cfg: dict):
        self.cfg = cfg

    def search(self, query: str) -> List[Item]:
        raise NotImplementedError