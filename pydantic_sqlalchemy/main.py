from typing import Container, Optional, Type

from pydantic import BaseConfig, BaseModel, create_model, ConfigDict
from sqlalchemy.inspection import inspect
from sqlalchemy.orm.properties import ColumnProperty


def sqlalchemy_to_pydantic(
    db_model: Type, *, config=None, exclude=None
) -> Type[BaseModel]:
    if exclude is None:
        exclude = []

    if config is None:
        config = ConfigDict(from_attributes=True)

    mapper = inspect(db_model)
    fields = {}
    for attr in mapper.attrs:
        if isinstance(attr, ColumnProperty):
            if attr.columns:
                name = attr.key
                if name in exclude:
                    continue
                column = attr.columns[0]
                python_type: Optional[type] = None
                if hasattr(column.type, "impl"):
                    if hasattr(column.type.impl, "python_type"):
                        python_type = column.type.impl.python_type
                elif hasattr(column.type, "python_type"):
                    python_type = column.type.python_type
                assert python_type, f"Could not infer python_type for {column}"
                default = None
                if column.default is None:
                    if column.nullable:
                        default = None
                        python_type = Optional[python_type]
                    else:
                        default = ...
                fields[name] = (python_type, default)
    pydantic_model = create_model(
        db_model.__name__, __config__=config, **fields  # type: ignore
    )
    return pydantic_model