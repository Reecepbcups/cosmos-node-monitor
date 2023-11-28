from typing import List


class Endpoint:
    name: str
    nodes: List[str]
    references: List[str]
    allowed_block_drift: int = 5

    def __init__(
        self,
        name: str,
        nodes: List[str],
        references: List[str],
        allowed_block_drift: int = 5,
    ):
        self.name = name
        self.nodes = nodes
        self.references = references
        self.allowed_block_drift = allowed_block_drift

    def from_json(self, json: dict):
        self.name = json["name"]
        self.nodes = json["nodes"]
        self.references = json["references"]
        self.allowed_block_drift = json.get("allowed_block_drift", 5)

    def __repr__(self):
        return f"{self.name}: {self.nodes=}, {self.references=}"
