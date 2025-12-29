import rusty_tags as rt
from typing import Literal
from rusty_tags import Fragment


def Input(
        label:str = '', 
        type:Literal['date', 'datetime-local', 'email', 'month', 'number', 'password', 'search', 'tel', 'text', 'time', 'url', 'week'] = 'text', 
        placeholder:str = '', 
        supporting_text:str = '', 
        *args, **kwargs
    ):
    """
    Open Props UI compatible text field component.
    
    Args:
        label: The floating label text (this becomes the floating label)
        type: Input type (default: 'text')
        placeholder: NOT USED - Open Props UI uses floating labels instead of placeholders
        supporting_text: Helper text below the input
    """
    # For Open Props UI floating labels, we need an empty placeholder for the CSS to work
    # The label parameter becomes the floating label, not the placeholder
    placeholder = ' '
    
    return rt.Div(
        rt.Span(label, cls='label') if label else Fragment(),
        rt.Input(type=type, placeholder=placeholder, *args, **kwargs),
        rt.P(supporting_text, cls='supporting-text') if supporting_text else Fragment(),
        cls='field',
    )