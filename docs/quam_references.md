# Component referencing

## QuAM tree-structure
QuAM follows a tree structure, meaning that each QuAM component can have a parent component and it can have children.
However, situations often arise where a component needs access to another part of QuAM that is not directly one of its children. To accomodate this, we introduce the concept of references.

```
@dataclass
class Component(QuamComponent):
    

component = Component()
component.a = 42
component.b = "#./a
print(component.b)
```
