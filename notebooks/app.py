from starhtml import *

app, rt = star_app()

@rt('/')
def home():
    return Div(
        H1("StarHTML Demo"),
        
        # Define reactive state with signals
        Div(
            (counter := Signal("counter", 0)),  # Python-first signal definition
            
            # Reactive UI that updates automatically
            P("Count: ", Span(data_text=counter)),
            Button("+", data_on_click=counter.add(1)),
            Button("Reset", data_on_click=counter.set(0)),
            
            # Conditional styling
            data_class_active=counter > 0
        ),
        
        # Server-side interactions
        Button("Load Data", data_on_click=get("/api/data")),
        Div(id="content")
    )

@rt('/api/data')
def api_data():
    return Div("Data loaded from server!", id="content")

serve()