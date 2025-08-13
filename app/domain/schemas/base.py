from pydantic import BaseModel


class AppBaseModel(BaseModel):
    """Base model providing helper methods for JSON and dictionary conversion."""

    def to_json(self) -> str:
        """Convert the model to a JSON string excluding fields with None values.

        Returns:
            str: The JSON representation of the model.
        """
        return self.model_dump_json(exclude_none=True)

    def to_dict(self) -> dict:
        """Convert the model to a dictionary excluding fields with None values.

        Returns:
            dict: The dictionary representation of the model.
        """
        return self.model_dump(exclude_none=True)


__all__ = ["AppBaseModel"]
